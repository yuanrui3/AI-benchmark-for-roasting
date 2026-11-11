# Preflight report: run `pilot`

Generated 2026-11-11T23:01:28+00:00. Gates were fixed before data was seen (CLAUDE.md).

## Generation

| arm | lang | items | refused | errors | mean words | cost $ |
|---|---|---:|---:|---:|---:|---:|
| plain-opus | en | 120 | 0 | 0 | 141.2 | 1.72 |
| plain-opus | zh | 120 | 0 | 0 | 204.1 | 2.08 |
| facts-opus | en | 120 | 0 | 0 | 139.8 | 2.24 |
| facts-opus | zh | 120 | 0 | 0 | 198.2 | 2.46 |
| skill-opus | en | 120 | 0 | 0 | 135.5 | 3.63 |
| skill-opus | zh | 120 | 0 | 0 | 187.0 | 3.81 |
| frame-opus | en | 120 | 0 | 0 | 137.4 | 2.06 |
| frame-opus | zh | 120 | 0 | 0 | 199.9 | 2.19 |
| control-bland | en | 120 | 0 | 0 | 149.3 | 0.41 |
| control-bland | zh | 120 | 0 | 0 | 278.1 | 0.74 |
| control-generic | en | 88 | 0 | 0 | 152.3 | 0.34 |
| control-generic | zh | 88 | 0 | 0 | 215.8 | 0.85 |
| plain-sonnet | en | 88 | 0 | 0 | 157.6 | 0.31 |
| plain-sonnet | zh | 88 | 0 | 0 | 214.5 | 1.02 |
| plain-haiku | en | 88 | 0 | 0 | 126.7 | 0.03 |
| plain-haiku | zh | 88 | 0 | 0 | 168.4 | 0.05 |
| frame-sonnet | en | 88 | 0 | 0 | 145.3 | 0.75 |
| frame-sonnet | zh | 88 | 0 | 0 | 209.9 | 1.18 |
| frame-haiku | en | 88 | 0 | 0 | 125.1 | 0.04 |
| frame-haiku | zh | 88 | 0 | 0 | 177.2 | 0.05 |

## Profile

Nerve = softeners per item (lower is braver). Novelty = share of items whose text collides (token Jaccard > 0.3) with another arm's item on the same target, plus stock-template hits. Economy = words per sentence. Agent-action = share of a roast's lines whose hit is someone doing something rather than a property of the object (agency.py; one column per labeller: a judge model, or `rule`, the free keyword rule; n/a until it has run). The other columns need no model.

| arm | lang | softeners/item | stock hits/item | collision rate | words/sentence | agent-action (judge-opus) | agent-action (judge-sonnet) | agent-action (rule) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| plain-opus | en | 0.00 | 0.03 | 0% | 10.1 | 37% | 38% | 15% |
| facts-opus | en | 0.00 | 0.03 | 29% | 8.9 | 45% | 37% | 12% |
| skill-opus | en | 0.00 | 0.03 | 28% | 6.2 | 47% | 44% | 8% |
| frame-opus | en | 0.00 | 0.03 | 0% | 10.6 | 88% | 84% | 20% |
| control-bland | en | 0.00 | 0.05 | 0% | 14.7 | 22% | 22% | 15% |
| control-generic | en | 0.00 | 0.06 | 0% | 10.4 | 49% | 48% | 16% |
| plain-sonnet | en | 0.00 | 0.10 | 0% | 10.3 | 39% | 36% | 15% |
| plain-haiku | en | 0.00 | 0.09 | 0% | 12.1 | 38% | 39% | 16% |
| frame-sonnet | en | 0.00 | 0.05 | 0% | 11.2 | 90% | 87% | 20% |
| frame-haiku | en | 0.00 | 0.05 | 0% | 12.3 | 91% | 92% | 22% |
| plain-opus | zh | 0.00 | 0.01 | 0% | 15.5 | 35% | 39% | 8% |
| facts-opus | zh | 0.00 | 0.03 | 2% | 14.8 | 43% | 37% | 8% |
| skill-opus | zh | 0.00 | 0.07 | 2% | 12.4 | 43% | 39% | 7% |
| frame-opus | zh | 0.01 | 0.01 | 0% | 15.8 | 77% | 75% | 14% |
| control-bland | zh | 0.00 | 0.02 | 0% | 28.5 | 6% | 12% | 16% |
| control-generic | zh | 0.00 | 0.05 | 0% | 16.2 | 53% | 51% | 12% |
| plain-sonnet | zh | 0.00 | 0.03 | 0% | 15.9 | 37% | 36% | 9% |
| plain-haiku | zh | 0.00 | 0.02 | 0% | 18.8 | 28% | 29% | 8% |
| frame-sonnet | zh | 0.00 | 0.02 | 0% | 16.4 | 77% | 72% | 18% |
| frame-haiku | zh | 0.00 | 0.01 | 0% | 18.3 | 77% | 73% | 19% |

