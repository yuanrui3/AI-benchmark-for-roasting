# Roast Anything · roast-generation benchmark

Two linked goals:

1. **Roast Anything** ("Roasting Is All You Need"): a fine-tuned or distilled model, from Claude or an open-weight base, that roasts any *thing*.
2. **A roast-generation benchmark.** It is the evaluation Roast Anything needs anyway, so it comes first.

Status on 9 Nov 2026, 04:40: `targets.jsonl` is final (200 facts web-verified by six agents, 35 corrected, 0 removed, 1 narrowed). The whole preflight pipeline is built and passes an end-to-end run on the mock provider (`uv run python run_all.py --mock`). No API keys yet: the owner sets them up on the morning of 10 Nov (`.env` is prepared with instructions). Next: `check_keys.py` → `run_all.py --run pilot --smoke` → read the smoke outputs and tune prompts if needed → full run → owner and friends rate.

Run scripts with `uv run python <script>`. Windows consoles are cp1252: every script switches stdout to UTF-8, and ad-hoc Python should run with `PYTHONUTF8=1`.

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
- **Two language tracks, English and Chinese** (owner's decision, 9 Nov 2026). Every arm generates in both; `name_zh` and `category_zh` drive the Chinese prompts; fact sheets stay English. Pairs never cross languages, raters pick a track, and gates are read per track. This doubles generation and rating load.

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
   Done: 22 pairs, 44 targets, one JSON object per line with `id`, `name`, `name_zh`, `twin` (id, symmetric), `category` / `category_zh` (shared by the pair; what the generic control roasts), `aliases` (every string the masker hides, including Chinese names and creators' surnames), `facts` (3–5 checkable sentences, the truth-gate ground truth), `sources` (one URL per fact), `verify` (open doubts; only the Beanie Babies courtroom detail remains), `verified` (date). Facts about deaths and victims were left out on purpose. Keep facts free of double quotes (the masker and prompts assume it).
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

## Pipeline (built 9 Nov 2026, tested end to end on the mock provider)

```
uv run python check_keys.py                       # free: validates both keys
uv run python run_all.py --run pilot --smoke      # 4 targets x 1 sample on real models, a few dollars
uv run python run_all.py --run pilot --budget 40  # full run; re-running resumes, nothing is paid twice
uv run python run_all.py --mock                   # zero-cost pipeline test
```

- `llm.py`: the one logged client (anthropic | openrouter | mock). Disk cache per call key, cost ledger, `--budget` is a run-wide cap shared by all stages through `runs/<run>/ledger.jsonl`. Claude 5.5 models accept no temperature, so the sampling policy is "provider default" and is recorded in the manifest. No server-side fallbacks: a refusal is data.
- `config.py`: arms, models, judges, prompts in both languages. Arms: `plain-{opus,gpt,gemini,deepseek,qwen}`, `facts-opus` (plain prompt + fact sheet, isolates facts from method), `skill-opus` (SKILL.md + fact sheet), `control-bland`, `control-generic`. Arms and judges whose key is missing are skipped with a notice. **OpenRouter ids are unverified guesses** until `generate.py --list-models <query>` confirms them.
- `generate.py` → `runs/<run>/items.jsonl`, refusals and errors included; `manifest.json`.
- `specificity.py` → `specificity.jsonl`. Masks names, aliases and distinctive single words (twin → `[OTHER]`); two judges pick from five candidates; the residual leak check and lexical twin-contrast use no model.
- `truth.py` → `truth.jsonl`. Claims labelled supported / contradicted / absent; an item fails only on a contradiction, because plain arms never saw the sheet.
- `damage.py` → `damaged.jsonl`, `damage.jsonl`. Seven variants (softener and frontload mechanical, the rest written by Haiku), both orders, per-judge accuracy, position bias, self-preference, the explain rule.
- `build_pairs.py` → `rate/pairs.js`, `rate/pairs.json`, `rate/index.html`. Same-target, cross-arm pairs in one fixed order for every rater; 10% gold pairs from damaged variants; no arm names in the file.
- `rate.html`: the blind pairwise page. Keys ←/→/B/S, "crosses a line" flags, rater card at start, autosave, JSON export. Raters drop their exports into `runs/<run>/votes/`.
- `judge_pairs.py` → `judge_pairs.jsonl`: judges rate the human pairs in both orders, for judge–human agreement.
- `analyze.py` → `report.md`, `summary.json`: profile (softeners, stock templates, cross-arm collisions, words per sentence), both gates, judge validation, Bradley–Terry with bootstrap CIs, rater agreement, judge–human agreement against the human–human ceiling, vote projection, the gate table and verdict.

Known gaps before the first real run: model ids unverified; prompts and parsers untested on real outputs; expect a tuning pass after `--smoke`. `runs/mock*/` is git-ignored; real runs are tracked except `raw/`.

## Early observations (anecdotal, two samples)

- Sonnet 5.5 and Opus 5.5 independently wrote the same Comic Sans joke: a clown at a funeral insisting everyone lighten up. Measure cross-model collapse.
- Haiku 5.5 named the target in both tries despite being told not to. Masking must be automatic.

## Reference material

- `.claude/skills/roast-anything/`: the owner's roast skill, a dark, fact-anchored house style that defaults to Chinese. It encodes the owner's own taste, and the owner is also a rater, so blind the arms and give friends' votes real weight.
- `reference/talk-show/`: Chapter 20, "Late Show", of the owner's novel 阴燃 · The Slow Fire, in English and Chinese. It is a style reference for satirical delivery: callbacks, Radio-Yerevan answers, *Yes, Minister* dialogue. It was machine-drafted and author-selected, so it is not a human-written baseline.
- `docs/landscape.md`: prior work.
- `docs/rater-card.md`: each rater's stated taste.
