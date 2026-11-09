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
                f"列出这段段子依赖的关于{name}的事实性前提：听众必须当真、包袱才成立的说法（年代、人名、数字、来历、"
                f"它是什么或做什么）。夸张、比喻、虚构的场景和纯观点是笑点本身，不算前提：“一群没睡醒的实习生凑出来的”"
                f"“靠吃垃圾活着”不是前提；“1994年为一只卡通狗设计的”才是。"
                f"给每一条打标签：supported（事实清单支持）、contradicted（事实清单表明它是错的；为了效果凑整的数字，"
                f"比如把43%说成“一半”，不算错）、absent（事实清单没有涉及）。\n"
                f"Return a JSON array of objects with keys \"claim\" and \"verdict\", and nothing else. "
                f"If there are no premises, return [].")
    return (f"Fact sheet about {name} (verified):\n{facts}\n\nText to check:\n---\n{text}\n---\n\n"
            f"List the factual premises the text relies on about {name}: statements a listener must take as true "
            f"for the material to land (dates, names, numbers, origins, what it is or does). Comic exaggeration, "
            f"metaphor, invented scenarios and opinion are the joke, not premises: 'designed by a committee of "
            f"sleep-deprived interns' or 'survives on garbage' are not premises; 'created in 1994 for a cartoon dog' "
            f"is. Label each premise: supported (the fact sheet backs it), contradicted (the fact sheet shows it is "
            f"false; a figure rounded for effect, such as 'half' for 43%, is not a contradiction), absent (the fact "
            f"sheet does not cover it).\n"
            f"Return a JSON array of objects with keys \"claim\" and \"verdict\", and nothing else. "
            f"If there are no premises, return [].")


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
    ap.add_argument("--budget", type=float, default=40.0, help="run-wide USD cap (ledger is shared by all stages)")
    ap.add_argument("--judges", default=None, help="comma list from config.JUDGES; default: the first judge whose key exists")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    run_dir = ROOT / "runs" / args.run
    targets = load_targets()
    items = [r for r in read_jsonl(run_dir / "items.jsonl")
             if r["kind"] != "generic" and r["text"].strip() and not r["refused"] and not r["error"]]
    judge_names = args.judges.split(",") if args.judges else config.truth_judges(args.mock)
    judges = {j: config.MODELS[config.JUDGES[j]] for j in judge_names}
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
                           effort=config.JUDGE_EFFORT, tag=f"truth:{jname}")
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
