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

Leaderboard (judge opinion, Bradley–Terry over every judged pool, 95% bootstrap intervals; `runs/pilot/leaderboard.md`):

| arm | en score | zh score |
|---|---:|---:|
| skill-opus | +1.94 [+1.74, +2.19] | +2.16 [+1.99, +2.30] |
| facts-opus | +1.86 [+1.65, +2.09] | +1.29 [+1.15, +1.46] |
| plain-opus | +1.71 [+1.49, +1.93] | +1.58 [+1.45, +1.71] |
| frame-opus | +0.83 [+0.67, +1.03] | +1.58 [+1.46, +1.71] |
| frame-sonnet | +0.26 [-0.03, +0.57] | +0.80 [+0.48, +1.04] |
| plain-sonnet | -0.00 [-0.28, +0.30] | +0.51 [+0.31, +0.73] |
| plain-haiku | -1.02 [-1.37, -0.72] | -2.33 [-2.80, -1.92] |
| frame-haiku | -2.29 [-2.78, -1.88] | -1.33 [-1.67, -1.01] |
| control-bland | -3.28 [-4.41, -2.49] | -4.25 [-4.44, -4.05] |

A one-point gap is about a 73% win rate. These are a validated judge's preferences, not human votes.

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

## Limits

Generation is Claude-only until the other families run; the judge and most generators share a family, so
self-preference is bounded (at most five points across runs) but not measured. Human calibration is one rater and
two public English sets; Chinese has no public preference data. Targets number 60 (44 things plus 16 practices).
