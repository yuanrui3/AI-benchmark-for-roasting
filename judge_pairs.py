"""Have each judge rate the SAME pairs the humans see, in both orders.

    uv run python judge_pairs.py --run mock --mock
    uv run python judge_pairs.py --run pilot --budget 8

This is what judge-human agreement is computed from (analyze.py), next to the
human-human ceiling. Gold pairs are included, so the judge's attention-check
accuracy is comparable to the raters'.

Output: runs/<run>/judge_pairs.jsonl, one row per pair x order x judge.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from common import ROOT, append_jsonl, parse_letter, read_jsonl, utf8_stdout
from damage import JUDGE_SYSTEM, judge_prompt
from llm import LLM, BudgetExceeded


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--budget", type=float, default=40.0, help="run-wide USD cap (ledger is shared by all stages)")
    ap.add_argument("--judges", default=None, help="comma list; default: every judge whose key exists")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--effort", default=config.PAIR_JUDGE_EFFORT, help="judge reasoning effort: low | medium | high")
    ap.add_argument("--pairs", default="rate/pairs.json", help="pool to judge, under runs/<run>")
    ap.add_argument("--out", default="judge_pairs.jsonl", help="output file under runs/<run>")
    ap.add_argument("--per-lang", type=int, default=None,
                    help="judge only the first N pairs per language, in file order (the order raters see); default all")
    args = ap.parse_args()

    run_dir = ROOT / "runs" / args.run
    pairs = json.loads((run_dir / args.pairs).read_text(encoding="utf-8"))["pairs"]
    if args.per_lang:
        seen: dict[str, int] = {}
        kept = []
        for p in pairs:
            seen[p["lang"]] = seen.get(p["lang"], 0) + 1
            if seen[p["lang"]] <= args.per_lang:
                kept.append(p)
        pairs = kept
    judge_names = args.judges.split(",") if args.judges else config.usable_judges(args.mock)
    judges = {j: config.MODELS[config.JUDGES[j]] for j in judge_names}
    out_path = run_dir / args.out
    done = {(r["pair_id"], r["order"], r["judge"]) for r in read_jsonl(out_path)} if out_path.exists() else set()
    jobs = [(p, o, j) for p in pairs for o in ("ab", "ba") for j in judges if (p["pair_id"], o, j) not in done]
    print(f"{len(pairs)} pairs x 2 orders x {len(judges)} judges -> {len(jobs)} calls to do")

    llm = LLM(run_dir, budget_usd=args.budget, mock=args.mock)
    lock = threading.Lock()
    stop = threading.Event()

    def work(job):
        p, order, jname = job
        if stop.is_set():
            return
        spec = judges[jname]
        first, second = (p["a"], p["b"]) if order == "ab" else (p["b"], p["a"])
        try:
            res = llm.call(spec, JUDGE_SYSTEM, judge_prompt(first["text"], second["text"], p["lang"], p["target_name"], p["facts"]),
                           max_tokens=config.JUDGE_MAX_TOKENS, effort=args.effort,
                           tag=f"judge_pairs:{jname}")
        except BudgetExceeded as e:
            stop.set()
            print(f"BUDGET: {e}")
            return
        if res.error:  # not persisted: the ledger keeps the error and the next run retries the call
            print(f"  failed, will retry next run: {res.error[:80]}", flush=True)
            return
        ans = parse_letter(res.text)
        # map the letter back to the pair's canonical a/b
        winner = None
        if ans:
            winner = ("a" if ans == "A" else "b") if order == "ab" else ("b" if ans == "A" else "a")
        row = {"pair_id": p["pair_id"], "lang": p["lang"], "target_id": p["target_id"], "order": order, "judge": jname,
               "judge_family": spec.family, "winner": winner, "winner_item": p[winner]["item_id"] if winner else None,
               "chose_first": ans == "A", "parse_fail": ans is None, "gold": p.get("gold"),
               "gold_correct": (p["gold"]["better"] == winner) if p.get("gold") and winner else None,
               "cost_usd": res.cost_usd, "error": res.error}
        with lock:
            append_jsonl(out_path, row)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for _ in as_completed([ex.submit(work, j) for j in jobs]):
            pass
    rows = read_jsonl(out_path)
    print(f"spent ${llm.spent_usd:.2f}; {len(rows)} judgements")
    for j in sorted({r["judge"] for r in rows}):
        rs = [r for r in rows if r["judge"] == j]
        gold = [r for r in rs if r["gold_correct"] is not None]
        p_first = sum(r["chose_first"] for r in rs) / len(rs)
        print(f"  {j}: P(first)={p_first:.2f}  gold acc={sum(r['gold_correct'] for r in gold) / len(gold) if gold else float('nan'):.2f} "
              f"parse fail={sum(r['parse_fail'] for r in rs) / len(rs):.2f}")
    return 0 if not stop.is_set() else 3


if __name__ == "__main__":
    sys.exit(main())
