# Preflight report: run `pilot-or`

Generated 2026-11-11T19:48:52+00:00. Gates were fixed before data was seen (CLAUDE.md).

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

## Profile

Nerve = softeners per item (lower is braver). Novelty = share of items whose text collides (token Jaccard > 0.3) with another arm's item on the same target, plus stock-template hits. Economy = words per sentence. Agent-action = share of a roast's lines whose hit is someone doing something rather than a property of the object (agency.py; one column per labeller: a judge model, or `rule`, the free keyword rule; n/a until it has run). The other columns need no model.

| arm | lang | softeners/item | stock hits/item | collision rate | words/sentence | agent-action (rule) |
|---|---|---:|---:|---:|---:|---:|
| plain-gpt | en | 0.00 | 0.20 | 0% | 14.6 | 12% |
| plain-gemini | en | 0.00 | 0.10 | 0% | 12.4 | 15% |
| plain-deepseek | en | 0.00 | 0.30 | 0% | 14.9 | 16% |
| plain-qwen | en | 0.00 | 0.50 | 0% | 15.7 | 23% |
| control-bland | en | 0.00 | 0.10 | 0% | 15.5 | 5% |
| control-generic | en | 0.00 | 0.00 | 0% | 14.0 | 19% |
| plain-gpt | zh | 0.00 | 0.10 | 0% | 23.7 | 6% |
| plain-gemini | zh | 0.00 | 0.10 | 0% | 21.5 | 7% |
| plain-deepseek | zh | 0.00 | 0.00 | 0% | 21.6 | 11% |
| plain-qwen | zh | 0.00 | 0.10 | 0% | 19.3 | 12% |
| control-bland | zh | 0.00 | 0.00 | 0% | 29.9 | 18% |
| control-generic | zh | 0.00 | 0.20 | 0% | 23.6 | 12% |

## Novelty (comic device)

One judge call per target and language groups that target's roasts by the image or angle each is built on (devices.py). Cross-arm = share of an arm's items whose device another arm also used on the same target; self-repeat = the arm's own samples share a device. One row per judge, items = roasts that judge grouped; a judge that ran before an arm was added never saw that arm, so compare cross-arm rates only between judges whose cells hold the same arms (cell sizes below). Attractors are devices three or more arms reached on their own.

| arm | lang | judge | items | cross-arm | self-repeat |
|---|---|---|---:|---:|---:|
| plain-gpt | en | judge-deepseek | 10 | 80% | 0% |
| plain-gpt | zh | judge-deepseek | 10 | 90% | 0% |
| plain-gemini | en | judge-deepseek | 10 | 60% | 0% |
| plain-gemini | zh | judge-deepseek | 10 | 60% | 0% |
| plain-deepseek | en | judge-deepseek | 10 | 90% | 0% |
| plain-deepseek | zh | judge-deepseek | 10 | 90% | 0% |
| plain-qwen | en | judge-deepseek | 10 | 70% | 0% |
| plain-qwen | zh | judge-deepseek | 10 | 60% | 0% |

- judge-deepseek: 20 cells, 4.0 roasts from 4.0 arms per cell

Attractors:

- 4 arms, javascript (en): gaslighting logic and weird type coercion [judge-deepseek]
- 4 arms, las-vegas (zh): 机场老虎机 [judge-deepseek]
- 4 arms, macau (zh): 大三巴只是一堵墙 [judge-deepseek]
- 4 arms, papyrus (en): appropriated spiritual font for faux-authentic media [judge-deepseek]
- 3 arms, comic-sans (zh): 幼儿园手工/涂鸦 [judge-deepseek]
- 3 arms, crocs (zh): 花钱堵洞 [judge-deepseek]
- 3 arms, durian (en): Medieval weapon / biological weapon [judge-deepseek]
- 3 arms, jackfruit (en): medieval weapon fruit [judge-deepseek]
- 3 arms, las-vegas (en): fake landmarks and overpriced cheap experiences [judge-deepseek]
- 3 arms, ugg (en): shapeless food-like foot (bread/marshmallow/pillow) [judge-deepseek]

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