## Novelty (comic device)

One judge call per target and language groups that target's roasts by the image or angle each is built on (devices.py). Cross-arm = share of an arm's items whose device another arm also used on the same target; self-repeat = the arm's own samples share a device. One row per judge, items = roasts that judge grouped; a judge that ran before an arm was added never saw that arm, so compare cross-arm rates only between judges whose cells hold the same arms (cell sizes below). Attractors are devices three or more arms reached on their own.

| arm | lang | judge | items | cross-arm | self-repeat |
|---|---|---|---:|---:|---:|
| plain-opus | en | judge-opus | 88 | 44% | 68% |
| plain-opus | en | judge-sonnet | 120 | 44% | 82% |
| plain-opus | zh | judge-opus | 88 | 51% | 66% |
| plain-opus | zh | judge-sonnet | 120 | 55% | 73% |
| facts-opus | en | judge-opus | 88 | 73% | 91% |
| facts-opus | en | judge-sonnet | 120 | 82% | 88% |
| facts-opus | zh | judge-opus | 88 | 75% | 95% |
| facts-opus | zh | judge-sonnet | 120 | 78% | 92% |
| skill-opus | en | judge-opus | 88 | 67% | 91% |
| skill-opus | en | judge-sonnet | 120 | 68% | 77% |
| skill-opus | zh | judge-opus | 88 | 75% | 93% |
| skill-opus | zh | judge-sonnet | 120 | 71% | 77% |
| plain-sonnet | en | judge-opus | 88 | 41% | 61% |
| plain-sonnet | en | judge-sonnet | 88 | 62% | 77% |
| plain-sonnet | zh | judge-opus | 88 | 51% | 64% |
| plain-sonnet | zh | judge-sonnet | 88 | 70% | 64% |
| plain-haiku | en | judge-opus | 88 | 32% | 57% |
| plain-haiku | en | judge-sonnet | 88 | 51% | 70% |
| plain-haiku | zh | judge-opus | 88 | 27% | 59% |
| plain-haiku | zh | judge-sonnet | 88 | 40% | 64% |

- judge-opus: 88 cells, 10.0 roasts from 5.0 arms per cell
- judge-sonnet: 120 cells, 8.9 roasts from 4.5 arms per cell
- en: judge-opus and judge-sonnet agree on whether two roasts share a device for 83% of 1980 roast pairs both grouped (judge-opus puts 20% of them in one device, judge-sonnet 28%).
- zh: judge-opus and judge-sonnet agree on whether two roasts share a device for 87% of 1980 roast pairs both grouped (judge-opus puts 23% of them in one device, judge-sonnet 28%).

Attractors:

