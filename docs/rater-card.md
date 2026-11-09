# Rater cards

Each rater states their taste before rating, so that any human ranking can be read as "funny to these people."

## Rater 1 (owner)

- Native Chinese speaker; also rates English.
- Likes Soviet political jokes and *Yes, Minister*; political satire generally.
- Explained jokes are dead jokes. Reasonable isn't funny. Prefers darker angles.
- Wrote the roast-anything skill, so they may recognize its style. Rate blind, and expect some home-team bias.

## Rater 2

- Languages:
- What they find funny (shows, comedians, forums):
- Dark humor tolerance (1–5):
- Aggressive-humor score (1–7, from the four card items):
- Anything off-limits:

## Rater 3

- Languages:
- What they find funny:
- Dark humor tolerance (1–5):
- Aggressive-humor score (1–7):
- Anything off-limits:

## How the card is collected

`rate.html` asks for all of this before the first pair and writes it into the export file, so `analyze.py` prints the cards next to the ranking. The four taste items are paraphrases in the style of the aggressive-humor subscale of the Humor Styles Questionnaire (Martin et al., 2003; a validated Chinese version exists, Chen & Martin 2007), scored 1–7 with the second item reversed and averaged. They are not the published items, so the score is comparable across our raters, not to published norms. `analyze.py` reports the score per rater and checks whether it tracks the rater's "crosses a line" flags and their agreement with the LLM judge.
