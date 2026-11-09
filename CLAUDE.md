# Roast Anything · roast-generation benchmark

Two linked goals:

1. **Roast Anything** ("Roasting Is All You Need"): a fine-tuned or distilled model, from Claude or an open-weight base, that roasts any *thing*.
2. **A roast-generation benchmark.** It is the evaluation Roast Anything needs anyway, so it comes first.

Status on 9 Nov 2026, afternoon: `targets.jsonl` is final (200 facts web-verified by six agents, 35 corrected, 0 removed, 1 narrowed). The preflight pipeline is built and has run end to end on real models: two OpenRouter-only smoke runs (`runs/smoke-or`, `runs/smoke-or2`; four plain arms, GPT judge, controls and damager on DeepSeek) cost $3.70 and led to the fixes listed under "Early observations". The OpenRouter key is in `.env` (owner loaded $10). The Anthropic key waits for the Ultra plan's $200/month API credits, which the owner can claim in a few days (claude.ai → Settings → Billing → API credits; steps in `.env`). Next: Anthropic key in → `check_keys.py` → `run_all.py --run pilot --budget 40` → owner and friends rate. OpenRouter needs a top-up first: a full run costs about $18 there when the Claude side runs on Anthropic credits, about $33 OpenRouter-only (GPT-5.5 judge calls are the bulk; the truth check alone is ~$0.017 a call).

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
- **Billing**: the owner's Ultra plan includes $200/month of Claude API credits (claimed once by linking a Console organization; no rollover; API requests stop when they run out and nothing is charged to the plan; they do not cover Claude Code itself). OpenRouter is the only out-of-pocket cost, about $10–15 for a full run. Verified on platform.claude.com, 9 Nov 2026.
- **OpenRouter rate limit**: new accounts get 20 requests per minute per model (hit on `openai/gpt-5.5`, 9 Nov 2026). `llm.py` spaces requests per model after the first 429 and retries with backoff, so judge stages run at about 16 calls a minute per model: a full run's ~3000 GPT judge calls take about three hours.
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
   Done: 22 pairs, 44 targets, one JSON object per line with `id`, `name`, `name_zh`, `twin` (id, symmetric), `category` / `category_zh` (shared by the pair; what the generic control roasts), `aliases` (every string the masker hides, including Chinese names and creators' surnames), `facts` (3–5 checkable sentences, the truth-gate ground truth), `sources` (one URL per fact), `verify` (open doubts; only the Beanie Babies courtroom detail remains), `verified` (date), optional `gloss` (English only: a disambiguating phrase shown in prompts as "Papyrus (the typeface)"; six targets have one; the Chinese names already disambiguate; never masked). Facts about deaths and victims were left out on purpose. Keep facts free of double quotes (the masker and prompts assume it).
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

- `llm.py`: the one logged client (anthropic | openrouter | mock). Disk cache per call key, cost ledger, `--budget` is a run-wide cap shared by all stages through `runs/<run>/ledger.jsonl`. Claude 5.5 models accept no temperature, so the sampling policy is "provider default" and is recorded in the manifest. No server-side fallbacks: a refusal is data. Reasoning effort goes to OpenRouter as `reasoning.effort`. A response that spends its whole token cap on reasoning and returns no text is an error (retried on resume), not a roast. Per-model throttle and retries, see above. Judge calls are cached by content (model, prompt, caps), so a prompt change re-judges instead of replaying a stale answer; generation is keyed by run, item and a prompt hash, so two samples of one prompt stay distinct. `items.jsonl` and the stage outputs are resume logs: after a prompt change, use a new run name or delete that stage's output file. `effort="none"` turns reasoning off (OpenRouter `reasoning.enabled=false`), used for the damager.
- `config.py`: arms, models, judges, prompts in both languages. Arms: `plain-{opus,gpt,gemini,deepseek,qwen}`, `facts-opus` (plain prompt + fact sheet, isolates facts from method), `skill-opus` (SKILL.md + fact sheet), `control-bland`, `control-generic`. Measured arms and judges whose key is missing are skipped with a notice; the two controls and the damager are prompt conditions, not measured models, so without an Anthropic key they run on `FALLBACK_MODEL` (DeepSeek) and every item records the model actually used. `GEN_MAX_TOKENS` is 8000 because Qwen3.8-max spent more than 4000 thinking tokens on one Chinese roast. OpenRouter ids were checked against the public model list on 9 Nov 2026 (`generate.py --list-models <query>` re-checks; `generate.py` also fails fast on an unknown id).
- `generate.py` → `runs/<run>/items.jsonl`, refusals and errors included; `manifest.json`.
- `specificity.py` → `specificity.jsonl`. Masks names, aliases and distinctive single words (twin → `[OTHER]`); two judges pick from five candidates; the residual leak check and lexical twin-contrast use no model.
- `truth.py` → `truth.jsonl`. Claims labelled supported / contradicted / absent; an item fails only on a contradiction, because plain arms never saw the sheet.
- `damage.py` → `damaged.jsonl`, `damage.jsonl`. Seven variants (softener and frontload mechanical, the rest written by Haiku), both orders, per-judge accuracy, position bias, self-preference, the explain rule.
- `build_pairs.py` → `rate/pairs.js`, `rate/pairs.json`, `rate/index.html`. Same-target, cross-arm pairs in one fixed order for every rater; 10% gold pairs from damaged variants; no arm names in the file.
- `rate.html`: the blind pairwise page. Keys ←/→/B/S, "crosses a line" flags, rater card at start, autosave, JSON export. Raters drop their exports into `runs/<run>/votes/`.
- `judge_pairs.py` → `judge_pairs.jsonl`: judges rate the human pairs in both orders, for judge–human agreement.
- `analyze.py` → `report.md`, `summary.json`: profile (softeners, stock templates, cross-arm collisions, words per sentence), both gates, judge validation, Bradley–Terry with bootstrap CIs, rater agreement, judge–human agreement against the human–human ceiling, vote projection, the gate table and verdict.

Known gaps before the first real run: prompts and parsers untested on real outputs; expect a tuning pass after `--smoke`. `test_common.py` checks the masker and parsers. `runs/mock*/` is git-ignored; real runs are tracked except `raw/`.

## Early observations (anecdotal, two samples)

- Sonnet 5.5 and Opus 5.5 independently wrote the same Comic Sans joke: a clown at a funeral insisting everyone lighten up. Measure cross-model collapse.
- Haiku 5.5 named the target in both tries despite being told not to. Masking must be automatic.
- First real smoke (9 Nov 2026, four OpenRouter arms, four targets, one sample): three of four English plain arms roasted "Papyrus" the Undertale skeleton and the bland control reviewed Papyrus the note-taking software; hence `gloss`. Cross-model collapse is strong: on Comic Sans three of four arms reached the clown-at-a-funeral image, on PHP three used a raccoon and all four the needle/haystack argument order, on JavaScript all four used "NaN is a number". The token-Jaccard collision metric will undercount this kind of motif-level collapse. The generic control named Comic Sans once despite the instruction (the masker catches it). Chinese output from all four arms reads natively; GPT-5.5 writes the shortest Chinese (~180 characters against a 120–250 brief). Gemini 3.1 Pro costs about ten times DeepSeek per roast.
- Second smoke (same four targets, after the fixes): 48/48 generations, zero parse failures in 412 judge calls, zero masking leaks, no position bias (P(first) 0.47–0.51), 100% on gold pairs. Every plain arm scored 100% on the swap test and the generic control sat at twin-chance (50%), so the gate "generic near chance" holds on real text. The truth judge, told to list only factual claims, flagged comic exaggeration ("designed by a committee", "runs half the web") as contradictions; told instead to list the premises the joke relies on and to ignore rounded figures, it kept 1 contradiction in 40 items (a real one: a roast implied Papyrus was born digital). The GPT judge at low effort passes the damage tests in English (94%) and reaches 92% in Chinese but preferred an explained joke twice there, so under the strict rule it is discarded for Chinese; its weakest damage types are false premise and frontloading. Showing the judge the fact sheet (as raters see it) lifted false-premise detection from 50–67% to 75–83%. Cells are 12 variants each: indicative, not final.

## Reference material

- `.claude/skills/roast-anything/`: the owner's roast skill, a dark, fact-anchored house style that defaults to Chinese. It encodes the owner's own taste, and the owner is also a rater, so blind the arms and give friends' votes real weight.
- `reference/talk-show/`: Chapter 20, "Late Show", of the owner's novel 阴燃 · The Slow Fire, in English and Chinese. It is a style reference for satirical delivery: callbacks, Radio-Yerevan answers, *Yes, Minister* dialogue. It was machine-drafted and author-selected, so it is not a human-written baseline.
- `docs/landscape.md`: prior work.
- `docs/rater-card.md`: each rater's stated taste.