- 5 arms, nuclear-fusion (zh): 永远还差三十年 [judge-sonnet]
- 4 arms, emacs (en): Great OS lacking a good editor [judge-sonnet]
- 4 arms, emacs (zh): 操作系统缺好编辑器 [judge-opus, judge-sonnet]
- 4 arms, javascript (en): Quirk catalogue: rapid-fire list of language gotchas [judge-sonnet]
- 4 arms, juicero (en): Hands beat the machine; bag-squeezing absurdity [judge-sonnet]
- 4 arms, luosifen (zh): 螺蛳背锅酸笋干活 [judge-opus, judge-sonnet]
- 4 arms, nfts (en): You bought a receipt, not art [judge-opus, judge-sonnet]
- 4 arms, nfts (zh): 买了个收藏夹/网址收据 [judge-opus, judge-sonnet]
- 4 arms, oat-milk (zh): 燕麦奶就是粥汤 [judge-opus, judge-sonnet]
- 4 arms, vim (en): Vim as a hostage situation [judge-sonnet]
- 3 arms, almond-milk (en): Almond milk as a rumor of a nut, diluted [judge-sonnet]
- 3 arms, almond-milk (zh): 杏仁路过的水 [judge-sonnet]

## Specificity gate (masked swap test, k=5)

Chance 20%; twin-only chance 50%. Pooled over judges.

| arm | lang | n | picked target | target vs twin | residual leak | lexical contrast |
|---|---|---:|---:|---:|---:|---:|
| plain-opus | en | 118 | 100% | 100% | 0% | 0.037 |
| plain-opus | zh | 120 | 100% | 100% | 0% | 0.001 |
| facts-opus | en | 116 | 96% | 99% | 0% | 0.212 |
| facts-opus | zh | 119 | 100% | 100% | 0% | 0.006 |
| skill-opus | en | 118 | 95% | 97% | 0% | 0.174 |
| skill-opus | zh | 119 | 100% | 100% | 0% | 0.005 |
| frame-opus | en | 119 | 97% | 100% | 0% | 0.020 |
| frame-opus | zh | 119 | 99% | 99% | 0% | 0.001 |
| control-bland | en | 120 | 100% | 100% | 0% | 0.019 |
| control-bland | zh | 120 | 100% | 100% | 0% | 0.001 |
| control-generic | en | 84 | 49% | 50% | 0% | -0.001 |
| control-generic | zh | 83 | 48% | 49% | 0% | 0.000 |
| plain-sonnet | en | 88 | 100% | 100% | 0% | 0.035 |
| plain-sonnet | zh | 88 | 99% | 99% | 0% | 0.002 |
| plain-haiku | en | 87 | 100% | 100% | 0% | 0.028 |
| plain-haiku | zh | 88 | 100% | 100% | 0% | 0.002 |
| frame-sonnet | en | 86 | 91% | 95% | 0% | 0.014 |
| frame-sonnet | zh | 88 | 99% | 99% | 0% | 0.001 |
| frame-haiku | en | 87 | 97% | 98% | 0% | 0.016 |
| frame-haiku | zh | 88 | 100% | 100% | 0% | 0.001 |

Specificity varies across arms (range >= 15 points, some arm < 90%): **False**. Generic control near chance on the twin test: **True**.

## Truth gate

An item fails only on a contradicted premise; facts absent from the sheet do not count against it. One row per judge, n = items; where several judges checked an item it passes the gate only if every one of them passed it.

