"""Read a judge's verdicts on any pool: win rate per arm, head-to-head grid, gold accuracy, position bias.

    uv run python pool_rank.py --run pilot                                              # main pool, judge_pairs.jsonl
    uv run python pool_rank.py --run pilot --pool rate-ladder-plain --judge judge_pairs_ladder_plain.jsonl
    uv run python pool_rank.py --run pilot --pool rate-opus --judge judge_pairs_opus.jsonl --only judge-opus

analyze.py reads only the main pool (rate/); this reads the judge-only pools (ladder, all-Opus, framing) the same way.
A win rate is over the pairs the arm appeared in, so arms with different opponents are not on one scale: read the
head-to-head grid for that. Wilson 95% intervals on the win rates; a judge that flips with the order on many pairs
has little to say about those pairs (frame_test.py counts the flips for the framing pools).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict

from common import ROOT, read_jsonl, utf8_stdout


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z = 1.96
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--pool", default="rate", help="folder under runs/<run> with pairs.json")
    ap.add_argument("--judge", default="judge_pairs.jsonl", help="judge rows for this pool, under runs/<run>")
    ap.add_argument("--only", default=None, help="comma list of judge names to report (default: all in the file)")
    args = ap.parse_args()

    run_dir = ROOT / "runs" / args.run
    items = {r["item_id"]: r for r in read_jsonl(run_dir / "items.jsonl")}
    pairs = {p["pair_id"]: p for p in json.loads((run_dir / args.pool / "pairs.json").read_text(encoding="utf-8"))["pairs"]}
    rows = read_jsonl(run_dir / args.judge)
    only = set(args.only.split(",")) if args.only else None

    wins: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0, 0])))   # judge -> lang -> arm -> [w, n]
    h2h: dict = defaultdict(lambda: defaultdict(lambda: [0, 0]))                         # (judge, lang) -> (x, y) -> [x wins, n]
    gold: dict = defaultdict(lambda: [0, 0])
    first: dict = defaultdict(lambda: [0, 0])
    for r in rows:
        p = pairs.get(r["pair_id"])
        if not p or r.get("winner") not in ("a", "b") or (only and r["judge"] not in only):
            continue
        j, lang, pick = r["judge"], p["lang"], r["winner"]
        if r.get("chose_first") is not None:
            first[(j, lang)][0] += bool(r["chose_first"])
            first[(j, lang)][1] += 1
        if p["gold"]:
            gold[(j, lang)][0] += pick == p["gold"]["better"]
            gold[(j, lang)][1] += 1
            continue
        a, b = items.get(p["a"]["item_id"]), items.get(p["b"]["item_id"])
        if not a or not b:
            continue
        w, l = (a, b) if pick == "a" else (b, a)
        wins[j][lang][w["arm"]][0] += 1
        wins[j][lang][w["arm"]][1] += 1
        wins[j][lang][l["arm"]][1] += 1
        x, y = sorted([a["arm"], b["arm"]])
        h2h[(j, lang)][(x, y)][0] += w["arm"] == x
        h2h[(j, lang)][(x, y)][1] += 1

    print(f"pool {args.pool}: {len(pairs)} pairs, {sum(bool(p['gold']) for p in pairs.values())} gold; "
          f"{len(rows)} judge rows in {args.judge}")
    for j in sorted(wins):
        for lang in sorted(wins[j]):
            print(f"\n== {j} {lang}: win rate per arm, non-gold pairs, both orders")
            for arm, (w, n) in sorted(wins[j][lang].items(), key=lambda kv: -kv[1][0] / max(kv[1][1], 1)):
                lo, hi = wilson(w, n)
                print(f"  {arm:16s} {w:4d}/{n:<4d} {w / n:5.2f}  [{lo:.2f}, {hi:.2f}]")
            g, f = gold[(j, lang)], first[(j, lang)]
            line = f"  gold {g[0]}/{g[1]}" if g[1] else "  no gold pairs"
            if f[1]:
                line += f"   P(first) {f[0] / f[1]:.2f} (n={f[1]})"
            print(line)
            print("  head-to-head, share won by the first-named arm:")
            for (x, y), (w, n) in sorted(h2h[(j, lang)].items()):
                lo, hi = wilson(w, n)
                print(f"    {x:16s} vs {y:16s} {w:4d}/{n:<4d} {w / n:5.2f}  [{lo:.2f}, {hi:.2f}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
