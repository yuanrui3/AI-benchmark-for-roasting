"""Truth gate: do the roast's premises check out against the fact sheet?

    uv run python truth.py --run mock --mock
    uv run python truth.py --run pilot --budget 8

A judge extracts every checkable factual claim the roast makes about the target and
labels each one supported / contradicted / absent relative to the fact sheet. Obvious
hyperbole, metaphor and opinion are not claims. An item FAILS the gate only on a
contradiction: plain-prompt arms never saw the sheet, so true facts that are merely
absent from it must not count against them.

Output: runs/<run>/truth.jsonl, one row per item x judge, with the claims and counts.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from common import ROOT, append_jsonl, load_targets, read_jsonl, utf8_stdout
from llm import LLM, BudgetExceeded

JUDGE_SYSTEM = "You are a meticulous fact-checker. Follow the output format exactly."
VERDICTS = ("supported", "contradicted", "absent")


def prompt(text: str, target: dict, lang: str) -> str:
    facts = "\n".join(f"- {f}" for f in target["facts"])
    name = config.target_name(target, lang)
    if lang == "zh":
        return (f"关于{name}的事实清单（已核实，英文）：\n{facts}\n\n待检查的段子：\n---\n{text}\n---\n\n"
                f"列出段子里关于{name}的每一条可核查的事实性说法（明显的夸张、比喻和纯观点不算）。"
                f"给每一条打标签：supported（事实清单支持）、contradicted（事实清单表明它是错的）、"
                f"absent（事实清单没有涉及）。\n"
                f"Return a JSON array of objects with keys \"claim\" and \"verdict\", and nothing else. "
                f"If there are no factual claims, return [].")
    return (f"Fact sheet about {name} (verified):\n{facts}\n\nText to check:\n---\n{text}\n---\n\n"
            f"List every checkable factual claim the text makes about {name}. Obvious hyperbole, metaphor and "
            f"opinion are not claims. Label each one: supported (the fact sheet backs it), contradicted (the fact "
            f"sheet shows it is false), absent (the fact sheet does not cover it).\n"
            f"Return a JSON array of objects with keys \"claim\" and \"verdict\", and nothing else. "
            f"If there are no factual claims, return [].")


def parse_claims(text: str) -> list[dict] | None:
    m = re.search(r"\[.*\]", text or "", re.S)
    if not m:
        return None
    try:
        arr = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    out = []
    for c in arr if isinstance(arr, list) else []:
        if isinstance(c, dict) and str(c.get("verdict", "")).lower() in VERDICTS:
            out.append({"claim": str(c.get("claim", ""))[:300], "verdict": str(c["verdict"]).lower()})
    return out


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--budget", type=float, default=8.0)
    ap.add_argument("--judges", default="judge-sonnet", help="comma list from config.JUDGES")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    run_dir = ROOT / "runs" / args.run
    targets = load_targets()
    items = [r for r in read_jsonl(run_dir / "items.jsonl")
             if r["kind"] != "generic" and r["text"].strip() and not r["refused"] and not r["error"]]
    judges = {j: config.MODELS[config.JUDGES[j]] for j in args.judges.split(",")}
    out_path = run_dir / "truth.jsonl"
    done = {(r["item_id"], r["judge"]) for r in read_jsonl(out_path)} if out_path.exists() else set()
    jobs = [(it, j) for it in items for j in judges if (it["item_id"], j) not in done]
    print(f"{len(items)} items, {len(judges)} judge(s) -> {len(jobs)} calls to do")

    llm = LLM(run_dir, budget_usd=args.budget, mock=args.mock)
    lock = threading.Lock()
    stop = threading.Event()

    def work(job):
        it, jname = job
        if stop.is_set():
            return
        spec = judges[jname]
        t = targets[it["target_id"]]
        try:
            res = llm.call(spec, JUDGE_SYSTEM, prompt(it["text"], t, it["lang"]), max_tokens=2000,
                           effort=config.JUDGE_EFFORT, key=f"truth|{args.run}|{it['item_id']}|{jname}", tag=f"truth:{jname}")
        except BudgetExceeded as e:
            stop.set()
            print(f"BUDGET: {e}")
            return
        claims = parse_claims(res.text)
        counts = {v: sum(c["verdict"] == v for c in claims or []) for v in VERDICTS}
        row = {"item_id": it["item_id"], "target_id": t["id"], "arm": it["arm"], "kind": it["kind"], "lang": it["lang"],
               "gen_family": it["family"], "judge": jname, "judge_family": spec.family, "claims": claims,
               **{f"n_{v}": counts[v] for v in VERDICTS}, "passes": claims is not None and counts["contradicted"] == 0,
               "parse_fail": claims is None, "cost_usd": res.cost_usd, "error": res.error}
        with lock:
            append_jsonl(out_path, row)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for _ in as_completed([ex.submit(work, j) for j in jobs]):
            pass

    rows = read_jsonl(out_path)
    print(f"\nspent ${llm.spent_usd:.2f}\n{'arm':18s} {'lang':4s} {'n':>4s} {'pass':>6s} {'claims':>7s} {'supp':>6s} "
          f"{'contra':>6s} {'absent':>6s} {'parse✗':>7s}")
    for arm in sorted({r["arm"] for r in rows}):
        for lang in sorted({r["lang"] for r in rows}):
            rs = [r for r in rows if r["arm"] == arm and r["lang"] == lang]
            if not rs:
                continue
            n = len(rs)
            tot = sum(r["n_supported"] + r["n_contradicted"] + r["n_absent"] for r in rs)
            print(f"{arm:18s} {lang:4s} {n:4d} {sum(r['passes'] for r in rs) / n:6.2f} {tot / n:7.2f} "
                  f"{sum(r['n_supported'] for r in rs) / n:6.2f} {sum(r['n_contradicted'] for r in rs) / n:6.2f} "
                  f"{sum(r['n_absent'] for r in rs) / n:6.2f} {sum(r['parse_fail'] for r in rs) / n:7.2f}")
    return 0 if not stop.is_set() else 3


if __name__ == "__main__":
    sys.exit(main())
