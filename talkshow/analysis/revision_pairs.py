"""Revision pairs: a line the author deleted and the rewrite that replaced it.

    uv run python talkshow/analysis/revision_pairs.py     # -> pairs_revision.jsonl, for external_anchor.py

The rating page keeps each deleted line's reason, and where it was rewritten the reason points at the new line
("改写，见 336"). Same idea, same author pair, edited for funniness by a human: a judge that shares the author's
taste should prefer the version the author scored higher (normally the rewrite). Only one-to-one pointers are used;
"见 253–259" (four lines rewritten into seven) is skipped.
"""
import json
import pathlib
import random
import re

BASE = pathlib.Path(__file__).resolve().parent
import sys
sys.stdout.reconfigure(encoding="utf-8")
rows = {r["n"]: r for r in (json.loads(l) for l in (BASE.parent / "ratings" / "punchlines.jsonl").read_text(encoding="utf-8").splitlines())}
CONTEXT = "脱口秀《人比AI更像AI》里的两条包袱：演员是一台 AI，对着现场观众讲。两条是同一个点子的两个写法。"
rng = random.Random(5)
out = []
for r in rows.values():
    if not r["deleted"] or not r["delete_reason"]:
        continue
    m = re.search(r"见\s*(\d+)\s*$", r["delete_reason"])
    if not m:
        continue
    new = rows.get(int(m.group(1)))
    if not new or r["score"] is None or new["score"] is None or r["score"] == new["score"]:
        print(f"  skipped {r['n']} -> {m.group(1)} (scores {r['score']} / {new['score'] if new else None})")
        continue
    a, b = (r, new) if rng.random() < 0.5 else (new, r)
    out.append({"id": f"renbi-rev-{r['n']}-{new['n']}", "source": "renbi-revision", "context": CONTEXT,
                "a": a["text"], "b": b["text"], "human": "a" if a["score"] > b["score"] else "b",
                "confidence": abs(a["score"] - b["score"]), "rewrite_won": new["score"] > r["score"]})
(BASE / "pairs_revision.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in out), encoding="utf-8")
print(f"{len(out)} revision pairs; the rewrite is the author's higher-scored version in {sum(p['rewrite_won'] for p in out)}")
