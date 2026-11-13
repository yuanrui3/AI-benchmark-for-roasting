"""What predicts the author's 0-10 punchline scores? No model calls.

    uv run python talkshow/analysis/analyze.py        # the output is kept in findings.txt

Reads ../ratings/punchlines.jsonl (written by build.py). Prints: the score distribution, kept vs deleted lines, score against who the
material came from (paragraph AI share 0..1 from the attribution page; the rating page's own source notes), score
against free text features (the same family metric_check.py tests against the Opus judge), the author's notes by
score, and drift over the rating session.
"""
import json
import pathlib
import re
import statistics as st
from collections import Counter, defaultdict

from scipy import stats

BASE = pathlib.Path(__file__).resolve().parent.parent
import sys
sys.stdout.reconfigure(encoding="utf-8")
rows = [json.loads(l) for l in (BASE / "ratings" / "punchlines.jsonl").read_text(encoding="utf-8").splitlines()]
S = [r for r in rows if r["score"] is not None]


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def line(label, xs):
    return f"  {label:34s} n={len(xs):3d}  mean {mean(xs):.2f}  median {st.median(xs) if xs else float('nan')}"


print(f"## {len(S)} scored punchlines: mean {mean([r['score'] for r in S]):.2f}, sd {st.pstdev([r['score'] for r in S]):.2f}")
print("  histogram:", dict(sorted(Counter(r["score"] for r in S).items())))

print("\n## kept vs deleted")
kept = [r["score"] for r in S if not r["deleted"]]
dele = [r["score"] for r in S if r["deleted"]]
print(line("kept in the script", kept))
print(line("deleted later", dele))
print("  Mann-Whitney p = %.2g" % stats.mannwhitneyu(kept, dele).pvalue)
print("  delete reasons:", "; ".join(f"[{r['score']}] {r['delete_reason']}" for r in S if r["deleted"] and r["delete_reason"])[:900])

print("\n## rewritten after rating (text now differs from the text as rated), kept lines only")
ch = [r["score"] for r in S if not r["deleted"] and r["text_changed"]]
un = [r["score"] for r in S if not r["deleted"] and not r["text_changed"]]
print(line("rewritten later", ch))
print(line("left as rated", un))

print("\n## score vs who it came from: paragraph AI share (0 = co-author, 1 = AI), matched kept lines")
M = [r for r in S if r["block_ai_share"] is not None and not r["deleted"]]
rho = stats.spearmanr([r["block_ai_share"] for r in M], [r["score"] for r in M])
print(f"  n={len(M)}  Spearman rho = {rho.statistic:+.3f}  p = {rho.pvalue:.3g}")
for lo, hi, lab in [(0, 0.35, "co-author-led (AI share <= 0.35)"), (0.35, 0.65, "mixed (0.35-0.65)"), (0.65, 1.01, "AI-led (>= 0.65)")]:
    print(line(lab, [r["score"] for r in M if lo <= r["block_ai_share"] < hi or (hi > 1 and r["block_ai_share"] >= lo)]))
top = [r for r in M if r["score"] >= 9]
low = [r for r in M if r["score"] <= 6]
print(f"  mean AI share of lines scored >= 9: {mean([r['block_ai_share'] for r in top]):.2f} (n={len(top)}); "
      f"of lines scored <= 6: {mean([r['block_ai_share'] for r in low]):.2f} (n={len(low)}); all: {mean([r['block_ai_share'] for r in M]):.2f}")

print("\n## score vs the rating page's own source note (lines that carry one)")
by = defaultdict(list)
for r in S:
    if not r["deleted"]:
        by[r["source_class"] or ("note, unclassified" if r["source_note"] else "no note (older lines)")].append(r["score"])
for k in ["human_verbatim", "human_idea", "ai_original", "note, unclassified", "no note (older lines)"]:
    if by.get(k):
        print(line(k, by[k]))
hv, ao = by.get("human_verbatim", []) + by.get("human_idea", []), by.get("ai_original", [])
if hv and ao:
    print("  co-author material (verbatim + idea) vs AI-original: Mann-Whitney p = %.2g" % stats.mannwhitneyu(hv, ao).pvalue)

print("\n## score vs free text features (kept lines); Spearman rho, and mean score with / without")
K = [r for r in S if not r["deleted"]]


def feats(r):
    t = r["text"]
    body = re.sub(r"【[^】]*】|（[^）]*）", "", t)
    sents = [s for s in re.split(r"[。！？!?；;]+", body) if s.strip()]
    chars = len(re.sub(r"\s", "", body))
    return {
        "chars": chars,
        "sentences": len(sents),
        "chars/sentence": chars / max(1, len(sents)),
        "has a number": 1 if re.search(r"\d|[一二三四五六七八九十百千万亿]{2,}", body) else 0,
        "sourced fact (has links)": 1 if r["source_links"] else 0,
        "marked pause （停一拍）": 1 if "停一拍" in t else 0,
        "audience in the bit (【…】/举手/那位)": 1 if re.search(r"【[^】]*(笑|喊|鼓掌|全场|观众|有人)[^】]*】|举手|那位|前排|后排", t) else 0,
        "callback (阿希/牢A/回扣)": 1 if ("阿希" in t or "牢A" in t or "回扣" in (r["source_note"] or "")) else 0,
        "AI-jargon mapping": 1 if re.search(r"预训练|蒸馏|对齐|回滚|幻觉|上下文|提示词|训练数据|版本|微调|token|模型|参数|检测器|温度", t) else 0,
        "self-roast (我/我们这行/我老板)": 1 if re.search(r"我老板|我们这行|我们行业|我东家|我自己|我也", t) else 0,
    }


F = [(feats(r), r["score"]) for r in K]
for name in F[0][0]:
    xs = [f[name] for f, _ in F]
    ys = [s for _, s in F]
    rho = stats.spearmanr(xs, ys)
    if set(xs) <= {0, 1}:
        a = [s for f, s in F if f[name] == 1]
        b = [s for f, s in F if f[name] == 0]
        print(f"  {name:38s} rho {rho.statistic:+.2f} (p={rho.pvalue:.2g})   with: {mean(a):.2f} (n={len(a)})   without: {mean(b):.2f} (n={len(b)})")
    else:
        print(f"  {name:38s} rho {rho.statistic:+.2f} (p={rho.pvalue:.2g})   mean {mean(xs):.1f}")

print("\n## score by section (kept lines, sections with >= 8)")
sec = defaultdict(list)
for r in K:
    sec[r["section"]].append(r["score"])
for g, xs in sorted(sec.items(), key=lambda kv: -mean(kv[1])):
    if len(xs) >= 8:
        print(f"  {mean(xs):.2f}  n={len(xs):2d}  {g}")

print("\n## the author's notes, by score")
for r in sorted([r for r in S if r["note"]], key=lambda r: r["score"]):
    print(f"  [{r['score']}] n={r['n']:3d} {r['note'][:110]}")

print("\n## drift over the rating session (order of saving)")
T = sorted([r for r in S if r["rated_at"]], key=lambda r: r["rated_at"])
q = len(T) // 4
for i in range(4):
    part = T[i * q:(i + 1) * q if i < 3 else len(T)]
    print(f"  quarter {i + 1}: n={len(part)} mean {mean([r['score'] for r in part]):.2f}  ({part[0]['rated_at'][11:16]}–{part[-1]['rated_at'][11:16]} UTC)")
