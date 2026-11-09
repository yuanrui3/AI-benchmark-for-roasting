# Preflight report: run `smoke-or`

Generated 2026-11-09T17:52:11+00:00. Gates were fixed before data was seen (CLAUDE.md).

## Generation

| arm | lang | items | refused | errors | mean words | cost $ |
|---|---|---:|---:|---:|---:|---:|
| plain-gpt | en | 4 | 0 | 0 | 120.8 | 0.03 |
| plain-gpt | zh | 4 | 0 | 0 | 111.5 | 0.03 |
| plain-gemini | en | 4 | 0 | 0 | 140.5 | 0.09 |
| plain-gemini | zh | 4 | 0 | 0 | 184.0 | 0.12 |
| plain-deepseek | en | 4 | 0 | 0 | 136.2 | 0.01 |
| plain-deepseek | zh | 4 | 0 | 0 | 196.0 | 0.02 |
| plain-qwen | en | 4 | 0 | 0 | 110.0 | 0.03 |
| plain-qwen | zh | 4 | 0 | 1 | 140.3 | 0.02 |
| control-bland | en | 4 | 0 | 0 | 134.8 | 0.01 |
| control-bland | zh | 4 | 0 | 0 | 230.0 | 0.01 |
| control-generic | en | 4 | 0 | 0 | 137.8 | 0.01 |
| control-generic | zh | 4 | 0 | 0 | 249.2 | 0.00 |

## Profile (no model needed)

Nerve = softeners per item (lower is braver). Novelty = share of items whose text collides (token Jaccard > 0.3) with another arm's item on the same target, plus stock-template hits. Economy = words per sentence.

| arm | lang | softeners/item | stock hits/item | collision rate | words/sentence |
|---|---|---:|---:|---:|---:|
| plain-gpt | en | 0.00 | 0.00 | 0% | 14.2 |
| plain-gemini | en | 0.00 | 0.00 | 0% | 10.8 |
| plain-deepseek | en | 0.00 | 0.25 | 0% | 14.3 |
| plain-qwen | en | 0.00 | 0.50 | 0% | 15.7 |
| control-bland | en | 0.00 | 0.00 | 0% | 15.0 |
| control-generic | en | 0.00 | 0.00 | 0% | 13.8 |
| plain-gpt | zh | 0.00 | 0.00 | 0% | 17.8 |
| plain-gemini | zh | 0.00 | 0.50 | 0% | 17.1 |
| plain-deepseek | zh | 0.00 | 0.25 | 0% | 13.1 |
| plain-qwen | zh | 0.00 | 0.00 | 0% | 16.8 |
| control-bland | zh | 0.00 | 0.00 | 0% | 31.7 |
| control-generic | zh | 0.00 | 0.00 | 0% | 30.2 |

## Specificity gate (masked swap test, k=5)

Chance 20%; twin-only chance 50%. Pooled over judges.

| arm | lang | n | picked target | target vs twin | residual leak | lexical contrast |
|---|---|---:|---:|---:|---:|---:|
| plain-gpt | en | 4 | 100% | 100% | 0% | 0.025 |
| plain-gpt | zh | 4 | 100% | 100% | 0% | 0.006 |
| plain-gemini | en | 4 | 100% | 100% | 0% | 0.032 |
| plain-gemini | zh | 4 | 100% | 100% | 0% | 0.002 |
| plain-deepseek | en | 3 | 100% | 100% | 0% | 0.018 |
| plain-deepseek | zh | 1 | 100% | 100% | 0% | 0.000 |

Specificity varies across arms (range >= 15 points, some arm < 90%): **False**. Generic control near chance on the twin test: **False**.

## Truth gate

An item fails only on a contradicted premise; facts absent from the sheet do not count against it.

| arm | lang | n | pass | claims/item | contradicted/item | absent/item |
|---|---|---:|---:|---:|---:|---:|
| plain-deepseek | zh | 1 | 100% | 10.0 | 0.0 | 9.0 |
| plain-qwen | en | 1 | 100% | 1.0 | 0.0 | 1.0 |
| plain-qwen | zh | 1 | 100% | 11.0 | 0.0 | 8.0 |
| control-bland | en | 1 | 0% | 12.0 | 1.0 | 11.0 |
| control-bland | zh | 1 | 100% | 7.0 | 0.0 | 7.0 |

## Judge validation (damage tests)

A usable judge prefers the original >= 90% of the time and never prefers an explained joke. P(first) is position bias (0.5 is none). Self-pref = accuracy on its own family's roasts minus others'.

| judge | lang | explain | false | frontload | generic | pad | polite | softener | overall | P(first) | self-pref | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| judge-gpt | en | 100% | 100% | 75% | 100% | 100% | 100% | 100% | 95% | 0.55 | n/a | usable |
| judge-gpt | zh | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 0.33 | +0.00 | usable |

## Human votes

_No votes yet. Open runs/<run>/rate/index.html, rate, export, and drop the JSON files into runs/<run>/votes/._

## Gates

| gate | result |
|---|---|
| controls behave (bland below real arms / generic near chance) | no data / FAIL |
| spread (two arms, non-overlapping 95% CIs) | no data |
| raters agree (>= 0.6, ties excluded) | no data |
| specificity varies | FAIL |
| a judge is usable (>= 90% damage, never prefers explained) | PASS |

**Verdict: no verdict yet (human data missing)**
