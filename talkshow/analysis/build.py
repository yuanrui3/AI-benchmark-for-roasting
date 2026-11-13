"""Rebuild the machine-readable files of the talk-show release from its published pages.

    uv run python talkshow/analysis/build.py

Reads  attribution/standup_zh.html, standup_en.html, model_card.html  (every paragraph carries data-s, the AI's share
       of that paragraph on a 0..1 scale, and a one-line reason)
       ratings/index.html (the punchline list with section titles and source notes) and ratings/ratings_db.json (the
       author's saved scores: n, text as rated, score 0-10, note, time)
Writes attribution/*_blocks.jsonl  one row per scored paragraph: id, lang, section, ai_share, why, text
       ratings/punchlines.jsonl and punchlines.csv  one row per punchline (see the README for the columns)

A punchline is matched to the Chinese paragraph that contains the largest share of its character bigrams; the rating
page often condenses a line, so the match is fuzzy and its strength is kept (`block_match`, accepted at 0.35).
Source class comes from the rating page's own note where there is one: human_verbatim (合作者的原话), human_idea (the
co-author's idea, angle, topic or request, the AI's wording), ai_original (本稿原创), else empty.
"""
from __future__ import annotations

import csv
import html as H
import json
import re
from html.parser import HTMLParser
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
VOID = {"br", "img", "meta", "link", "input", "hr", "col", "source", "wbr"}