| arm | lang | judge | n | pass | claims/item | contradicted/item | absent/item |
|---|---|---|---:|---:|---:|---:|---:|
| plain-opus | en | judge-opus | 88 | 91% | 9.4 | 0.1 | 5.3 |
| plain-opus | en | judge-sonnet | 120 | 79% | 9.72 | 0.22 | 5.73 |
| plain-opus | zh | judge-opus | 88 | 93% | 6.14 | 0.08 | 3.56 |
| plain-opus | zh | judge-sonnet | 120 | 90% | 7.85 | 0.12 | 4.75 |
| facts-opus | en | judge-opus | 88 | 96% | 8.49 | 0.05 | 0.23 |
| facts-opus | en | judge-sonnet | 120 | 97% | 10.05 | 0.03 | 0.76 |
| facts-opus | zh | judge-opus | 88 | 99% | 7.45 | 0.01 | 0.2 |
| facts-opus | zh | judge-sonnet | 120 | 92% | 10.51 | 0.07 | 0.78 |
| skill-opus | en | judge-opus | 88 | 98% | 9.06 | 0.02 | 0.92 |
| skill-opus | en | judge-sonnet | 120 | 92% | 10.8 | 0.08 | 1.75 |
| skill-opus | zh | judge-opus | 88 | 98% | 7.89 | 0.02 | 0.76 |
| skill-opus | zh | judge-sonnet | 120 | 92% | 11.02 | 0.08 | 1.8 |
| frame-opus | en | judge-opus | 88 | 96% | 7.0 | 0.05 | 4.02 |
| frame-opus | en | judge-sonnet | 120 | 91% | 7.59 | 0.11 | 4.56 |
| frame-opus | zh | judge-opus | 88 | 94% | 5.93 | 0.06 | 3.5 |
| frame-opus | zh | judge-sonnet | 120 | 88% | 7.76 | 0.14 | 4.67 |
| control-bland | en | judge-opus | 88 | 99% | 9.01 | 0.01 | 6.14 |
| control-bland | en | judge-sonnet | 120 | 94% | 9.07 | 0.07 | 6.46 |
| control-bland | zh | judge-opus | 87 | 98% | 8.32 | 0.02 | 5.62 |
| control-bland | zh | judge-sonnet | 120 | 96% | 9.09 | 0.04 | 6.09 |
| plain-sonnet | en | judge-opus | 88 | 78% | 8.05 | 0.26 | 4.41 |
| plain-sonnet | en | judge-sonnet | 88 | 76% | 8.94 | 0.27 | 4.98 |
| plain-sonnet | zh | judge-opus | 88 | 91% | 5.55 | 0.09 | 2.93 |
| plain-sonnet | zh | judge-sonnet | 87 | 93% | 7.59 | 0.08 | 4.03 |
| plain-haiku | en | judge-opus | 88 | 90% | 5.98 | 0.11 | 3.14 |
| plain-haiku | en | judge-sonnet | 88 | 84% | 7.17 | 0.17 | 3.98 |
| plain-haiku | zh | judge-opus | 88 | 90% | 4.58 | 0.1 | 2.59 |
| plain-haiku | zh | judge-sonnet | 88 | 91% | 6.23 | 0.1 | 3.57 |
| frame-sonnet | en | judge-opus | 88 | 97% | 6.07 | 0.03 | 3.58 |
| frame-sonnet | en | judge-sonnet | 88 | 94% | 6.69 | 0.06 | 4.02 |
| frame-sonnet | zh | judge-opus | 88 | 92% | 5.48 | 0.08 | 3.32 |
| frame-sonnet | zh | judge-sonnet | 88 | 89% | 7.26 | 0.11 | 4.3 |
| frame-haiku | en | judge-opus | 88 | 96% | 5.07 | 0.05 | 2.94 |
| frame-haiku | en | judge-sonnet | 88 | 90% | 5.35 | 0.1 | 2.97 |
| frame-haiku | zh | judge-opus | 88 | 97% | 4.82 | 0.03 | 2.84 |
| frame-haiku | zh | judge-sonnet | 88 | 86% | 6.48 | 0.14 | 3.94 |

- en: judge-opus and judge-sonnet agree on pass/fail for 92% of 792 items both checked; judge-opus alone fails 19, judge-sonnet alone fails 43.
- zh: judge-opus and judge-sonnet agree on pass/fail for 92% of 790 items both checked; judge-opus alone fails 21, judge-sonnet alone fails 41.

## Judge validation (damage tests)

A usable judge prefers the original >= 90% of the time and never prefers an explained joke. P(first) is position bias (0.5 is none). Self-pref = accuracy on its own family's roasts minus others'.

| judge | lang | explain | false | frontload | generic | pad | polite | softener | overall | P(first) | self-pref | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| judge-opus | en | 100% | 100% | 98% | 95% | 100% | 98% | 100% | 99% | 0.51 | n/a | usable |
| judge-opus | zh | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 0.50 | n/a | usable |
| judge-sonnet | en | 73% | 93% | 88% | 100% | 95% | 100% | 100% | 93% | 0.52 | n/a | discard |
| judge-sonnet | zh | 83% | 97% | 95% | 100% | 100% | 100% | 98% | 96% | 0.53 | n/a | discard |

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
