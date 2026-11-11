"""Did the agent-action framing beat the plain framing? Reads a framing pool and its votes.

    uv run python frame_test.py --run pilot-or                                  # pool rate-frame, votes in votes-frame/
    uv run python frame_test.py --run mock-pilot --pool rate-frame --votes votes-frame

The pool is built by build_pairs.py --same-model --arms plain-X,frame-X,...: every pair is plain-X vs frame-X of
the same model on the same target, so a vote is about the framing, not the model. This reports, per rater and
per model, framed wins / plain wins / both bad / skipped; the framed share of decisive votes with a Wilson 95%
interval and an exact binomial p-value against 50%; the same for a judge file if one exists; and the
agent-action rates (agency.jsonl) of the two framings, one row per labeller. Writes runs/<run>/<pool>/frame_test.md.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict

from common import ROOT, read_jsonl, utf8_stdout


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def binom_p(k: int, n: int) -> float:
    if n == 0:
        return float("nan")
    try:
        from scipy.stats import binomtest
        return binomtest(k, n, 0.5).pvalue
    except Exception:  # noqa: BLE001
        return float("nan")


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--pool", default="rate-frame", help="folder under runs/<run> with pairs.json")
    ap.add_argument("--votes", default="votes-frame", help="folder under runs/<run> with rater exports")
    ap.add_argument("--judge", default="judge_pairs_frame.jsonl", help="judge rows for this pool, if any")
    args = ap.parse_args()

    run_dir = ROOT / "runs" / args.run
    pairs = {p["pair_id"]: p for p in json.loads((run_dir / args.pool / "pairs.json").read_text(encoding="utf-8"))["pairs"]}
    items = {r["item_id"]: r for r in read_jsonl(run_dir / "items.jsonl")}

    def kind_of(item_id: str) -> str | None:
        if "~" in item_id:
            return "gold"
        r = items.get(item_id)
        return r["kind"] if r else None

    def model_of(item_id: str) -> str:
        r = items.get(item_id.split("~")[0])
        return r["model"] if r else "?"

    lines: list[str] = [f"# Framing test: run `{args.run}`, pool `{args.pool}`", ""]
    n_frame_pairs = sum(1 for p in pairs.values() if not p["gold"])
    lines.append(f"{len(pairs)} pairs in the pool ({n_frame_pairs} framing pairs, {len(pairs) - n_frame_pairs} gold).")

    # ---- human votes
    votes_dir = run_dir / args.votes
    files = sorted(votes_dir.glob("*.json")) if votes_dir.exists() else []
    tally: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))  # (rater, model) -> counts
    gold_ok: dict[str, list[bool]] = defaultdict(list)
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        rater = data.get("rater", {}).get("name") or f.stem
        for v in data.get("votes", []):
            p = pairs.get(v["pair_id"])
            if not p:
                continue
            left, right, choice = v["left_item"], v["right_item"], v["choice"]
            if "~" in left or "~" in right:
                if choice in ("left", "right"):
                    chosen = left if choice == "left" else right
                    gold_ok[rater].append("~" not in chosen)
                continue
            kl, kr = kind_of(left), kind_of(right)
            if {kl, kr} != {"plain", "frame"}:
                continue
            key = (rater, model_of(left))
            if choice == "left":
                tally[key][kl] += 1
            elif choice == "right":
                tally[key][kr] += 1
            elif choice in ("both_bad", "skip"):
                tally[key][choice] += 1

    def block(title: str, groups: dict[str, dict[str, int]]) -> None:
        lines.append(f"\n## {title}\n")
        lines.append("| group | framed wins | plain wins | both bad | skipped | framed share | 95% CI | p (vs 50%) |")
        lines.append("|---|---:|---:|---:|---:|---:|---|---:|")
        tot = defaultdict(int)
        for g, c in sorted(groups.items()):
            k, n = c.get("frame", 0), c.get("frame", 0) + c.get("plain", 0)
            lo, hi = wilson(k, n)
            lines.append(f"| {g} | {k} | {c.get('plain', 0)} | {c.get('both_bad', 0)} | {c.get('skip', 0)} | "
                         f"{(k / n if n else float('nan')):.0%} | [{lo:.0%}, {hi:.0%}] | {binom_p(k, n):.3f} |")
            for kk, vv in c.items():
                tot[kk] += vv
        k, n = tot.get("frame", 0), tot.get("frame", 0) + tot.get("plain", 0)
        lo, hi = wilson(k, n)
        lines.append(f"| **all** | {k} | {tot.get('plain', 0)} | {tot.get('both_bad', 0)} | {tot.get('skip', 0)} | "
                     f"{(k / n if n else float('nan')):.0%} | [{lo:.0%}, {hi:.0%}] | {binom_p(k, n):.3f} |")

    if tally:
        by_rater: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        by_model: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for (rater, model), c in tally.items():
            for kk, vv in c.items():
                by_rater[rater][kk] += vv
                by_model[model][kk] += vv
        block("Human votes by rater", by_rater)
        block("Human votes by model", by_model)
        if gold_ok:
            lines.append("\nGold accuracy: " + ", ".join(f"{r} {sum(v)}/{len(v)}" for r, v in sorted(gold_ok.items())))
    else:
        lines.append(f"\n_No human votes yet. Rate {args.pool}/index.html and drop the exports into {args.votes}/._")

    # ---- judges
    jpath = run_dir / args.judge
    if jpath.exists():
        by_judge: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        flips: dict[str, dict[str, set]] = defaultdict(lambda: defaultdict(set))
        for r in read_jsonl(jpath):
            p = pairs.get(r["pair_id"])
            if not p or p["gold"] or not r.get("winner"):
                continue
            k = kind_of(p[r["winner"]]["item_id"])
            if k in ("plain", "frame"):
                by_judge[r["judge"]][k] += 1
                flips[r["judge"]][r["pair_id"]].add(k)
        if by_judge:
            block("Judge votes (both orders)", by_judge)
            for j, d in sorted(flips.items()):
                both = [v for v in d.values() if len(v) == 2]
                lines.append(f"- {j}: order-inconsistent on {len(both)} of {len(d)} pairs")

    # ---- agent-action rates
    apath = run_dir / "agency.jsonl"
    if apath.exists():
        langs = {p["lang"] for p in pairs.values()}
        # one row per labeller: a judge model and the free keyword rule label at very different levels, so never pool them
        rates: dict[tuple[str, str, str], list[float]] = defaultdict(list)
        for r in read_jsonl(apath):
            if r["lang"] in langs and r["kind"] in ("plain", "frame") and r["agent_rate"] is not None:
                rates[(r["judge"], r["kind"], r["lang"])].append(r["agent_rate"])
        if rates:
            lines.append("\n## Agent-action rate (agency.jsonl)\n")
            lines.append("| labeller | framing | lang | items | mean agent rate |")
            lines.append("|---|---|---|---:|---:|")
            for (j, k, lang), vals in sorted(rates.items()):
                lines.append(f"| {j} | {k} | {lang} | {len(vals)} | {sum(vals) / len(vals):.2f} |")

    text = "\n".join(lines) + "\n"
    (run_dir / args.pool / "frame_test.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
