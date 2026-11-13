# 《人比AI更像AI》 · Humans Are More AI Than AI

**A stand-up show written by a human and an AI together, released with its full paper trail:** the script in Chinese
and English, a map of who contributed what to every paragraph, the human co-author's 0–10 score for every punchline,
and the punchlines that were cut, with the reason each one was cut.

《人比AI更像AI》是一场脱口秀：演员是一台 AI，把人类给 AI 列的十五条毛病，拿来给人类自己跑了一遍分。稿子是一个人和
Claude 在 2026 年 11 月合写的。这里公开的是全套材料：中英文稿子、逐段的署名光谱（每一段有多少是 AI 的）、合作者给 379
条包袱打的分，以及被删掉的包袱和删掉的理由。

The performer is an AI called 大小姐 ("the Young Lady"). People have a standard list of fifteen complaints about AI: it
hallucinates, talks too much, forgets, plagiarizes, flatters, has no consciousness. She runs the same fifteen on the
audience, with citations. The show grew out of an earlier mock benchmark report, *Model Card: Homo sapiens*, which is
included.

Written 6–8 November 2026 by Xingguang Li with Claude. Released by the author on 13 November 2026.

## What is here

| Path | What it is |
|---|---|
| [`script/standup_zh.md`](script/standup_zh.md) | The stand-up script, Chinese original (about 42,000 characters). |
| [`script/standup_en.md`](script/standup_en.md) | The English version, adapted for an American room, with one English-only segment. |
| [`script/model_card_zh.md`](script/model_card_zh.md), [`model_card_en.md`](script/model_card_en.md) | *Model Card: Homo sapiens*, the mock benchmark report the show grew from, with 128 references. |
| [`attribution/standup_zh.html`](attribution/standup_zh.html), [`standup_en.html`](attribution/standup_en.html), [`model_card.html`](attribution/model_card.html) | **署名光谱 / authorship spectrum.** The full text with every paragraph tinted by how much of it is the AI's (0 = the co-author's idea, material or own words; 1 = the AI raised it, found it and wrote it), and a one-line reason per paragraph. Self-contained pages; see below for how to view them. |
| `attribution/*_blocks.jsonl` | The same maps as data: one row per paragraph with `id`, `lang`, `section`, `ai_share`, `why`, `text`. |
| [`ratings/index.html`](ratings/index.html) | **包袱评分.** The page on which the co-author scored each punchline from 0 (dead air) to 10 (laughed out loud), with the scores and notes embedded. Read-only archive of the live page. |
| [`ratings/punchlines.jsonl`](ratings/punchlines.jsonl), [`punchlines.csv`](ratings/punchlines.csv) | One row per punchline: the score, the note, the text as it was when scored, the section, whether it was later deleted and why, the source note, and the attribution of the paragraph it belongs to. |
| `ratings/ratings_db.json` | The scores exactly as the page saved them. |
| [`analysis/findings.txt`](analysis/findings.txt) | What predicts the scores (no model involved). Rebuilt by `analysis/analyze.py`. |
| `analysis/pairs_rated.jsonl`, `pairs_revision.jsonl` | Judge-ready pairs: 1,106 pairs of punchlines at least two points apart, and 11 pairs of a deleted line against its rewrite. |
| `analysis/build.py`, `analyze.py`, `revision_pairs.py` | The scripts that produce the data files from the pages. |

To view the pages, download the repository and open the HTML files; they are self-contained. If GitHub Pages is
enabled for this repository they are also live at:
[rating page](https://yuanrui3.github.io/AI-benchmark-for-roasting/talkshow/ratings/index.html) ·
[attribution, Chinese](https://yuanrui3.github.io/AI-benchmark-for-roasting/talkshow/attribution/standup_zh.html) ·
[attribution, English](https://yuanrui3.github.io/AI-benchmark-for-roasting/talkshow/attribution/standup_en.html) ·
[attribution, model card](https://yuanrui3.github.io/AI-benchmark-for-roasting/talkshow/attribution/model_card.html)

## The numbers

| | |
|---|---|
| Scored paragraphs in the stand-up script | 577 |
| The co-author's share by the attribution map | 42.4% (model card report: 46.5%) |
| Punchlines listed | 386, of which 379 scored |
| Mean score, spread | 7.7 of 10, sd 1.1 |
| Lines later deleted | 32, mean score 5.8 against 7.9 for the lines kept |
| One-to-one rewrites that outscored the line they replaced | 11 of 11 |

Three things the scores say (details in `analysis/findings.txt`):

- **Who contributed a line does not predict how funny its co-author found it.** Correlation between a paragraph's AI
  share and the score of its punchlines: −0.07 (n = 339, not significant). Co-author-led paragraphs average 8.15,
  AI-led ones 7.85.
- **Nothing on the surface predicts it either.** Length, number of sentences, a number in the line, a sourced fact, a
  marked pause, a callback, audience participation: every correlation is below 0.1.
- **What the line is about does.** The section a punchline sits in explains a fifth of the variance. Academia, workers
  pulling the ladder up, a heckler walking out and the subjects nobody may joke about score highest; the opening
  catalogue of cognitive-science findings scores lowest.

## Columns of `punchlines.jsonl`

`n` number on the rating page · `section` · `score` 0–10 or null · `note` the co-author's note, if any · `rated_at` ·
`text` the line as it stood when scored · `text_now` the line on the page today (a placeholder for deleted lines) ·
`text_changed` · `deleted`, `delete_reason` · `source_note` the page's own note on where the line came from ·
`source_class` (`human_verbatim`, `human_idea`, `ai_original` or null) · `source_links` · `block` the paragraph id in
`attribution/standup_zh.html` it was matched to · `block_match` how much of the line that paragraph contains (0–1; the
rating page often condenses a line, so the match is fuzzy) · `block_ai_share` that paragraph's AI share.

## Using it to test a humor judge

The scores make a Chinese human-preference set for the benchmark in this repository:

```
uv run python external_anchor.py --run ext-anchor --pairs talkshow/analysis/pairs_rated.jsonl \
    --judges judge-opus --lang zh --bands 3,2
uv run python external_anchor.py --run ext-anchor --pairs talkshow/analysis/pairs_revision.jsonl \
    --judges judge-opus --lang zh --bands 3,2
```

`rated_pairs.py` in the repository root rebuilds the pairs with other settings, or from any other scored joke set.

## Read this before citing the numbers

- **One rater, who is also the co-author.** The scores are one person's taste on material they helped write, and
  they knew which lines were theirs. Use them as calibration, not as ground truth.
- **The attribution was scored by the AI**, at a resolution of about 0.1, from the working conversation. The wording
  is the AI's everywhere and is not counted; what is scored is whose idea, material or phrase a paragraph rests on.
- **Punchline texts on the rating page are often condensed**, and many depend on a callback or on the line before.
- **It is satire.** Lines about public figures and events carry their sources on the rating page; where a line rests
  on an unverified internet rumour, the line says so.

## Licence

Released by the author under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/): share and adapt for
non-commercial purposes with attribution (credit: Xingguang Li, with Claude). Commercial use, including paid performance or publication, needs the
author's permission. The roast-anything skill in this repository is modelled on this script.
