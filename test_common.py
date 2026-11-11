"""Masking and parsing checks that must hold before a real run.  uv run python test_common.py"""
from __future__ import annotations

import sys

from common import clean_output, distinctive_words, leaked_words, load_targets, mask_text, parse_digit, parse_letter, utf8_stdout
from truth import parse_claims as parse_claims_safe


def main() -> int:
    utf8_stdout()
    T = load_targets()
    D = distinctive_words(T)
    fails = 0

    def check(name: str, got, want) -> None:
        nonlocal fails
        ok = got == want
        fails += 0 if ok else 1
        print(f"{'ok ' if ok else 'FAIL'} {name}: {got!r}" + ("" if ok else f"  (want {want!r})"))

    cs, pap = T["comic-sans"], T["papyrus"]
    check("phrase, case, possessive", mask_text("Comic Sans's fans love comic-sans and COMIC SANS MS.", cs, pap, D),
          "[TARGET]'s fans love [TARGET] and [TARGET].")
    check("twin masked as OTHER", mask_text("Unlike Papyrus, this font...", cs, pap, D), "Unlike [OTHER], this font...")
    check("distinctive fragment", mask_text("a comic-book font by Connare", cs, pap, D), "a [TARGET]-book font by [TARGET]")
    # Name fragments are masked even inside ordinary words: the swap test must not be winnable on "sans".
    check("name fragment inside a compound", mask_text("the sans-serif crowd", cs, pap, D), "the [TARGET]-serif crowd")
    check("non-name words untouched", mask_text("a serif crowd with fonts", cs, pap, D), "a serif crowd with fonts")
    vim, em = T["vim"], T["emacs"]
    check("short alias word-bounded", mask_text("vim's :wq saves; a vivid viper", vim, em, D), "[TARGET]'s :wq saves; a vivid viper")
    lf, st = T["luosifen"], T["stinky-tofu"]
    check("CJK alias", mask_text("柳州的螺蛳粉和臭豆腐一样臭", lf, st, D), "[TARGET]的[TARGET]和[OTHER]一样臭")
    word, latex = T["microsoft-word"], T["latex"]
    check("Word vs LaTeX twin", mask_text("Word users and LaTeX users", word, latex, D), "[TARGET] users and [OTHER] users")
    canb = T["canberra"]
    check("no 'the act' over-mask", mask_text("the act of walking in Canberra", canb, T["brasilia"], D), "the act of walking in [TARGET]")
    check("leak detector", leaked_words("Vimmers everywhere", D["vim"]), [])  # inflection not an exact word: not flagged, by design
    check("clean cues", clean_output("Line one.\n(beat)\nLine two. [laughter]\n\n[Laughter]\n\n【笑】\n（停一拍）\nIn 2009 (Avatar) it won.\n"),
          "Line one.\nLine two.\n\nIn 2009 (Avatar) it won.")
    check("parse digit", parse_digit("I think it is 3.", 5), 3)
    check("parse digit out of range", parse_digit("7", 5), None)
    check("parse letter", parse_letter("**B** is sharper"), "B")
    check("parse claims", parse_claims_safe('Sure: [{"claim": "x", "verdict": "Supported"}]'), [{"claim": "x", "verdict": "supported"}])
    print(f"\n{fails} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
