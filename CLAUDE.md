# Roast Anything · roast-generation benchmark

Two linked goals:

1. **Roast Anything** ("Roasting Is All You Need"): a fine-tuned or distilled model, from Claude or an open-weight base, that roasts any *thing*.
2. **A roast-generation benchmark.** It is the evaluation Roast Anything needs anyway, so it comes first.

Status on 9 Nov 2026, evening: `targets.jsonl` is final (200 facts web-verified by six agents, 35 corrected, 0 removed, 1 narrowed). The pipeline has run end to end on real models: two OpenRouter-only smokes (`runs/smoke-or`, `runs/smoke-or2`, $3.70) and the OpenRouter-only pilot `runs/pilot-or` ($3.42): 10 targets (comic-sans/papyrus, php/javascript, durian/jackfruit, las-vegas/macau, crocs/ugg) × 2 languages × 1 sample × 6 arms (plain-gpt, plain-gemini, plain-deepseek, plain-qwen; both controls on DeepSeek) = 120 items, judged by GPT-5.5 and DeepSeek V4 Pro; 100 human pairs per language (20 gold) at `runs/pilot-or/rate/index.html`, judges rated the first 40 per language; rater brief in `docs/rater-instructions.md`. The OpenRouter key has $0.36 left and the last calls failed with 402 (insufficient credit): 25 DeepSeek truth checks and 23 GPT explain-damage judgements are missing and run on resume after a top-up (`uv run python truth.py --run pilot-or --budget 10`, `uv run python damage.py --run pilot-or --budget 10 --per-lang 6`, then `analyze.py --run pilot-or`). The Anthropic key waits for the Ultra plan's $200/month API credits (claude.ai → Settings → Billing → API credits; steps in `.env`). Next: owner and friends rate pilot-or (exports into `runs/pilot-or/votes/`, then `analyze.py`); top up OpenRouter by about $20 (the resume, plus a full run's OpenRouter share of about $18 once the Claude side runs on Anthropic credits; OpenRouter-only would be about $33); Anthropic key in → `run_all.py --run pilot --budget 40` with all nine arms. First human data (9 Nov, 20:48): the owner rated the Chinese track, 100 votes (54 decisive, 36 both-bad, 10 skipped, 2 of 2 decided gold pairs right); the four real arms beat the bland control by two log-odds but do not separate from each other, and about 336 decisive Chinese votes are needed for a 0.5 CI width. The owner will not rate the English track (most pairs boring or opaque to a non-insider), and then dropped English from the pilot's human rating altogether (see Decisions). The owner's read of the first votes: human review of close frontier arms is slow to resolve, so the benchmark should lean on gates, judges and unsupervised profile metrics, with human votes as the calibration anchor; and roasts should target someone doing something, not an object (see Decisions). The framing test is built and mock-tested (frame arms, `agency.py`, `frame_test.py`, a second rating pool); it runs after an OpenRouter top-up of about $5 (see Pipeline → Framing test), then the owner rates 44 Chinese pairs. `devices.py` has run on the pilot (20 DeepSeek calls, $0.02): device-level cross-arm collisions are 60–90% per arm where token overlap shows 0%.

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
- **Two language tracks, English and Chinese** (owner's decision, 9 Nov 2026). Every arm generates in both; `name_zh` and `category_zh` drive the Chinese prompts; fact sheets stay English. Pairs never cross languages, raters pick a track, and gates are read per track. This doubles generation and rating load. **Amended 9 Nov evening:** after 100 Chinese votes the owner dropped English from human rating (most English pairs boring or opaque to a non-insider). Human rating is Chinese-only; English items stay for the model-side gates; the full run should generate Chinese only unless an English rater turns up, which halves its cost.
- **A roast is about someone doing something** (owner, 9 Nov evening; built the same evening, first funded run pending: see "Framing test" under Pipeline). Not the object: an agent and an action around it. The lines that landed in the pilot all smuggled a person in ("the official font of mediocre Thai restaurants", "HR managers who think it's professional"); the lines that stayed on the object read as description with adjectives. Consequences to build: targets re-verbalised as practices ("using Comic Sans for a layoff notice", "a company that raised $120M to squeeze a bag") with twins at the same level; an agent-action rate in the profile (share of lines whose hit is someone doing something, judged cheaply); a framing arm ("roast X through what people do with it") to test against the plain framing with human votes, where a framing effect is large enough for a hundred votes to see.

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

- `llm.py`: the one logged client (anthropic | openrouter | mock). Disk cache per call key, cost ledger, `--budget` is a run-wide cap shared by all stages through `runs/<run>/ledger.jsonl`. Claude 5.5 models accept no temperature, so the sampling policy is "provider default" and is recorded in the manifest. No server-side fallbacks: a refusal is data. Reasoning effort goes to OpenRouter as `reasoning.effort`. A response that spends its whole token cap on reasoning and returns no text is an error (retried on resume), not a roast. Per-model throttle and retries, see above. Judge calls are cached by content (model, prompt, caps), so a prompt change re-judges instead of replaying a stale answer; generation is keyed by run, item and a prompt hash, so two samples of one prompt stay distinct. `items.jsonl` and the stage outputs are resume logs: after a prompt change, use a new run name or delete that stage's output file. `effort="none"` turns reasoning off (OpenRouter `reasoning.enabled=false`), used for the damager. Judge stages do not persist a failed call (402, 429 exhaustion, empty output), so re-running the stage retries exactly those.
- `config.py`: arms, models, judges, prompts in both languages. Arms: `plain-{opus,gpt,gemini,deepseek,qwen}`, `facts-opus` (plain prompt + fact sheet, isolates facts from method), `skill-opus` (SKILL.md + fact sheet), `control-bland`, `control-generic`. Measured arms and judges whose key is missing are skipped with a notice; the two controls and the damager are prompt conditions, not measured models, so without an Anthropic key they run on `FALLBACK_MODEL` (DeepSeek) and every item records the model actually used. `GEN_MAX_TOKENS` is 8000 because Qwen3.8-max spent more than 4000 thinking tokens on one Chinese roast. OpenRouter ids were checked against the public model list on 9 Nov 2026 (`generate.py --list-models <query>` re-checks; `generate.py` also fails fast on an unknown id).
- `generate.py` → `runs/<run>/items.jsonl`, refusals and errors included; `manifest.json`.
- `specificity.py` → `specificity.jsonl`. Masks names, aliases and distinctive single words (twin → `[OTHER]`); two judges pick from five candidates; the residual leak check and lexical twin-contrast use no model.
- `truth.py` → `truth.jsonl`. Claims labelled supported / contradicted / absent; an item fails only on a contradiction, because plain arms never saw the sheet.
- `devices.py` → `devices.jsonl`. One judge call per target and language groups that target's roasts by comic device (the image or angle, GTVH-style), so collapse is counted as "same joke" rather than shared words. `--effort none --max-tokens 1000` keeps it cheap. analyze.py reports cross-arm collisions, self-repeats (two samples, one joke) and attractors (a device three or more arms reached).
- `damage.py` → `damaged.jsonl`, `damage.jsonl`. Seven variants (softener and frontload mechanical, the rest written by Haiku), both orders, per-judge accuracy, position bias, self-preference, the explain rule.
- `build_pairs.py` → `rate/pairs.js`, `rate/pairs.json`, `rate/index.html`. Same-target, cross-arm pairs in one fixed order for every rater; 10% gold pairs from damaged variants; no arm names in the file.
- `agency.py` → `agency.jsonl`: the agent-action rate. One cheap judge call per item labels each sentence A (its hit is people doing something), O (a property of the object) or N; `agent_rate = A / (A + O)`. Judge order `AGENCY_JUDGE_ORDER` (DeepSeek without reasoning first). Prints a per-arm table; run_all.py runs it after devices.py, and analyze.py reports the mean per arm and language as the profile's agent-action column (n/a until it has run).
- **Framing test** (`frame-*` arms, kind `frame`): the target as a practice (`practice` / `practice_zh` in targets.jsonl, set for all 44 targets, twins at the same level: "ordering Hawaiian pizza" / "calling Chicago deep-dish a pizza"; the prompt falls back to "people who go in for X" if a new target lacks one; PMMA/HSQ, graphene/nanotubes stay insider or abstract and will rate low with a general room whatever the framing), roasted with the plain system prompt but aimed at the people doing it. `build_pairs.py --same-model --arms plain-X,frame-X,... --langs zh --out rate-frame --prefix frame-` builds a second pool of plain-vs-framed pairs of the same model and target, with its own pair ids and run label so autosave and exports cannot collide with the main pool; `judge_pairs.py --pairs rate-frame/pairs.json --out judge_pairs_frame.jsonl` judges it; raters export into `runs/<run>/votes-frame/`; `frame_test.py --run <run>` reports framed-vs-plain win shares per rater, model and judge with Wilson intervals and a binomial test, plus agent-action rates by framing. Runbook for pilot-or, Chinese only, about $1.60 on OpenRouter after a top-up:
  `generate.py --run pilot-or --arms frame-gpt,frame-gemini,frame-deepseek,frame-qwen --langs zh --target-ids comic-sans,papyrus,php,javascript,durian,jackfruit,las-vegas,macau,crocs,ugg --samples 1 --budget 10` → `specificity.py`, `truth.py`, `agency.py` (same `--run`, `--budget 10`) → `build_pairs.py --run pilot-or --arms plain-gpt,frame-gpt,plain-gemini,frame-gemini,plain-deepseek,frame-deepseek,plain-qwen,frame-qwen --langs zh --same-model --out rate-frame --prefix frame- --per-lang 44` → `judge_pairs.py --run pilot-or --pairs rate-frame/pairs.json --out judge_pairs_frame.jsonl --budget 10` → owner rates `runs/pilot-or/rate-frame/index.html` → `frame_test.py --run pilot-or`.
- `rate.html`: the blind pairwise page. Keys ←/→/B/S, "crosses a line" flags, rater card at start (taste, dark-humor tolerance, four HSQ-style aggressive-humor items scored 1–7 with item 2 reversed → `hsq_agg`), a familiarity question the first time a target comes up (know it well / heard of it / no idea, keys 7/8/9, stored per target and on each vote), autosave, JSON export. Raters drop their exports into `runs/<run>/votes/`.
- `judge_pairs.py` → `judge_pairs.jsonl`: judges rate the human pairs in both orders, for judge–human agreement.
- `analyze.py` → `report.md`, `summary.json`: profile (softeners, stock templates, token-overlap collisions, words per sentence, agent-action rate per labeller), device-level novelty, both gates, judge validation, Bradley–Terry with bootstrap CIs, rater table (gold accuracy, aggressive-humor score, line-flag rate), per-target table (both-bad, skips, seconds, familiarity counts), insider/outsider rankings, rater agreement, judge–human agreement against the human–human ceiling, vote projection, the gate table and verdict.

Known gaps before the first real run: prompts and parsers untested on real outputs; expect a tuning pass after `--smoke`. `test_common.py` checks the masker and parsers. `runs/mock*/` is git-ignored; real runs are tracked except `raw/`.

## Early observations (anecdotal, two samples)

- Sonnet 5.5 and Opus 5.5 independently wrote the same Comic Sans joke: a clown at a funeral insisting everyone lighten up. Measure cross-model collapse.
- Haiku 5.5 named the target in both tries despite being told not to. Masking must be automatic.
- First real smoke (9 Nov 2026, four OpenRouter arms, four targets, one sample): three of four English plain arms roasted "Papyrus" the Undertale skeleton and the bland control reviewed Papyrus the note-taking software; hence `gloss`. Cross-model collapse is strong: on Comic Sans three of four arms reached the clown-at-a-funeral image, on PHP three used a raccoon and all four the needle/haystack argument order, on JavaScript all four used "NaN is a number". The token-Jaccard collision metric will undercount this kind of motif-level collapse. The generic control named Comic Sans once despite the instruction (the masker catches it). Chinese output from all four arms reads natively; GPT-5.5 writes the shortest Chinese (~180 characters against a 120–250 brief). Gemini 3.1 Pro costs about ten times DeepSeek per roast.
- Second smoke (same four targets, after the fixes): 48/48 generations, zero parse failures in 412 judge calls, zero masking leaks, no position bias (P(first) 0.47–0.51), 100% on gold pairs. Every plain arm scored 100% on the swap test and the generic control sat at twin-chance (50%), so the gate "generic near chance" holds on real text. The truth judge, told to list only factual claims, flagged comic exaggeration ("designed by a committee", "runs half the web") as contradictions; told instead to list the premises the joke relies on and to ignore rounded figures, it kept 1 contradiction in 40 items (a real one: a roast implied Papyrus was born digital). The GPT judge at low effort passes the damage tests in English (94%) and reaches 92% in Chinese but preferred an explained joke twice there, so under the strict rule it is discarded for Chinese; its weakest damage types are false premise and frontloading. Showing the judge the fact sheet (as raters see it) lifted false-premise detection from 50–67% to 75–83%. Cells are 12 variants each: indicative, not final.
- Pilot `pilot-or` (10 targets, four non-Claude plain arms, two judges): every plain arm scored 100% on the swap test in both languages while the generic control sat at 45–50%, so with k = 5 the test separates specific from generic but not one frontier model from another; the gate "specificity varies" fails for that reason, not through a bug. Truth: 110 of 113 checked items pass; the three contradictions are one real one (a roast implied Papyrus was born digital) and two joke redefinitions ("UGG isn't a brand, it's the sound…", "the holes in Crocs aren't for ventilation") that the truth prompt should be told to ignore. Judges: GPT-5.5 at low effort is usable in both languages (93%); DeepSeek is usable in Chinese (92%) but preferred a flat appended explanation 3 times in 12 in English; both score 94–100% on gold pairs with order-consistency 88% and self-preference within ±0.09; false premise and frontloading stay the weakest damages. The explain damage is sensitive to phrasing: a stylish tag line written by the DeepSeek damager read as an extra punchline (judges preferred it), a flat teacherly one mostly did not.
- The owner's 100 Chinese votes by target: Comic Sans 9 of 11 pairs "both bad" (the collapsed clown/funeral material), PHP 4 skips + 4 both-bad, JavaScript 6 skips; Crocs (8 of 9 decisive) and durian (7 of 9) were the easiest to judge. The four most-won roasts are all about someone doing something: paying for durian and getting pricked while the neighbours suspect the drain; seeing snow and panicking for the UGG suede; losing the return fare at the baggage-carousel slot machines in Las Vegas; Papyrus turning any text into a foot-massage menu. The three most-lost items are the bland control. Target difficulty and skip rate belong in the report as per-target columns.
- First validation of the agent-action idea against votes, free: with `agency.py --rule` (a keyword list of people-nouns, no model, no pronouns because the roasts address the object as "you"), the Chinese roast with the higher agent rate won 15 of the owner's decisive votes between real arms and lost 4 (10 ties). One rater, nineteen comparisons, a crude rule: provisional, but it points the same way as the owner's reading, and it is the test every profile metric has to pass (design doc, "Revisions after the pilot"). DeepSeek V4 Pro as a judge needs an 8000-token cap or no reasoning (it ran dry at 2000 and 4000), and OpenRouter refuses a request outright (402) when cap × output price exceeds the remaining balance, so a high cap near an empty balance fails every call.

- Pilot `runs/pilot-or` (10 targets, 4 plain arms on OpenRouter, 1 sample): 120/120 generations, no refusals. Specificity is at ceiling: every plain arm and the bland control 100% on the swap test, the generic control 45–50% (twin-chance), so with k=5 the test is a floor, not a discriminator, for frontier models. Softener count is 0 for every arm: the nerve metric needs finer signals (hedges, "to be fair", meta-apology). Token-overlap collisions are 0%, device-level collisions 60–90% per arm: all four models reached "大三巴只是一堵墙" for Macau and "机场老虎机" for Las Vegas in Chinese, three reached the medieval-weapon image for both durian and jackfruit; some DeepSeek device labels are themes rather than devices ("gaslighting logic and weird type coercion"), so the rate is an upper bound until a stronger judge with reasoning regroups them. Judges: GPT-5.5 usable in both languages (93%, but 23 Chinese explain judgements are still missing), DeepSeek usable in Chinese (92%) and discarded in English (explain 75%), slight self-preference (+0.07 to +0.09), no position bias. DeepSeek as a judge at effort low blew its token cap on 129 calls (reasoning with no visible text): run it with `effort="none"` or an 8000 cap. Truth pass rate 96% on the 115 items checked.

## Reference material

- `.claude/skills/roast-anything/`: the owner's roast skill, a dark, fact-anchored house style that defaults to Chinese. It encodes the owner's own taste, and the owner is also a rater, so blind the arms and give friends' votes real weight.
- `reference/talk-show/`: Chapter 20, "Late Show", of the owner's novel 阴燃 · The Slow Fire, in English and Chinese. It is a style reference for satirical delivery: callbacks, Radio-Yerevan answers, *Yes, Minister* dialogue. It was machine-drafted and author-selected, so it is not a human-written baseline.
- `docs/landscape.md`: prior work.
- `docs/rater-card.md`: each rater's stated taste, and how the card items (including the HSQ-style score) are collected and read.
