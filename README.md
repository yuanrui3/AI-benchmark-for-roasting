# Roast Anything: a roast-generation benchmark

Can a model write a roast that is funny, true, and about *this* thing? This repository is the preflight for a
benchmark that scores roasts in English and Chinese, with gates before taste and a judge validated without humans.
Working notes, decisions and every result are in `CLAUDE.md`; the design is in `docs/evaluation-design.md`.

## What is measured

A roast of a target (a font, a programming language, a city, a shoe, a practice such as "going to Macau to win it
all back") is scored only after it passes two gates:

- **Specificity**: with names masked, a judge must pick the target from five candidates including a near-twin
  (Comic Sans vs Papyrus, PHP vs JavaScript). Frontier models are at ceiling here, so `depth.py` grades instead how
  much of the roast would not land on the twin, sentence by sentence.
- **Truth**: every premise the joke relies on is checked against a web-verified fact sheet; an item fails on a
  contradiction, not on a fact the sheet lacks. Comic exaggeration, puns and redefinitions do not count.

Then taste: blind pairwise comparison of two roasts of the same target. A **judge** is admitted only if it passes
seven damage tests (explained joke, padding, politeness, softeners, generic rewrite, front-loaded punchline, false
premise) at 90% or better and never prefers an explained joke; it is also checked for position bias in both orders.
Unsupervised profile metrics (agent-action rate, comic-device collisions, length and rhythm) are reported next to the
judge's ranking and tested against it with `metric_check.py`.

## Results so far (11 Nov 2026, Claude side; other families wait for OpenRouter credit)

- **Opus 5.5 is a usable judge** in both languages (damage tests 99–100% on Claude roasts, 94–99% on other
  models' roasts, no position bias). Sonnet 5.5 is not: it prefers explained jokes and takes the first-shown roast
  up to three times in four on close pairs.
- **The judge has a public human anchor**: Opus picks the crowd-preferred New Yorker caption 77% of the time (GPT-4
  in the literature 67%; a judge fine-tuned on the crowd data 82–85%) and the funnier edited headline 67% (71% at a
  clear crowd margin). It also agreed 77% with the one human rater's 47 decisive votes, which is read as
  calibration, not as a target.
- **The benchmark orders models**: on the same prompt Opus beats Sonnet (74–85%) and Sonnet beats Haiku (74–94%),
  intervals not touching.
- **Among Opus prompts** the house-style skill is best in both languages; feeding the fact sheet is neutral in
  English and a handicap in Chinese; aiming the roast at the people doing the thing costs in English and is neutral
  in Chinese.
- **Facts steer models into the same joke**: fact-fed arms share a comic device with another arm on 73–86% of items,
  and three Claude models reach the same device on oat milk, NFTs, nuclear fusion and Emacs.
- **The truth gate catches invention**: Sonnet's plain English roasts fail it most (0.76–0.78 pass), below Haiku and
  Opus; the judge prefers the truthful roast in 85–90% of decided pairs where truth differs.
- **Specificity depth** (`depth.py`, the share of a roast's target-bearing sentences that would not land on the
  twin) spreads the arms the swap test cannot: generic control 0.04–0.07, bland 0.31, Haiku 0.36–0.55, Sonnet
  0.40–0.64, plain Opus 0.67, house style 0.77, fact-fed 0.81; the deeper roast wins 64–79% of decided pairs.
- **The framing has to match the target**: on sixteen practice-first targets (砍一刀, 996, 相亲角, 考研, 盲盒, 老头乐,
  预制菜, 瑞幸 and their twins) the roast aimed at the people doing the thing beats the plain roast in both
  languages (70% en, 57% zh), the reverse of the 44 things; plain Opus also invents more on these topics and
  the truth gate drops it to 62% in English.
- **Free metrics that track the judge** (`metric_check.py`): truth, more sentences, fewer words per sentence and
  fact density predict the judge's pick; novelty of comic device does not (the shared obvious joke wins).

Leaderboard (judge opinion, Bradley–Terry over every judged pool, 95% bootstrap intervals; `runs/pilot/leaderboard.md`):

| arm | en score | zh score |
|---|---:|---:|
| skill-opus | +2.03 [+1.86, +2.27] | +2.16 [+2.01, +2.33] |
| facts-opus | +1.91 [+1.71, +2.13] | +1.31 [+1.17, +1.46] |
| plain-opus | +1.53 [+1.39, +1.73] | +1.57 [+1.45, +1.71] |
| frame-opus | +0.95 [+0.80, +1.16] | +1.58 [+1.47, +1.72] |
| frame-sonnet | +0.37 [+0.16, +0.68] | +0.80 [+0.55, +1.00] |
| plain-sonnet | -0.18 [-0.52, +0.21] | +0.49 [+0.21, +0.75] |
| plain-haiku | -1.19 [-1.55, -0.79] | -2.34 [-2.91, -1.93] |
| frame-haiku | -2.17 [-2.58, -1.81] | -1.33 [-1.74, -0.97] |
| control-bland | -3.24 [-4.37, -2.38] | -4.25 [-4.44, -3.99] |

A one-point gap is about a 73% win rate. These are a validated judge's preferences, not human votes.

## Setup

Python 3.12 or newer and [uv](https://docs.astral.sh/uv/). Then:

```
uv sync                          # the pipeline's dependencies (add --extra anchor for external_pairs.py)
cp .env.example .env             # fill in ANTHROPIC_API_KEY and/or OPENROUTER_API_KEY; .env is git-ignored
uv run python check_keys.py      # free: confirms what each key can reach
uv run python test_common.py     # unit checks, no network
uv run python run_all.py --mock  # the whole pipeline on a fake provider, zero cost, about a minute
```

Either key alone works: arms and judges whose provider is missing are skipped and reported. On Windows set
`PYTHONUTF8=1` (or run `python -X utf8`) so Chinese output prints. Every real call is cached under
`runs/<run>/raw/` and logged to `runs/<run>/ledger.jsonl`, so interrupted runs resume and nothing is paid twice;
`--budget` is a hard cap per run.

## Running it

```
uv run python check_keys.py                      # validates the keys in .env (see .env.example)
uv run python run_all.py --run pilot --smoke     # a few dollars on real models
uv run python run_all.py --run pilot --budget 40 # full run; re-running resumes, nothing is paid twice
uv run python run_all.py --mock                  # zero-cost pipeline test
```

Stages: `generate.py` → `specificity.py` → `truth.py` → `devices.py` → `agency.py` → `depth.py` → `damage.py` →
`build_pairs.py` → `judge_pairs.py` → `analyze.py` (report) → `leaderboard.py`, `pool_rank.py`, `metric_check.py`,
`frame_test.py`. `external_pairs.py` and `external_anchor.py` validate a judge against public crowd humor
preferences. Every call is cached on disk and logged to a cost ledger; `--budget` is a run-wide cap.

## Layout

- `config.py`: models, arms (prompt × model), judges, prompts in both languages, lengths, effort. Add a model or an arm here.
- `targets.jsonl`: one target per line: names in both languages, aliases, a near-twin, a practice form, four to five verified facts with sources. Add targets here; the pipeline picks them up by id.
- `llm.py`: the one logged client (Anthropic, OpenRouter, mock) with the disk cache, cost ledger and retries.
- Stage scripts (each reads `runs/<run>/items.jsonl`, writes one `.jsonl`, resumes): `generate`, `specificity`, `truth`, `devices`, `agency`, `depth`, `damage`, `build_pairs`, `judge_pairs`.
- Readers: `analyze.py` (report and gates), `leaderboard.py`, `pool_rank.py`, `metric_check.py`, `frame_test.py`.
- Judge validation against public crowd data: `external_pairs.py`, `external_anchor.py`.
- `rate.html`: the blind human rating page (no server needed; open a pool's `index.html`).
- `runs/pilot/`: the full Claude-side run, 60 targets, 2,080 roasts, every judge file, `report.md`, `leaderboard.md`.
- `docs/`: design notes, rater instructions, model-access notes. `CLAUDE.md`: the project's working log and decisions.

## Adding things

- **A model**: add it to `MODELS` in `config.py` (provider and id), then an arm `{"name": ..., "kind": "plain", "model": ...}`. Run `generate.py --run <run> --arms <name>`, the gate stages, then `judge_pairs.py --judges judge-opus` on a pool built with `build_pairs.py --arms <name>,plain-opus,...`.
- **A judge**: add it to `JUDGES`, run `damage.py --judges <name>`; it is usable only if it clears the damage tests in `analyze.py`.
- **A target**: a line in `targets.jsonl` with a twin, facts you have checked against the sources you list, and a practice form; `generate.py --target-ids <id>` fills the arms.

## Licence

Code is MIT; the targets, run data and docs are CC BY 4.0; the house-style skill and the chapters under
`reference/` are the author's, all rights reserved (see `LICENSE`). The public humour datasets fetched by
`external_pairs.py` are not included and keep their own licences.

## Limits

Generation is Claude-only until the other families run; the judge and most generators share a family, so
self-preference is bounded (at most five points across runs) but not measured. Human calibration is one rater and
two public English sets; Chinese has no public preference data. Targets number 60 (44 things plus 16 practices); the Chinese half of the practice pool is only part-judged, the
November credits having run out there.
