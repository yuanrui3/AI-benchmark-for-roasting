"""Turn any set of jokes with a scalar human score into a pairs file for external_anchor.py.

    uv run python rated_pairs.py --items my_jokes.jsonl --out ext-data/pairs_mine.jsonl --min-gap 2 --n 1200
    uv run python rated_pairs.py --items … --out … --id-field n --text-field text --score-field score --group-field group \
        --source mine --context "Two lines from the same stand-up set."

Input: one JSON object per line with an id, a text and a number a human gave it (a 0-10 rating, an upvote count, a
mean crowd grade); rows without a score are skipped. Output: one pair per line, {id, source, context, a, b, human,
confidence}, where `human` is the side with the higher score and `confidence` is the score gap, the format
external_anchor.py judges. Keep both files outside git when the text is not yours to publish (ext-data/ is ignored).

Only pairs at least --min-gap apart are used: a one-point gap on a ten-point scale is inside one rater's own noise.
Pairs are drawn so no item appears in more than its share (an outlier would otherwise be in every pair), half from
the same group (same section or topic, so topic is held fixed) and half across groups when a group field is given.
The pick is one rater's or one crowd's taste: read the agreement number as calibration, not as ground truth.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

from common import read_jsonl, utf8_stdout


def draw(cands: list[tuple], n: int, cap: int, rng: random.Random) -> list[tuple]:
    rng.shuffle(cands)
    used: Counter = Counter()
    out = []
    for a, b in cands:
        if len(out) >= n:
            break
        if used[a["_id"]] >= cap or used[b["_id"]] >= cap:
            continue
        used[a["_id"]] += 1
        used[b["_id"]] += 1
        out.append((a, b))
    return out


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--id-field", default="id")
    ap.add_argument("--text-field", default="text")
    ap.add_argument("--score-field", default="score")
    ap.add_argument("--group-field", default=None, help="section or topic; enables same-group and cross-group halves")
    ap.add_argument("--source", default="rated", help="label written to each pair's `source` (suffix -same / -cross)")
    ap.add_argument("--context", default="", help="one line shown to the judge before every pair")
    ap.add_argument("--min-gap", type=float, default=2.0)
    ap.add_argument("--n", type=int, default=1200)
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args()

    items = []
    for r in read_jsonl(Path(args.items)):
        s, t = r.get(args.score_field), r.get(args.text_field)
        if isinstance(s, (int, float)) and isinstance(t, str) and t.strip():
            items.append({"_id": str(r[args.id_field]), "_text": t.strip(), "_score": float(s),
                          "_group": r.get(args.group_field) if args.group_field else None})
    rng = random.Random(args.seed)
    same, cross = [], []
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if abs(a["_score"] - b["_score"]) < args.min_gap:
                continue
            (same if args.group_field and a["_group"] == b["_group"] else cross).append((a, b))
    want_same = min(len(same), args.n // 2) if args.group_field else 0
    want_cross = min(len(cross), args.n - want_same)
    cap = max(4, math.ceil(2 * args.n / max(1, len(items)) * 1.5))
    chosen = [("same", p) for p in draw(same, want_same, cap, rng)] + [("cross", p) for p in draw(cross, want_cross, cap, rng)]
    rng.shuffle(chosen)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for kind, (a, b) in chosen:
            if rng.random() < 0.5:
                a, b = b, a
            f.write(json.dumps({
                "id": f"{args.source}-{a['_id']}-{b['_id']}",
                "source": f"{args.source}-{kind}" if args.group_field else args.source,
                "context": args.context, "a": a["_text"], "b": b["_text"],
                "human": "a" if a["_score"] > b["_score"] else "b",
                "confidence": abs(a["_score"] - b["_score"]),
            }, ensure_ascii=False) + "\n")
    gaps = Counter(abs(a["_score"] - b["_score"]) for _, (a, b) in chosen)
    print(f"{len(items)} scored items; eligible pairs: {len(same)} same-group, {len(cross)} cross-group (gap >= {args.min_gap})")
    print(f"wrote {len(chosen)} pairs -> {out}  ({sum(k == 'same' for k, _ in chosen)} same-group, "
          f"{sum(k == 'cross' for k, _ in chosen)} cross-group; per-item cap {cap})")
    print("gap histogram:", dict(sorted(gaps.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
