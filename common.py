"""Helpers shared by the evaluation stages: loading, masking, tokenizing, parsing judge answers."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MASK = "[TARGET]"
MASK_OTHER = "[OTHER]"

CJK = re.compile(r"[㐀-鿿]")
STOP_EN = set("""a an the and or but of to in on at for with by from as is are was were be been being it its this that
these those there here they them their he she his her we our you your i me my not no nor so than then too very can
could would should will just also into over under about after before between while which who whom whose what when
where why how all any both each few more most other some such only own same up down out off if because until""".split())


def utf8_stdout() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict) -> None:
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_targets(path: Path = ROOT / "targets.jsonl") -> dict[str, dict]:
    return {t["id"]: t for t in read_jsonl(path)}


# ---- masking ----------------------------------------------------------------

def all_names(target: dict) -> list[str]:
    names = [target["name"], target.get("name_zh") or ""] + list(target.get("aliases", []))
    names += [target["name"].split(" (")[0]]
    return sorted({n.strip() for n in names if n and n.strip()}, key=len, reverse=True)


def _pattern(alias: str) -> re.Pattern:
    if CJK.search(alias):
        return re.compile(re.escape(alias))
    parts = [re.escape(p) for p in re.split(r"[\s\-]+", alias) if p]
    body = r"[\s\-]+".join(parts)
    return re.compile(rf"(?<![A-Za-z0-9]){body}(?![A-Za-z0-9])", re.IGNORECASE)


def mask_text(text: str, target: dict, twin: dict | None, distinct: dict[str, set[str]] | None = None) -> str:
    """Replace the target's names with [TARGET] and the twin's with [OTHER].

    With `distinct` (from distinctive_words), single alias words that belong to no other target
    ("Comic", "Papyrus", "Vista") are masked as well, so a judge cannot win the swap test on a fragment.
    """
    out = text
    if twin is not None:
        for n in all_names(twin):
            out = _pattern(n).sub(MASK_OTHER, out)
        if distinct:
            for w in sorted(distinct.get(twin["id"], ()), key=len, reverse=True):
                out = _pattern(w).sub(MASK_OTHER, out)
    for n in all_names(target):
        out = _pattern(n).sub(MASK, out)
    if distinct:
        for w in sorted(distinct.get(target["id"], ()), key=len, reverse=True):
            out = _pattern(w).sub(MASK, out)
    return out


def distinctive_words(targets: dict[str, dict]) -> dict[str, set[str]]:
    """Per target: alias words (len>=4, Latin) that belong to no other target. Used to detect name leaks."""
    words_by_target: dict[str, set[str]] = {}
    for tid, t in targets.items():
        ws = set()
        for n in all_names(t):
            if CJK.search(n):
                continue
            for w in re.split(r"[^A-Za-z0-9]+", n):
                if len(w) >= 4:
                    ws.add(w.lower())
        words_by_target[tid] = ws
    counts = Counter(w for ws in words_by_target.values() for w in ws)
    return {tid: {w for w in ws if counts[w] == 1} for tid, ws in words_by_target.items()}


def leaked_words(masked_text: str, distinct: set[str]) -> list[str]:
    toks = set(w.lower() for w in re.findall(r"[A-Za-z0-9]{4,}", masked_text))
    return sorted(toks & distinct)


# ---- lexical features --------------------------------------------------------

def tokens(text: str) -> set[str]:
    """English words (>=3 chars, minus stopwords) plus CJK character bigrams."""
    out = set()
    for w in re.findall(r"[A-Za-z][A-Za-z0-9']{2,}", text):
        w = w.lower().strip("'")
        if w not in STOP_EN:
            out.add(w)
    for run in re.findall(r"[㐀-鿿]{2,}", text):
        out.update(run[i:i + 2] for i in range(len(run) - 1))
    return out


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---- judge answers ------------------------------------------------------------

def parse_digit(text: str, k: int) -> int | None:
    m = re.search(r"\b([1-9])\b", text or "")
    if m and 1 <= int(m.group(1)) <= k:
        return int(m.group(1))
    return None


def parse_letter(text: str, letters: str = "AB") -> str | None:
    m = re.search(rf"\b([{letters}])\b", (text or "").upper())
    return m.group(1) if m else None


_CUE_LINE = re.compile(r"^[ \t]*[\[【(（][^\]】)）\n]{1,14}[\]】)）][ \t]*\n?", re.M)
_CUE_INLINE = re.compile(r"[ \t]*[\[【][^\]】\n]{1,14}[\]】]")


def clean_output(text: str) -> str:
    """Remove stage directions a performable script carries: whole lines such as (beat), (pause), [laughter],
    （停一拍）, 【笑】, and inline [laughter] / 【笑】. They are not jokes, they announce one, and they identify
    the skill arm to every rater and judge. Parenthesised text inside a sentence (a year, an aside) is kept."""
    out = _CUE_LINE.sub("", text)
    out = _CUE_INLINE.sub("", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def count_words(text: str, lang: str) -> int:
    if lang == "zh":
        return len(CJK.findall(text))
    return len(re.findall(r"[A-Za-z0-9']+", text))
