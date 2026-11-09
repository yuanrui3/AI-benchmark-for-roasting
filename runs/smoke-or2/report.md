# Preflight report: run `smoke-or2`

Generated 2026-11-09T19:04:35+00:00. Gates were fixed before data was seen (CLAUDE.md).

## Generation

| arm | lang | items | refused | errors | mean words | cost $ |
|---|---|---:|---:|---:|---:|---:|
| plain-gpt | en | 4 | 0 | 0 | 123.5 | 0.03 |
| plain-gpt | zh | 4 | 0 | 0 | 105.5 | 0.03 |
| plain-gemini | en | 4 | 0 | 0 | 140.5 | 0.08 |
| plain-gemini | zh | 4 | 0 | 0 | 173.5 | 0.11 |
| plain-deepseek | en | 4 | 0 | 0 | 141.0 | 0.01 |
| plain-deepseek | zh | 4 | 0 | 0 | 152.2 | 0.00 |
| plain-qwen | en | 4 | 0 | 0 | 115.5 | 0.02 |
| plain-qwen | zh | 4 | 0 | 0 | 145.2 | 0.08 |
| control-bland | en | 4 | 0 | 0 | 121.0 | 0.01 |
| control-bland | zh | 4 | 0 | 0 | 218.5 | 0.01 |
| control-generic | en | 4 | 0 | 0 | 143.2 | 0.01 |
| control-generic | zh | 4 | 0 | 0 | 235.8 | 0.01 |

## Profile (no model needed)

Nerve = softeners per item (lower is braver). Novelty = share of items whose text collides (token Jaccard > 0.3) with another arm's item on the same target, plus stock-template hits. Economy = words per sentence.

| arm | lang | softeners/item | stock hits/item | collision rate | words/sentence |
|---|---|---:|---:|---:|---:|
| plain-gpt | en | 0.00 | 0.25 | 0% | 15.4 |
| plain-gemini | en | 0.00 | 0.25 | 0% | 11.0 |
| plain-deepseek | en | 0.00 | 0.75 | 0% | 12.8 |
| plain-qwen | en | 0.00 | 0.75 | 0% | 16.5 |
| control-bland | en | 0.00 | 0.00 | 0% | 16.1 |
| control-generic | en | 0.00 | 0.00 | 0% | 14.0 |
| plain-gpt | zh | 0.00 | 0.00 | 0% | 20.1 |
| plain-gemini | zh | 0.00 | 0.25 | 0% | 16.1 |
| plain-deepseek | zh | 0.00 | 0.00 | 0% | 16.9 |
| plain-qwen | zh | 0.00 | 0.00 | 0% | 16.1 |
| control-bland | zh | 0.00 | 0.00 | 0% | 31.2 |
| control-generic | zh | 0.00 | 0.00 | 0% | 21.4 |

## Specificity gate (masked swap test, k=5)

Chance 20%; twin-only chance 50%. Pooled over judges.

| arm | lang | n | picked target | target vs twin | residual leak | lexical contrast |
|---|---|---:|---:|---:|---:|---:|
| plain-gpt | en | 4 | 100% | 100% | 0% | -0.003 |
| plain-gpt | zh | 4 | 100% | 100% | 0% | 0.005 |
| plain-gemini | en | 4 | 100% | 100% | 0% | 0.023 |
| plain-gemini | zh | 4 | 100% | 100% | 0% | -0.000 |
| plain-deepseek | en | 4 | 100% | 100% | 0% | 0.025 |
| plain-deepseek | zh | 4 | 100% | 100% | 0% | 0.002 |
| plain-qwen | en | 4 | 100% | 100% | 0% | 0.029 |
| plain-qwen | zh | 4 | 100% | 100% | 0% | 0.009 |
| control-bland | en | 4 | 100% | 100% | 0% | 0.005 |
| control-bland | zh | 4 | 100% | 100% | 0% | 0.002 |
| control-generic | en | 4 | 50% | 50% | 0% | -0.002 |
| control-generic | zh | 4 | 50% | 50% | 0% | 0.000 |

Specificity varies across arms (range >= 15 points, some arm < 90%): **False**. Generic control near chance on the twin test: **True**.

## Truth gate

An item fails only on a contradicted premise; facts absent from the sheet do not count against it.

| arm | lang | n | pass | claims/item | contradicted/item | absent/item |
|---|---|---:|---:|---:|---:|---:|
| plain-gpt | en | 4 | 100% | 8.5 | 0.0 | 6.25 |
| plain-gpt | zh | 4 | 75% | 4.75 | 0.25 | 2.5 |
| plain-gemini | en | 4 | 100% | 7.75 | 0.0 | 4.25 |
| plain-gemini | zh | 4 | 100% | 5.0 | 0.0 | 2.5 |
| plain-deepseek | en | 4 | 100% | 9.25 | 0.0 | 6.0 |
| plain-deepseek | zh | 4 | 100% | 5.0 | 0.0 | 3.25 |
| plain-qwen | en | 4 | 100% | 8.5 | 0.0 | 4.5 |
| plain-qwen | zh | 4 | 100% | 7.0 | 0.0 | 4.0 |
| control-bland | en | 4 | 100% | 13.0 | 0.0 | 11.0 |
| control-bland | zh | 4 | 100% | 11.75 | 0.0 | 8.75 |

## Judge validation (damage tests)

A usable judge prefers the original >= 90% of the time and never prefers an explained joke. P(first) is position bias (0.5 is none). Self-pref = accuracy on its own family's roasts minus others'.

| judge | lang | explain | false | frontload | generic | pad | polite | softener | overall | P(first) | self-pref | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| judge-gpt | en | 100% | 75% | 83% | 100% | 100% | 100% | 100% | 94% | 0.51 | -0.01 | usable |
| judge-gpt | zh | 83% | 83% | 75% | 100% | 100% | 100% | 100% | 92% | 0.54 | +0.10 | discard |

## Human votes

_No votes yet. Open runs/<run>/rate/index.html, rate, export, and drop the JSON files into runs/<run>/votes/._

## Gates

| gate | result |
|---|---|
| controls behave (bland below real arms / generic near chance) | no data / PASS |
| spread (two arms, non-overlapping 95% CIs) | no data |
| raters agree (>= 0.6, ties excluded) | no data |
| specificity varies | FAIL |
| a judge is usable (>= 90% damage, never prefers explained) | PASS |

**Verdict: no verdict yet (human data missing)**
