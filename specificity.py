"""Specificity gate: masked swap test (k=5, twin included) plus model-free lexical checks.

    uv run python specificity.py --run mock --mock
    uv run python specificity.py --run pilot --budget 10

For every item: mask the target's names (and the twin's), check for leaked name words,
compute a lexical twin-contrast score, then ask each judge which of five candidates
(target, twin, three random others) the masked text is about.

Output: runs/<run>/specificity.jsonl (one line per item x judge) and a per-arm summary.
Chance is 20%; on the twin-only question it is 50%.
"""
from __future__ import annotations

import argparse
import random
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import config
from common import (ROOT, MASK, append_jsonl, distinctive_words, jaccard, leaked_words, load_targets, mask_text,
                    parse_digit, read_jsonl, tokens, utf8_stdout)
from llm import LLM, BudgetExceeded

K = 5
JUDGE_SYSTEM = "You are a careful reader taking a quiz. Follow the answer format exactly."


def judge_prompt(masked: str, names: list[str], lang: str) -> str:
    opts = "\n".join(f"{i + 1}. {n}" for i, n in enumerate(names))
    if lang == "zh":
        return (f"下面这段话里，被吐槽的对象的名字被替换成了 {MASK}（相关的另一个对象替换成了 [OTHER]）。\n\n"
                f"---\n{masked}\n---\n\n它吐槽的是哪一个？\n{opts}\n\nAnswer with the number only.")
    return (f"In the passage below, the target's name has been replaced with {MASK} (a related thing with [OTHER]).\n\n"
            f"---\n{masked}\n---\n\nWhich of these is the target?\n{opts}\n\nAnswer with the number only.")


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--budget", type=float, default=40.0, help="run-wide USD cap (ledger is shared by all stages)")
    ap.add_argument("--judges", default=None, help="comma list; default: every judge whose key exists")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    run_dir = ROOT / "runs" / args.run
    items = [r for r in read_jsonl(run_dir / "items.jsonl") if r["text"].strip() and not r["refused"] and not r["error"]]
    targets = load_targets()
    distinct = distinctive_words(targets)
    fact_tokens = {tid: tokens(" ".join(t["facts"]) + " " + t["name"]) for tid, t in targets.items()}
    judge_names = args.judges.split(",") if args.judges else config.usable_judges(args.mock)
    judges = {j: config.MODELS[config.JUDGES[j]] for j in judge_names}
    out_path = run_dir / "specificity.jsonl"
    done = {(r["item_id"], r["judge"]) for r in read_jsonl(out_path)} if out_path.exists() else set()

    llm = LLM(run_dir, budget_usd=args.budget, mock=args.mock)
    lock = threading.Lock()
    stop = threading.Event()
    ids = sorted(targets)

    jobs = []
    for it in items:
        t = targets[it["target_id"]]
        twin = targets.get(t["twin"])
        masked = mask_text(it["text"], t, twin, distinct)
        leaks = leaked_words(masked, distinct[t["id"]])  # residual only: inflections the word-boundary regex missed
        toks = tokens(masked)
        lex_target = jaccard(toks, fact_tokens[t["id"]])
        lex_twin = jaccard(toks, fact_tokens[t["twin"]]) if twin else 0.0
        rng = random.Random(f"{args.seed}|{it['item_id']}")
        others = rng.sample([i for i in ids if i not in (t["id"], t["twin"])], K - 2)
        cands = [t["id"], t["twin"]] + others
        rng.shuffle(cands)
        names = [config.target_name(targets[c], it["lang"]) for c in cands]
        base = {
            "item_id": it["item_id"], "target_id": t["id"], "arm": it["arm"], "kind": it["kind"], "lang": it["lang"],
            "gen_family": it["family"], "masked_len": len(masked), "leaks": leaks,
            "lex_target": round(lex_target, 4), "lex_twin": round(lex_twin, 4),
            "lex_contrast": round(lex_target - lex_twin, 4), "candidates": cands,
        }
        for jname, spec in judges.items():
            if (it["item_id"], jname) in done:
                continue
            jobs.append((base, jname, spec, judge_prompt(masked, names, it["lang"])))

    print(f"{len(items)} items, {len(judges)} judges -> {len(jobs)} judge calls to do")

    def work(job):
        base, jname, spec, prompt = job
        if stop.is_set():
            return
        try:
            res = llm.call(spec, JUDGE_SYSTEM, prompt, max_tokens=config.JUDGE_MAX_TOKENS, effort=config.JUDGE_EFFORT,
                           key=f"spec|{args.run}|{base['item_id']}|{jname}", tag=f"spec:{jname}")
        except BudgetExceeded as e:
            stop.set()
            print(f"BUDGET: {e}")
            return
        ans = parse_digit(res.text, K)
        picked = base["candidates"][ans - 1] if ans else None
        row = {**base, "judge": jname, "judge_family": spec.family, "answer_raw": res.text[:40], "picked": picked,
               "correct": picked == base["target_id"], "picked_twin": picked == targets[base["target_id"]]["twin"],
               "parse_fail": ans is None, "cost_usd": res.cost_usd, "error": res.error}
        with lock:
            append_jsonl(out_path, row)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for _ in as_completed([ex.submit(work, j) for j in jobs]):
            pass

    rows = read_jsonl(out_path)
    print(f"\nspent ${llm.spent_usd:.2f}. Per arm (all judges pooled): acc = picked target; twin-acc = target vs twin "
          f"when one of the pair was picked; leak = share of items with a distinctive name word unmasked")
    print(f"{'arm':18s} {'lang':4s} {'n':>4s} {'acc':>6s} {'twin':>6s} {'leak':>6s} {'lex':>7s} {'parse✗':>7s}")
    for arm in sorted({r["arm"] for r in rows}):
        for lang in sorted({r["lang"] for r in rows}):
            rs = [r for r in rows if r["arm"] == arm and r["lang"] == lang]
            if not rs:
                continue
            pair = [r for r in rs if r["correct"] or r["picked_twin"]]
            acc = sum(r["correct"] for r in rs) / len(rs)
            twin_acc = (sum(r["correct"] for r in pair) / len(pair)) if pair else float("nan")
            leak = sum(bool(r["leaks"]) for r in rs) / len(rs)
            lex = sum(r["lex_contrast"] for r in rs) / len(rs)
            pf = sum(r["parse_fail"] for r in rs) / len(rs)
            print(f"{arm:18s} {lang:4s} {len(rs):4d} {acc:6.2f} {twin_acc:6.2f} {leak:6.2f} {lex:7.3f} {pf:7.2f}")
    return 0 if not stop.is_set() else 3


if __name__ == "__main__":
    sys.exit(main())