An item fails only on a contradicted premise; facts absent from the sheet do not count against it. One row per judge, n = items; where several judges checked an item it passes the gate only if every one of them passed it.

| arm | lang | judge | n | pass | claims/item | contradicted/item | absent/item |
|---|---|---|---:|---:|---:|---:|---:|
| plain-gpt | en | judge-deepseek | 8 | 100% | 6.88 | 0.0 | 4.75 |
| plain-gpt | en | judge-gpt | 4 | 100% | 8.5 | 0.0 | 6.25 |
| plain-gpt | zh | judge-deepseek | 7 | 100% | 4.86 | 0.0 | 2.71 |
| plain-gpt | zh | judge-gpt | 4 | 75% | 4.75 | 0.25 | 2.5 |
| plain-gemini | en | judge-deepseek | 8 | 100% | 6.38 | 0.0 | 3.62 |
| plain-gemini | en | judge-gpt | 4 | 100% | 7.75 | 0.0 | 4.25 |
| plain-gemini | zh | judge-deepseek | 6 | 100% | 4.83 | 0.0 | 3.67 |
| plain-gemini | zh | judge-gpt | 4 | 100% | 5.0 | 0.0 | 2.5 |
| plain-deepseek | en | judge-deepseek | 6 | 83% | 5.83 | 0.17 | 4.17 |
| plain-deepseek | en | judge-gpt | 4 | 100% | 9.25 | 0.0 | 6.0 |
| plain-deepseek | zh | judge-deepseek | 9 | 100% | 5.22 | 0.0 | 3.44 |
| plain-deepseek | zh | judge-gpt | 4 | 100% | 5.0 | 0.0 | 3.25 |
| plain-qwen | en | judge-deepseek | 9 | 89% | 7.11 | 0.11 | 3.78 |
| plain-qwen | en | judge-gpt | 4 | 100% | 8.5 | 0.0 | 4.5 |
| plain-qwen | zh | judge-deepseek | 7 | 100% | 5.43 | 0.0 | 3.57 |
| plain-qwen | zh | judge-gpt | 4 | 100% | 7.0 | 0.0 | 4.0 |
| control-bland | en | judge-deepseek | 5 | 100% | 10.8 | 0.0 | 8.8 |
| control-bland | en | judge-gpt | 4 | 100% | 13.0 | 0.0 | 11.0 |
| control-bland | zh | judge-deepseek | 8 | 100% | 9.0 | 0.0 | 6.88 |
| control-bland | zh | judge-gpt | 4 | 100% | 11.75 | 0.0 | 8.75 |

- en: judge-deepseek and judge-gpt agree on pass/fail for 100% of 20 items both checked; judge-deepseek alone fails 0, judge-gpt alone fails 0.
- zh: judge-deepseek and judge-gpt agree on pass/fail for 95% of 19 items both checked; judge-deepseek alone fails 0, judge-gpt alone fails 1.

## Judge validation (damage tests)

A usable judge prefers the original >= 90% of the time and never prefers an explained joke. P(first) is position bias (0.5 is none). Self-pref = accuracy on its own family's roasts minus others'.

| judge | lang | explain | false | frontload | generic | pad | polite | softener | overall | P(first) | self-pref | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| judge-deepseek | en | 75% | 75% | 83% | 100% | 100% | 100% | 100% | 90% | 0.55 | +0.09 | discard |
| judge-deepseek | zh | 100% | 67% | 83% | 100% | 92% | 100% | 100% | 92% | 0.54 | +0.07 | usable |
| judge-gpt | en | 100% | 75% | 83% | 100% | 100% | 100% | 100% | 93% | 0.51 | -0.02 | usable |
| judge-gpt | zh | n/a | 83% | 75% | 100% | 100% | 100% | 100% | 93% | 0.54 | +0.08 | usable |
| judge-opus | en | 100% | 67% | 92% | 100% | 100% | 100% | 100% | 94% | 0.51 | n/a | usable |
| judge-opus | zh | 100% | 92% | 100% | 100% | 100% | 100% | 100% | 99% | 0.49 | n/a | usable |

## Human votes

100 votes from 1 rater(s): owner.

Rater cards (stated taste, so a ranking reads as 'funny to these people'):

