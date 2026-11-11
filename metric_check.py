"""Do the unsupervised metrics predict which roast the validated judge prefers?

    uv run python metric_check.py --run pilot                       # judge-opus over the judged pools
    uv run python metric_check.py --run pilot --judge judge-opus --pools rate-opus:judge_pairs_opus.jsonl

For every judged pair where the judge picked the same item in both orders (a decisive pair), and for every
item-level metric where the two items differ, the share of pairs in which the winner has the higher value, with a
Wilson 95% interval. 50% means the metric says nothing about the judge's taste; well above or below 50% means it
tracks (or anti-tracks) it. Cross-arm pools confound metric with prompt (a frame arm is both more agentive and a
different prompt), so the same-prompt ladder pools are the cleaner read and the all-Opus pool is also broken down by
arm pair. Metrics: agent-action rate per labeller (agency.jsonl), truth pass and claim counts (truth.jsonl, the
judge's own rows), device shared with another arm (devices.jsonl, the judge's own cells), words, sentences, words
per sentence, and, when depth.jsonl exists, sentence-level specificity depth.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

from common import ROOT, count_words, read_jsonl, utf8_stdout

DEFAULT_POOLS = ["rate-opus:judge_pairs_opus.jsonl", "rate-ladder-plain:judge_pairs_ladder_plain.jsonl",
                 "rate-ladder-frame:judge_pairs_ladder_frame.jsonl", "rate:judge_pairs.jsonl"]
_SENT = re.compile(r"[.!?。！？]+")


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def item_metrics(run_dir: Path, items: dict[str, dict], judge: str) -> dict[str, dict[str, float]]:
    """metric name -> item_id -> value"""
    m: dict[str, dict[str, float]] = defaultdict(dict)
    for iid, it in items.items():
        text = it["text"]
        words = count_words(text, it["lang"])
        sents = max(1, len([s for s in _SENT.split(text) if s.strip()]))
        m["words"][iid] = words
        m["sentences"][iid] = sents
        m["words/sentence"][iid] = words / sents
    ap = run_dir / "agency.jsonl"
    if ap.exists():
        for r in read_jsonl(ap):
            if r.get("agent_rate") is not None:
                m[f"agent-action ({r['judge']})"][r["item_id"]] = r["agent_rate"]
    tp = run_dir / "truth.jsonl"
    if tp.exists():
        for r in read_jsonl(tp):
            if r["judge"] != judge or r.get("parse_fail"):
                continue
            m["truth pass"][r["item_id"]] = 1.0 if r["passes"] else 0.0
            claims = r.get("claims")
            m["claims/item"][r["item_id"]] = len(claims) if isinstance(claims, list) else (
                r.get("n_supported", 0) + r.get("n_contradicted", 0) + r.get("n_absent", 0))
            m["absent claims"][r["item_id"]] = r.get("n_absent", 0)
    dp = run_dir / "devices.jsonl"
    if dp.exists():
        for r in read_jsonl(dp):
            if r["judge"] != judge or r.get("parse_fail"):
                continue
            for g in r["groups"]:
                arms = [items[i]["arm"] for i in g["item_ids"] if i in items]
                for iid in g["item_ids"]:
                    if iid in items:
                        others = [a for j, a in zip(g["item_ids"], arms) if j != iid]
                        m["device shared with another arm"][iid] = 1.0 if any(a != items[iid]["arm"] for a in others) else 0.0
    sp = run_dir / "depth.jsonl"
    if sp.exists():
        for r in read_jsonl(sp):
            if r.get("depth") is not None:
                m[f"specificity depth ({r['judge']})"][r["item_id"]] = r["depth"]
    return m


def decisive_pairs(run_dir: Path, pool: str, judge_file: str, judge: str) -> list[tuple[str, str, str, str]]:
    """(lang, winner_item, loser_item, arm-pair label) for pairs the judge decided the same way in both orders."""
    import json
    pairs = {p["pair_id"]: p for p in json.loads((run_dir / pool / "pairs.json").read_text(encoding="utf-8"))["pairs"]}
    picks: dict[str, dict[str, str]] = defaultdict(dict)
    for r in read_jsonl(run_dir / judge_file):
        if r["judge"] == judge and r.get("winner_item"):
            picks[r["pair_id"]][r["order"]] = r["winner_item"]
    out = []
    for pid, d in picks.items():
        p = pairs.get(pid)
        if not p or p.get("gold") or len(d) != 2:
            continue
        w = set(d.values())
        if len(w) != 1:
            continue
        win = w.pop()
        a, b = p["a"]["item_id"], p["b"]["item_id"]
        lose = b if win == a else a
        out.append((p["lang"], win, lose))
    return out


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--judge", default="judge-opus")
    ap.add_argument("--pools", default=",".join(DEFAULT_POOLS), help="comma list of <pool>:<judge file>")
    args = ap.parse_args()
    run_dir = ROOT / "runs" / args.run
    items = {r["item_id"]: r for r in read_jsonl(run_dir / "items.jsonl")}
    metrics = item_metrics(run_dir, items, args.judge)

    for spec in args.pools.split(","):
        pool, jf = spec.split(":")
        if not (run_dir / pool / "pairs.json").exists() or not (run_dir / jf).exists():
            continue
        dec = decisive_pairs(run_dir, pool, jf, args.judge)
        print(f"\n## {pool} ({args.judge}): {len(dec)} decisive pairs")
        print(f"{'metric':36s} {'lang':4s} {'n':>5s} {'P(winner higher)':>17s}  95% CI")
        for name, vals in metrics.items():
            for lang in ("en", "zh"):
                k = n = 0
                for lg, w, l in dec:
                    if lg != lang or w not in vals or l not in vals or vals[w] == vals[l]:
                        continue
                    n += 1
                    k += vals[w] > vals[l]
                if n >= 20:
                    lo, hi = wilson(k, n)
                    flag = " *" if lo > 0.5 or hi < 0.5 else ""
                    print(f"{name:36s} {lang:4s} {n:5d} {k / n:17.2f}  [{lo:.2f}, {hi:.2f}]{flag}")
        if pool == "rate-opus":
            key = f"agent-action ({args.judge})"
            if key in metrics:
                print("\n  agent-action by arm pair (all-Opus pool), P(winner has the higher rate):")
                by = defaultdict(lambda: [0, 0])
                for lg, w, l in dec:
                    vals = metrics[key]
                    if w in vals and l in vals and vals[w] != vals[l]:
                        kp = (lg, " vs ".join(sorted([items[w]["arm"], items[l]["arm"]])))
                        by[kp][0] += vals[w] > vals[l]
                        by[kp][1] += 1
                for (lg, ap_), (k, n) in sorted(by.items()):
                    lo, hi = wilson(k, n)
                    print(f"    {lg} {ap_:28s} {k:4d}/{n:<4d} {k / n:5.2f}  [{lo:.2f}, {hi:.2f}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
