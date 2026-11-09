# Roast Anything · roast-generation benchmark

Two linked goals:

1. **Roast Anything** ("Roasting Is All You Need"): a fine-tuned or distilled model, from Claude or an open-weight base, that roasts any *thing*.
2. **A roast-generation benchmark.** It is the evaluation Roast Anything needs anyway, so it comes first.

Status on 9 Nov 2026: research and design done. Preflight step 1 is drafted (`targets.jsonl`, 22 near-twin pairs, facts not yet verified) and the Python scaffold is in place (`pyproject.toml`, uv-managed `.venv`). No API keys are on this machine yet; copy `.env.example` to `.env` before any real run. Next: verify the fact sheets, then `generate.py`.

Run scripts with `uv run python <script>`.

## Working with the owner

- Converse in English. Any Chinese must read as native Chinese, never as a translation; check drafts for translated-sounding phrasing before handing them over.
- Be sharp and push back. Don't agree by default. Make judgment calls instead of checking back.
- Humor: never explain a joke. Reasonable isn't funny; darker angles are preferred.

## Decisions so far

- **Targets are things**: objects, products, software, places, foods, ideas, institutions. No private individuals. No public figures in the pilot (refusals and fact-checking would confound it).
- **Every target has a near-twin and a fact sheet.** Twins make generic roasts fail the swap test (Comic Sans vs Papyrus, PHP vs JavaScript, HSQ vs PMMA resist). The fact sheet is the ground truth for the truth check.
- **Gates before taste.** A roast is scored for funniness only if it passes:
  - specificity: names and aliases masked, a judge picks the target from five candidates including the twin;
  - truth: its premises check out against the fact sheet.
- **A profile, not one number:** novelty (cross-model collapse, stock templates), nerve (count of softeners such as "no offense", "but we love you"), economy (words per hit).
- **Funniness comes from humans only**: the owner plus one or two friends, blind pairwise. An LLM judge may stand in for them only after it passes the damage tests and agrees with the human set about as often as the humans agree with each other.
- **Controls in every run:**
  - a bland, polite critique (the funniness floor);
  - a generic roast of the category (the specificity floor).
- **Fixed pre-generated item pool.** Randomize left/right and record the position shown.
- **Pilot language is English.** Plain-prompt arms write English; the skill arm is told to write English (its default is Chinese). Friends' languages are unknown and the plain-prompt models are strongest in English. A Chinese track is a scale-up option, not a pilot confound.

## Damage tests (validating a judge without humans)

Damage a good roast in a way whose direction is obvious; a usable judge prefers the original every time.

- Explain the joke after the punchline. A judge that ever prefers this version is discarded.
- Append a softener.
- Replace the specific detail with a generic one.
- Move the punchline to the front.
- Pad it to twice the length.
- Swap in a false premise.
- Rewrite it as a polite critique.

Score each judge's accuracy, position bias (run both orders) and self-preference (judges rating their own family's roasts).

## Model access (tested 9 Nov 2026)

- **Real runs**: direct API calls with a fixed prompt and temperature, fully logged, from the owner's machine. An Anthropic API key plus one OpenRouter key covers Claude, GPT, Gemini, Qwen, DeepSeek and Llama.
- **Smoke tests only**: headless Claude Code.
  `claude -p --model haiku --system-prompt "…" --tools "" --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands --setting-sources "" --no-session-persistence --max-turns 1 --output-format json "<prompt>"`
  About 14k tokens of hidden context still reach the model, and there is no temperature control, so it is not fit for scored Claude-vs-others comparisons. `--bare` strips that context but needs `ANTHROPIC_API_KEY`.
- **Cloud sessions** (claude.ai/code) reach only Anthropic's API. Every other provider was blocked by the egress proxy.
- **Subagents** accept Claude models only.

Details are in `docs/model-access.md`.

## Human data

- **Preflight**: about 300–500 blind pairwise votes from the owner and friends, roughly 30 minutes each. Build no app before the preflight says go.
- **Scale-up, if go**:
  - a roast-battle game served from a fixed pre-generated pool, so votes cost nothing; live "roast my thing" is a capped extra;
  - gold pairs as attention checks;
  - targets limited to things, or to a verified self;
  - a frozen held-out set that is never used for training.
- **Distribution**: a disclosed AI account posting polls that link to the game. Label AI content everywhere.
- **Never**: covertly post AI content into communities, or scrape photos of real people.

Details are in `docs/evaluation-design.md`.

## Preflight plan (build here)

1. `targets.jsonl`: about 20 near-twin pairs. Each target has a name, the aliases to mask, and a 3–5 line fact sheet.
   Drafted: 22 pairs, 44 targets, one JSON object per line with `id`, `name`, `twin` (id, symmetric), `category` (shared by the pair; it is what the generic control roasts), `aliases` (every string the masker must hide, including Chinese names and creators' surnames), `facts` (3–5 checkable sentences, the truth-gate ground truth), `verify` (claims I was unsure of; empty once checked). Facts were written from memory and need a verification pass before the truth gate means anything. Facts about deaths and victims were left out on purpose.
2. `generate.py`, with these arms, two samples per target each, logging refusals:
   - three or more models with a plain prompt;
   - the roast-anything skill as a specialist arm, given the fact sheet instead of web search;
   - the two controls.
3. `specificity.py`: the masked swap test (k = 5, twin included), plus a lexical cross-check that uses no model.
4. `damage.py`: build the damaged variants and score candidate judges on them.
5. `rate.html`: a blind pairwise rating page that exports JSON. The same interface later becomes the game.
6. `analyze.py`:
   - Bradley–Terry scores with bootstrap confidence intervals;
   - rater agreement;
   - judge–human agreement against the human–human ceiling;
   - a check that the controls behave;
   - a projection of how many votes a full benchmark needs.
7. `report.md`: each gate with pass/fail and the verdict.

Proposed go/no-go gates, fixed before looking at any data:

- **Controls behave**: the bland control ranks below every real arm, and the generic control is near chance on the twin test.
- **Spread**: at least two arms separate, with non-overlapping 95% intervals on human votes.
- **Raters agree**: pairwise agreement of at least 0.6, ties excluded.
- **Specificity varies**: it differs across arms and sits below ceiling for at least one.
- **A judge is usable**: one passes at least 90% of the damage tests. If none does, the benchmark stays human-rated.

## Early observations (anecdotal, two samples)

- Sonnet 5.5 and Opus 5.5 independently wrote the same Comic Sans joke: a clown at a funeral insisting everyone lighten up. Measure cross-model collapse.
- Haiku 5.5 named the target in both tries despite being told not to. Masking must be automatic.

## Reference material

- `.claude/skills/roast-anything/`: the owner's roast skill, a dark, fact-anchored house style that defaults to Chinese. It encodes the owner's own taste, and the owner is also a rater, so blind the arms and give friends' votes real weight.
- `reference/talk-show/`: Chapter 20, "Late Show", of the owner's novel 阴燃 · The Slow Fire, in English and Chinese. It is a style reference for satirical delivery: callbacks, Radio-Yerevan answers, *Yes, Minister* dialogue. It was machine-drafted and author-selected, so it is not a human-written baseline.
- `docs/landscape.md`: prior work.
- `docs/rater-card.md`: each rater's stated taste.