def squash(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip()


class Blocks(HTMLParser):
    """Collect every <div class="blk" data-s=...> with its text, the section heading above it and its inline reason."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.stack = [], []          # stack of (tag, role)
        self.lang, self.section, self.cur = None, None, None
        self.in_heading = False

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        role = None
        if tag == "div" and "art" in cls:
            self.lang = a.get("lang") or self.lang
            role = "art"
        elif tag == "div" and "blk" in cls:
            role = "blk"
            self.cur = {"id": a.get("id"), "lang": self.lang, "section": self.section,
                        "ai_share": float(a["data-s"]) if a.get("data-s") else None, "text": [], "why": [], "head": []}
        elif self.cur is not None and tag == "div" and "why" in cls:
            role = "why"
        elif self.cur is not None and tag == "span" and "chip" in cls:
            role = "chip"
        elif self.cur is not None and tag in ("h1", "h2", "h3"):
            role = "head"
        self.stack.append((tag, role))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        while self.stack:
            t, role = self.stack.pop()
            if role == "blk" and self.cur is not None:
                c = self.cur
                head = squash("".join(c["head"]))
                if head:
                    self.section = head
                if c["ai_share"] is not None and c["id"]:
                    self.rows.append({"id": c["id"], "lang": c["lang"], "section": c["section"], "ai_share": c["ai_share"],
                                      "why": squash("".join(c["why"])) or None, "text": squash("".join(c["text"]))})
                self.cur = None
            if t == tag:
                break

    def handle_data(self, data):
        if self.cur is None:
            return
        roles = [r for _, r in self.stack if r]
        if "chip" in roles:
            return
        if "why" in roles:
            self.cur["why"].append(data)
        elif "head" in roles:
            self.cur["head"].append(data)
        else:
            self.cur["text"].append(data)


def blocks_of(page: Path) -> list[dict]:
    s = page.read_text(encoding="utf-8")
    p = Blocks()
    p.feed(s)
    # the stand-up pages keep the reasons in a table at the end instead of inline; one row may cover several
    # paragraphs: <a href="#b26">26–30</a>，<a href="#b33">33–35</a> means b26..b30 and b33..b35 share the reason
    table = {}
    for row in re.findall(r"<tr>(.*?)</tr>", s, re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(cells) != 4 or 'href="#' not in cells[0]:
            continue
        reason = squash(H.unescape(re.sub(r"<[^>]+>", "", cells[3])))
        for prefix, a, b in re.findall(r'<a href="#([A-Za-z-]*?)\d+">(\d+)(?:[–-](\d+))?</a>', cells[0]):
            for k in range(int(a), int(b or a) + 1):
                table[f"{prefix}{k}"] = reason
    for r in p.rows:
        r["why"] = r["why"] or table.get(r["id"])
    return p.rows


def bigrams(t: str) -> set:
    t = re.sub(r"[\s，。、；：？！“”‘’（）【】《》—…,.;:?!\"'()\[\]<>·\-]", "", t)
    return {t[i:i + 2] for i in range(len(t) - 1)}


def src_class(note: str) -> str | None:
    if not note:
        return None
    if "合作者的原话" in note:
        return "human_verbatim"
    human = ["合作者的想法", "合作者的论点", "合作者的角度", "合作者的观察", "合作者批注", "合作者的批注", "合作者的要求",
             "合作者点的", "合作者要的", "合作者的题", "合作者转述", "合作者的亲身经历", "题目是合作者给的", "是合作者点的",
             "是合作者给的", "合作者删了", "合作者在"]
    if any(k in note for k in human):
        return "human_idea"
    if "本稿原创" in note:
        return "ai_original"
    return None


def main() -> None:
    att = BASE / "attribution"
    all_blocks = {}
    for name in ("standup_zh", "standup_en", "model_card"):
        rows = blocks_of(att / f"{name}.html")
        all_blocks[name] = rows
        (att / f"{name}_blocks.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                                                   encoding="utf-8", newline="\n")
        share = sum(r["ai_share"] for r in rows) / len(rows)
        print(f"{name}: {len(rows)} scored paragraphs, mean AI share {share:.3f} (co-author {100 * (1 - share):.1f}%)")

    page = (BASE / "ratings" / "index.html").read_text(encoding="utf-8")
    groups = json.loads(re.search(r"var GROUPS = (\[.*?\]);\n", page, re.S).group(1))
    db = {d["n"]: d for d in json.loads((BASE / "ratings" / "ratings_db.json").read_text(encoding="utf-8"))}
    zh = all_blocks["standup_zh"]
    for b in zh:
        b["_bg"] = bigrams(b["text"])

    rows = []
    for g in groups:
        deleted = g["title"].startswith("已删")
        for it in g["items"]:
            n = it["n"]
            d = db.get(n, {})
            rated = d.get("text") or it["t"]
            reason = None
            if deleted:
                m = re.search(r"——(.*?)】$", it["t"])
                reason = m.group(1) if m else None
            bg = bigrams(rated)
            best, score = None, 0.0
            if bg and not rated.startswith("【已删"):
                for b in zh:
                    ov = len(bg & b["_bg"]) / len(bg)
                    if ov > score:
                        best, score = b, ov
            ok = best is not None and score >= 0.35
            rows.append({
                "n": n,
                "section": d.get("group") if deleted and d.get("group") else g["title"],
                "deleted": deleted, "delete_reason": reason,
                "score": d.get("score") if isinstance(d.get("score"), (int, float)) else None,
                "note": d.get("note") or None, "rated_at": d.get("updatedAt"),
                "text": rated, "text_now": it["t"], "text_changed": bool(d.get("text")) and d["text"] != it["t"],
                "source_note": it.get("s"), "source_class": src_class(it.get("s", "")),
                "source_links": [u[1] for u in (it.get("u") or [])],
                "block": best["id"] if ok else None, "block_match": round(score, 2),
                "block_ai_share": best["ai_share"] if ok else None,
            })
    rows.sort(key=lambda r: r["n"])
    out = BASE / "ratings"
    (out / "punchlines.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8", newline="\n")
    cols = ["n", "section", "deleted", "delete_reason", "score", "note", "rated_at", "text", "text_now", "text_changed",
            "source_note", "source_class", "source_links", "block", "block_match", "block_ai_share"]
    with (out / "punchlines.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([" ".join(r[c]) if c == "source_links" else ("" if r[c] is None else r[c]) for c in cols])
    scored = [r for r in rows if r["score"] is not None]
    print(f"punchlines: {len(rows)} ({len(scored)} scored, {sum(r['deleted'] for r in rows)} deleted); "
          f"matched to a paragraph: {sum(r['block'] is not None for r in rows)}; with a source class: {sum(r['source_class'] is not None for r in rows)}")


if __name__ == "__main__":
    main()
