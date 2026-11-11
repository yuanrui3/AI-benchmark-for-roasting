"""Specificity depth: how much of a roast is true of this target only, sentence by sentence.

    uv run python depth.py --run pilot                         # first usable judge (Sonnet by default), all items
    uv run python depth.py --run pilot --judges judge-opus     # on request

The masked swap test is at ceiling for frontier models (every arm picks its target from five), so it is a floor, not
a measure. This stage grades depth instead. One judge call per item labels every sentence: T = lands on this target
and would not land on its near-twin (a fact, a quirk, a history that is this thing's); B = would land just as well on
the twin or on anything in the category (the joke is about the kind of thing, not the thing); N = not about the
target at all (connective, address, setup). depth = T / (T + B). Writes runs/<run>/depth.jsonl, one row per item x
judge, with the labels, and prints a per-arm table. Failed calls are not persisted (a re-run retries them).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from agency import sentences
from common import ROOT, append_jsonl, load_targets, read_jsonl, utf8_stdout
from llm import LLM, BudgetExceeded

JUDGE_SYSTEM = "You label the sentences of a comedy text against a fact sheet. Follow the output format exactly."


def prompt(sents: list[str], lang: str, name: str, twin: str, facts: list[str]) -> str:
    numbered = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(sents))
    sheet = "\n".join(f"- {f}" for f in facts)
    if lang == "zh":
        return (f"这是关于{name}的事实清单（已核实）：\n{sheet}\n\n"
                f"下面是一段吐槽{name}的段子，已按句编号：\n{numbered}\n\n"
                f"给每一句打一个标签：T = 这句打在{name}自己身上，换成{twin}就不成立（用了它独有的事实、毛病或来历）；"
                f"B = 这句换成{twin}或者同类的任何东西照样成立（说的是这一类东西，不是这一个）；"
                f"N = 这句根本不是在说{name}（过渡、铺垫、对观众说话）。"
                f"只输出一个 JSON 字符串数组，长度等于句数，按顺序一句一个标签，不要别的。")
    return (f"Fact sheet for {name} (verified):\n{sheet}\n\n"
            f"Below is a roast of {name}, one numbered sentence per line:\n{numbered}\n\n"
            f"Label each sentence: T = it lands on {name} itself and would not land on {twin} (it uses a fact, a flaw "
            f"or a history that belongs to this thing); B = it would land just as well on {twin} or on anything of the "
            f"kind (the joke is about the category, not this thing); N = it is not about {name} at all (connective, "
            f"setup, address to the audience). "
            f"Output only a JSON array of strings, one label per sentence in order, nothing else.")


def parse_labels(text: str, n: int) -> list[str] | None:
    m = re.search(r"\[.*?\]", text, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list) or len(data) != n:
        return None
    labs = [str(x).strip().upper()[:1] for x in data]
    return labs if all(l in ("T", "B", "N") for l in labs) else None


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--budget", type=float, default=40.0, help="run-wide USD cap (ledger is shared by all stages)")
    ap.add_argument("--judges", default=None, help="comma list; default: config.truth_judges()")
    ap.add_argument("--arms", default=None, help="comma list of arms (default: all)")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    run_dir = ROOT / "runs" / args.run
    targets = load_targets()
    items = [r for r in read_jsonl(run_dir / "items.jsonl") if r["text"].strip() and not r["refused"] and not r["error"]]
    if args.arms:
        items = [r for r in items if r["arm"] in set(args.arms.split(","))]
    judge_names = args.judges.split(",") if args.judges else config.truth_judges()
    judges = {j: config.MODELS[config.JUDGES[j]] for j in judge_names}
    out_path = run_dir / "depth.jsonl"
    done = {(r["item_id"], r["judge"]) for r in read_jsonl(out_path)} if out_path.exists() else set()
    jobs = [(it, j) for it in items for j in judges if (it["item_id"], j) not in done]
    print(f"{len(items)} items, {len(judges)} judge(s) -> {len(jobs)} calls to do")

    llm = LLM(run_dir, budget_usd=args.budget)
    lock = threading.Lock()
    stop = threading.Event()

    def work(job):
        it, jname = job
        if stop.is_set():
            return
        spec = judges[jname]
        t = targets[it["target_id"]]
        twin = targets.get(t.get("twin"))
        sents = sentences(it["text"], it["lang"])
        if not sents:
            return
        try:
            res = llm.call(spec, JUDGE_SYSTEM,
                           prompt(sents, it["lang"], config.target_name(t, it["lang"]),
                                  config.target_name(twin, it["lang"]) if twin else ("同类的东西" if it["lang"] == "zh" else "a similar thing"),
                                  t["facts"]),
                           max_tokens=config.JUDGE_MAX_TOKENS, effort=config.JUDGE_EFFORT, tag=f"depth:{jname}")
        except BudgetExceeded as e:
            stop.set()
            print(f"BUDGET: {e}")
            return
        if res.error:
            print(f"  failed, will retry next run: {res.error[:80]}", flush=True)
            return
        labs = parse_labels(res.text, len(sents))
        n_t = labs.count("T") if labs else 0
        n_b = labs.count("B") if labs else 0
        n_n = labs.count("N") if labs else 0
        row = {"item_id": it["item_id"], "target_id": it["target_id"], "arm": it["arm"], "kind": it["kind"],
               "lang": it["lang"], "model": it["model"], "judge": jname, "judge_family": spec.family,
               "n_sent": len(sents), "labels": labs, "n_target": n_t, "n_both": n_b, "n_other": n_n,
               "depth": (n_t / (n_t + n_b)) if labs and (n_t + n_b) else None,
               "parse_fail": labs is None, "cost_usd": res.cost_usd}
        with lock:
            append_jsonl(out_path, row)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for _ in as_completed([ex.submit(work, j) for j in jobs]):
            pass

    rows = read_jsonl(out_path) if out_path.exists() else []
    print(f"spent ${llm.spent_usd:.2f}. Depth = T / (T + B): share of target-bearing sentences that would not land on the twin.")
    print(f"{'judge':14s} {'arm':18s} lang    n  depth  target   both  other  parse✗")
    by: dict[tuple, list] = defaultdict(list)
    for r in rows:
        by[(r["judge"], r["arm"], r["lang"])].append(r)
    for (j, arm, lang), rs in sorted(by.items()):
        ok = [r for r in rs if r["depth"] is not None]
        tot = sum(r["n_sent"] for r in ok) or 1
        print(f"{j:14s} {arm:18s} {lang:4s} {len(rs):4d} "
              f"{(sum(r['depth'] for r in ok) / len(ok)) if ok else float('nan'):6.2f} "
              f"{sum(r['n_target'] for r in ok) / tot:7.2f} {sum(r['n_both'] for r in ok) / tot:6.2f} "
              f"{sum(r['n_other'] for r in ok) / tot:6.2f} {sum(r['parse_fail'] for r in rs) / len(rs):7.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
