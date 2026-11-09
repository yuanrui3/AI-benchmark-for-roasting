# Preflight report: run `pilot-or`

Generated 2026-11-09T19:52:36+00:00. Gates were fixed before data was seen (CLAUDE.md).

## Generation

| arm | lang | items | refused | errors | mean words | cost $ |
|---|---|---:|---:|---:|---:|---:|
| plain-gpt | en | 10 | 0 | 0 | 123.9 | 0.07 |
| plain-gpt | zh | 10 | 0 | 0 | 128.2 | 0.07 |
| plain-gemini | en | 10 | 0 | 0 | 140.0 | 0.22 |
| plain-gemini | zh | 10 | 0 | 0 | 198.1 | 0.27 |
| plain-deepseek | en | 10 | 0 | 0 | 150.3 | 0.01 |
| plain-deepseek | zh | 10 | 0 | 0 | 174.7 | 0.02 |
| plain-qwen | en | 10 | 0 | 0 | 117.9 | 0.06 |
| plain-qwen | zh | 10 | 0 | 0 | 158.6 | 0.12 |
| control-bland | en | 10 | 0 | 0 | 127.0 | 0.02 |
| control-bland | zh | 10 | 0 | 0 | 218.6 | 0.01 |
| control-generic | en | 10 | 0 | 0 | 149.9 | 0.02 |
| control-generic | zh | 10 | 0 | 0 | 221.9 | 0.03 |

## Profile (no model needed)

Nerve = softeners per item (lower is braver). Novelty = share of items whose text collides (token Jaccard > 0.3) with another arm's item on the same target, plus stock-template hits. Economy = words per sentence.

| arm | lang | softeners/item | stock hits/item | collision rate | words/sentence |
|---|---|---:|---:|---:|---:|
| plain-gpt | en | 0.00 | 0.20 | 0% | 14.6 |
| plain-gemini | en | 0.00 | 0.10 | 0% | 12.4 |
| plain-deepseek | en | 0.00 | 0.30 | 0% | 14.9 |
| plain-qwen | en | 0.00 | 0.50 | 0% | 15.7 |
| control-bland | en | 0.00 | 0.10 | 0% | 15.5 |
| control-generic | en | 0.00 | 0.00 | 0% | 14.0 |
| plain-gpt | zh | 0.00 | 0.10 | 0% | 23.7 |
| plain-gemini | zh | 0.00 | 0.10 | 0% | 21.5 |
| plain-deepseek | zh | 0.00 | 0.00 | 0% | 21.6 |
| plain-qwen | zh | 0.00 | 0.10 | 0% | 19.3 |
| control-bland | zh | 0.00 | 0.00 | 0% | 29.9 |
| control-generic | zh | 0.00 | 0.20 | 0% | 23.6 |

## Specificity gate (masked swap test, k=5)

Chance 20%; twin-only chance 50%. Pooled over judges.

| arm | lang | n | picked target | target vs twin | residual leak | lexical contrast |
|---|---|---:|---:|---:|---:|---:|
| plain-gpt | en | 20 | 100% | 100% | 0% | 0.009 |
| plain-gpt | zh | 20 | 100% | 100% | 0% | 0.002 |
| plain-gemini | en | 20 | 100% | 100% | 0% | 0.015 |
| plain-gemini | zh | 20 | 100% | 100% | 0% | -0.000 |
| plain-deepseek | en | 20 | 100% | 100% | 0% | 0.022 |
| plain-deepseek | zh | 20 | 100% | 100% | 0% | 0.001 |
| plain-qwen | en | 20 | 100% | 100% | 0% | 0.026 |
| plain-qwen | zh | 20 | 100% | 100% | 0% | 0.004 |
| control-bland | en | 20 | 100% | 100% | 0% | 0.007 |
| control-bland | zh | 20 | 100% | 100% | 0% | 0.001 |
| control-generic | en | 20 | 45% | 45% | 0% | 0.004 |
| control-generic | zh | 20 | 50% | 50% | 0% | 0.000 |

Specificity varies across arms (range >= 15 points, some arm < 90%): **False**. Generic control near chance on the twin test: **True**.

## Truth gate

An item fails only on a contradicted premise; facts absent from the sheet do not count against it.

| arm | lang | n | pass | claims/item | contradicted/item | absent/item |
|---|---|---:|---:|---:|---:|---:|
| plain-gpt | en | 12 | 100% | 7.42 | 0.0 | 5.25 |
| plain-gpt | zh | 11 | 91% | 4.82 | 0.09 | 2.64 |
| plain-gemini | en | 12 | 100% | 6.83 | 0.0 | 3.83 |
| plain-gemini | zh | 10 | 100% | 4.9 | 0.0 | 3.2 |
| plain-deepseek | en | 10 | 90% | 7.2 | 0.1 | 4.9 |
| plain-deepseek | zh | 13 | 100% | 5.15 | 0.0 | 3.38 |
| plain-qwen | en | 13 | 92% | 7.54 | 0.08 | 4.0 |
| plain-qwen | zh | 11 | 100% | 6.0 | 0.0 | 3.73 |
| control-bland | en | 9 | 100% | 11.78 | 0.0 | 9.78 |
| control-bland | zh | 12 | 100% | 9.92 | 0.0 | 7.5 |

## Judge validation (damage tests)

A usable judge prefers the original >= 90% of the time and never prefers an explained joke. P(first) is position bias (0.5 is none). Self-pref = accuracy on its own family's roasts minus others'.

| judge | lang | explain | false | frontload | generic | pad | polite | softener | overall | P(first) | self-pref | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| judge-deepseek | en | 75% | 75% | 83% | 100% | 100% | 100% | 100% | 90% | 0.55 | +0.09 | discard |
| judge-deepseek | zh | 100% | 67% | 83% | 100% | 92% | 100% | 100% | 92% | 0.54 | +0.07 | usable |
| judge-gpt | en | 100% | 75% | 83% | 100% | 100% | 100% | 100% | 93% | 0.51 | -0.02 | usable |
| judge-gpt | zh | n/a | 83% | 75% | 100% | 100% | 100% | 100% | 93% | 0.54 | +0.08 | usable |

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
