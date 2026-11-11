"""Leaderboard: Bradley-Terry over every judged pool, per judge and language, with bootstrap intervals.

    uv run python leaderboard.py --run pilot                     # judge-opus, all pools found -> runs/pilot/leaderboard.md
    uv run python leaderboard.py --run pilot --judge judge-sonnet

Every judgement (each order of each non-gold pair) is one vote between two arms. Pools are pooled: the main pool
links the controls to the Opus prompts, the ladder pools link Sonnet and Haiku to Opus on the same prompt, so the
comparison graph is connected and one scale covers every arm. Scores are log-odds centred on zero; a one-point gap
means the higher arm wins about 73% of pairs against the lower. Intervals are percentile bootstraps over pairs.
Judge opinions are not human votes: read the table as "what a validated judge prefers", with analyze.py's damage
tests and the external anchor as the judge's credentials.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

from common import ROOT, read_jsonl, utf8_stdout

POOLS = {"rate": "judge_pairs.jsonl", "rate-opus": "judge_pairs_opus.jsonl",
         "rate-ladder-plain": "judge_pairs_ladder_plain.jsonl", "rate-ladder-frame": "judge_pairs_ladder_frame.jsonl",
         "rate-frame": "judge_pairs_frame.jsonl", "rate-frame-en": "judge_pairs_frame_en.jsonl",
         "rate-cn": "judge_pairs_cn.jsonl"}


def bradley_terry(votes: list[tuple[str, str]], iters: int = 200) -> dict[str, float]:
    """votes = (winner arm, loser arm). MM algorithm; returns log-scores centred on zero."""
    arms = sorted({a for v in votes for a in v})
    wins = defaultdict(float)
    games = defaultdict(float)
    for w, l in votes:
        wins[w] += 1
        games[(w, l)] += 1
        games[(l, w)] += 1
    p = {a: 1.0 for a in arms}
    for _ in range(iters):
        new = {}
        for a in arms:
            denom = sum(n / (p[a] + p[b]) for (x, b), n in games.items() if x == a)
            new[a] = (wins[a] + 0.5) / denom if denom else p[a]   # +0.5 keeps an all-losing arm finite
        s = sum(new.values()) / len(new)
        p = {a: v / s for a, v in new.items()}
    logs = {a: math.log(v) for a, v in p.items()}
    mean = sum(logs.values()) / len(logs)
    return {a: v - mean for a, v in logs.items()}


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--judge", default="judge-opus")
    ap.add_argument("--boot", type=int, default=200)
    ap.add_argument("--seed", type=int, default=5)
    args = ap.parse_args()
    run_dir = ROOT / "runs" / args.run
    items = {r["item_id"]: r for r in read_jsonl(run_dir / "items.jsonl")}

    # pair-level votes: (lang, winner arm, loser arm), one per judgement
    votes_by_pair: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    used = []
    for pool, jf in POOLS.items():
        pp, jp = run_dir / pool / "pairs.json", run_dir / jf
        if not pp.exists() or not jp.exists():
            continue
        pairs = {p["pair_id"]: p for p in json.loads(pp.read_text(encoding="utf-8"))["pairs"]}
        n = 0
        for r in read_jsonl(jp):
            p = pairs.get(r["pair_id"])
            if r["judge"] != args.judge or not p or p.get("gold") or r.get("winner") not in ("a", "b"):
                continue
            a, b = items.get(p["a"]["item_id"]), items.get(p["b"]["item_id"])
            if not a or not b or a["arm"] == b["arm"]:
                continue
            w, l = (a, b) if r["winner"] == "a" else (b, a)
            votes_by_pair[(p["lang"], f"{pool}:{r['pair_id']}")].append((w["arm"], l["arm"]))
            n += 1
        used.append(f"{pool} ({n} judgements)")
    if not votes_by_pair:
        print("no judgements found for", args.judge)
        return 1

    rng = random.Random(args.seed)
    lines = [f"# Leaderboard: run `{args.run}`, judge `{args.judge}`", "",
             "Bradley-Terry log-odds over every judged pool (" + ", ".join(used) + "), centred on zero; "
             "a one-point gap is about a 73% win rate. 95% intervals: percentile bootstrap over pairs "
             f"({args.boot} resamples). The judge's credentials are in report.md (damage tests) and CLAUDE.md "
             "(external anchor); this is the judge's opinion, not human votes.", ""]
    for lang in ("en", "zh"):
        keys = [k for k in votes_by_pair if k[0] == lang]
        if not keys:
            continue
        votes = [v for k in keys for v in votes_by_pair[k]]
        score = bradley_terry(votes)
        boots: dict[str, list[float]] = defaultdict(list)
        for _ in range(args.boot):
            sample = [v for k in rng.choices(keys, k=len(keys)) for v in votes_by_pair[k]]
            for a, s in bradley_terry(sample, iters=60).items():
                boots[a].append(s)
        wins = defaultdict(lambda: [0, 0])
        for w, l in votes:
            wins[w][0] += 1
            wins[w][1] += 1
            wins[l][1] += 1
        lines += [f"## {lang}: {len(keys)} pairs, {len(votes)} judgements", "",
                  "| arm | score | 95% CI | win rate | judgements |", "|---|---:|---|---:|---:|"]
        for a, s in sorted(score.items(), key=lambda kv: -kv[1]):
            b = sorted(boots[a])
            lo, hi = b[int(0.025 * len(b))], b[int(0.975 * len(b)) - 1]
            w, n = wins[a]
            lines.append(f"| {a} | {s:+.2f} | [{lo:+.2f}, {hi:+.2f}] | {w / n:.2f} | {n} |")
        lines.append("")
    out = run_dir / "leaderboard.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