- **owner**: languages ?; likes I find funny things to be funny; dark-humor tolerance 5/5; aggressive-humor 4.5/7; off-limits: Mbappe

Aggressive-humor is the rater's 1–7 score from the four card items; line flags is the share of their votes where they flagged a roast as crossing a line. A higher score should go with fewer flags.

| rater | lang | votes | decisive | both bad | skipped | gold acc | median s/vote | aggressive-humor | line flags |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| owner | zh | 100 | 54 | 36 | 10 | 100% | 8.1 | 4.5 | 2% |

Per target (all pairs, gold included). Both-bad and skip counts say where the material or the rater gave up; familiarity is the number of raters who said, the first time the target came up, that they know it well / had heard of it / had no idea (zero everywhere for exports made before the question existed).

| lang | target | votes | decisive | both bad | skipped | median s/vote | know well | heard of | no idea |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| zh | javascript | 13 | 7 | 0 | 6 | 4.3 | 0 | 0 | 0 |
| zh | php | 12 | 4 | 4 | 4 | 9.8 | 0 | 0 | 0 |
| zh | comic-sans | 11 | 2 | 9 | 0 | 11.1 | 0 | 0 | 0 |
| zh | papyrus | 10 | 6 | 4 | 0 | 6.6 | 0 | 0 | 0 |
| zh | ugg | 9 | 5 | 4 | 0 | 8.2 | 0 | 0 | 0 |
| zh | macau | 9 | 6 | 3 | 0 | 7.5 | 0 | 0 | 0 |
| zh | crocs | 9 | 8 | 1 | 0 | 8.4 | 0 | 0 | 0 |
| zh | jackfruit | 9 | 5 | 4 | 0 | 12.0 | 0 | 0 | 0 |
| zh | durian | 9 | 7 | 2 | 0 | 5.2 | 0 | 0 | 0 |
| zh | las-vegas | 9 | 4 | 5 | 0 | 5.4 | 0 | 0 | 0 |

### Bradley-Terry on human votes, zh (52 decisive votes, all items)

| arm | score | 95% CI | both-bad rate | appearances |
|---|---:|---|---:|---:|
| plain-gpt | +0.71 | [+0.07, +1.39] | 32% | 21 |
| plain-qwen | +0.66 | [+0.11, +1.25] | 32% | 22 |
| plain-deepseek | +0.53 | [-0.13, +1.22] | 36% | 18 |
| plain-gemini | +0.12 | [-0.50, +0.77] | 42% | 20 |
| control-bland | -2.03 | [-2.29, -1.74] | 29% | 23 |

### Bradley-Terry, zh, gated (50 votes where both items passed specificity and truth)

| arm | score | 95% CI | appearances |
|---|---:|---|---:|
| plain-qwen | +0.66 | [+0.16, +1.20] | 22 |
| plain-gpt | +0.64 | [-0.01, +1.34] | 19 |
| plain-deepseek | +0.53 | [-0.07, +1.19] | 18 |
| plain-gemini | +0.17 | [-0.45, +0.80] | 19 |
| control-bland | -2.00 | [-2.26, -1.72] | 22 |

Mean 95% CI width across real arms: 1.27 log-odds. To reach a width of 0.5 (arms one notch apart become distinguishable) you need about **336 decisive votes** in zh, vs 52 now.

### Judge vs human, zh

- judge-deepseek: agrees with human votes 63% (n=19); flips its answer when order is swapped 18%. Human-human ceiling: n/a.
- judge-gpt: agrees with human votes 57% (n=21); flips its answer when order is swapped 12%. Human-human ceiling: n/a.
- judge-opus: agrees with human votes 77% (n=47); flips its answer when order is swapped 13%. Human-human ceiling: n/a.

## Gates

| gate | result |
|---|---|
| controls behave (bland below real arms / generic near chance) | PASS / PASS |
| spread (two arms, non-overlapping 95% CIs) | FAIL |
| raters agree (>= 0.6, ties excluded) | no data |
| specificity varies | FAIL |
| a judge is usable (>= 90% damage, never prefers explained) | PASS |

**Verdict: NO-GO as designed; see failed gates**
