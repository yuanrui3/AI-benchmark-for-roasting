# Preflight report: run `pilot`

Generated 2026-11-11T18:47:44+00:00. Gates were fixed before data was seen (CLAUDE.md).

## Generation

| arm | lang | items | refused | errors | mean words | cost $ |
|---|---|---:|---:|---:|---:|---:|
| plain-opus | en | 88 | 0 | 0 | 140.1 | 1.34 |
| plain-opus | zh | 88 | 0 | 0 | 206.0 | 1.51 |
| facts-opus | en | 88 | 0 | 0 | 139.3 | 1.68 |
| facts-opus | zh | 88 | 0 | 0 | 200.5 | 1.86 |
| skill-opus | en | 88 | 0 | 0 | 136.9 | 2.68 |
| skill-opus | zh | 88 | 0 | 0 | 188.1 | 2.80 |
| frame-opus | en | 88 | 0 | 0 | 137.6 | 1.51 |
| frame-opus | zh | 88 | 0 | 0 | 200.4 | 1.59 |
| control-bland | en | 88 | 0 | 0 | 149.5 | 0.29 |
| control-bland | zh | 88 | 0 | 0 | 274.8 | 0.57 |
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
| plain-opus | en | 0.00 | 0.03 | 0% | 10.1 | 37% | 34% | 14% |
| facts-opus | en | 0.00 | 0.02 | 32% | 9.0 | 45% | 36% | 11% |
| skill-opus | en | 0.00 | 0.05 | 31% | 6.2 | 47% | 44% | 7% |
| frame-opus | en | 0.00 | 0.05 | 0% | 10.7 | 88% | 84% | 21% |
| control-bland | en | 0.00 | 0.02 | 0% | 14.8 | 22% | 21% | 12% |
| control-generic | en | 0.00 | 0.06 | 0% | 10.4 | 49% | 48% | 16% |
| plain-sonnet | en | 0.00 | 0.10 | 0% | 10.3 | 39% | 36% | 15% |
| plain-haiku | en | 0.00 | 0.09 | 0% | 12.1 | 38% | 39% | 16% |
| frame-sonnet | en | 0.00 | 0.05 | 0% | 11.2 | 90% | 87% | 20% |
| frame-haiku | en | 0.00 | 0.05 | 0% | 12.3 | 91% | 92% | 22% |
| plain-opus | zh | 0.00 | 0.01 | 0% | 15.2 | 35% | 35% | 7% |
| facts-opus | zh | 0.00 | 0.05 | 2% | 14.9 | 43% | 36% | 8% |
| skill-opus | zh | 0.00 | 0.10 | 2% | 12.4 | 43% | 37% | 7% |
| frame-opus | zh | 0.01 | 0.01 | 0% | 15.7 | 77% | 74% | 15% |
| control-bland | zh | 0.00 | 0.02 | 0% | 28.1 | 6% | 10% | 13% |
| control-generic | zh | 0.00 | 0.05 | 0% | 16.2 | 53% | 51% | 12% |
| plain-sonnet | zh | 0.00 | 0.03 | 0% | 15.9 | 37% | 36% | 9% |
| plain-haiku | zh | 0.00 | 0.02 | 0% | 18.8 | 28% | 29% | 8% |
| frame-sonnet | zh | 0.00 | 0.02 | 0% | 16.4 | 77% | 72% | 18% |
| frame-haiku | zh | 0.00 | 0.01 | 0% | 18.3 | 77% | 73% | 19% |

## Novelty (comic device)

One judge call per target and language groups that target's roasts by the image or angle each is built on (devices.py). Cross-arm = share of an arm's items whose device another arm also used on the same target; self-repeat = the arm's own samples share a device. Attractors are devices three or more arms reached on their own.

| arm | lang | items | cross-arm | self-repeat |
|---|---|---:|---:|---:|
| plain-opus | en | 176 | 33% | 76% |
| plain-opus | zh | 176 | 35% | 73% |
| facts-opus | en | 176 | 73% | 89% |
| facts-opus | zh | 176 | 73% | 92% |
| skill-opus | en | 176 | 62% | 83% |
| skill-opus | zh | 176 | 68% | 82% |
| plain-sonnet | en | 88 | 41% | 61% |
| plain-sonnet | zh | 88 | 51% | 64% |
| plain-haiku | en | 88 | 32% | 57% |
| plain-haiku | zh | 88 | 27% | 59% |

Attractors:

- 4 arms, oat-milk (zh): 燕麦奶就是粥汤
- 4 arms, nfts (en): You bought a receipt, not art
- 3 arms, vision-pro (zh): 假眼装作在听
- 3 arms, vim (en): Vim users as hostages/captives
- 3 arms, slack (zh): 绿点监视与正在输入煎熬
- 3 arms, slack (en): Failed video game spawned the chat app
- 3 arms, risk (en): Endless game ends in hostage situation
- 3 arms, pmma (zh): 博士生就是光刻胶
- 3 arms, pmma (zh): PMMA就是被用的博士生
- 3 arms, nfts (zh): 右键另存为买个链接
- 3 arms, microsoft-word (en): Everyday formatting frustrations list
- 3 arms, microsoft-teams (zh): 状态灯绿黄告密

## Specificity gate (masked swap test, k=5)

Chance 20%; twin-only chance 50%. Pooled over judges.

| arm | lang | n | picked target | target vs twin | residual leak | lexical contrast |
|---|---|---:|---:|---:|---:|---:|
| plain-opus | en | 87 | 100% | 100% | 0% | 0.045 |
| plain-opus | zh | 88 | 100% | 100% | 0% | 0.001 |
| facts-opus | en | 86 | 99% | 100% | 0% | 0.218 |
| facts-opus | zh | 88 | 100% | 100% | 0% | 0.007 |
| skill-opus | en | 87 | 99% | 100% | 0% | 0.182 |
| skill-opus | zh | 88 | 100% | 100% | 0% | 0.006 |
| frame-opus | en | 88 | 98% | 100% | 0% | 0.021 |
| frame-opus | zh | 88 | 100% | 100% | 0% | 0.001 |
| control-bland | en | 88 | 100% | 100% | 0% | 0.022 |
| control-bland | zh | 88 | 100% | 100% | 0% | 0.001 |
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

An item fails only on a contradicted premise; facts absent from the sheet do not count against it.

| arm | lang | n | pass | claims/item | contradicted/item | absent/item |
|---|---|---:|---:|---:|---:|---:|
| plain-opus | en | 176 | 88% | 9.79 | 0.12 | 5.56 |
| plain-opus | zh | 176 | 92% | 7.12 | 0.09 | 4.22 |
| facts-opus | en | 176 | 96% | 9.33 | 0.04 | 0.48 |
| facts-opus | zh | 176 | 96% | 8.98 | 0.04 | 0.45 |
| skill-opus | en | 176 | 95% | 9.95 | 0.05 | 1.22 |
| skill-opus | zh | 176 | 97% | 9.54 | 0.03 | 1.23 |
| frame-opus | en | 176 | 95% | 7.3 | 0.06 | 4.23 |
| frame-opus | zh | 176 | 93% | 6.88 | 0.07 | 4.1 |
| control-bland | en | 176 | 99% | 9.19 | 0.01 | 6.31 |
| control-bland | zh | 175 | 97% | 8.86 | 0.03 | 5.93 |
| plain-sonnet | en | 176 | 77% | 8.49 | 0.27 | 4.69 |
| plain-sonnet | zh | 175 | 92% | 6.56 | 0.09 | 3.48 |
| plain-haiku | en | 176 | 87% | 6.57 | 0.14 | 3.56 |
| plain-haiku | zh | 176 | 90% | 5.4 | 0.1 | 3.08 |
| frame-sonnet | en | 176 | 96% | 6.38 | 0.05 | 3.8 |
| frame-sonnet | zh | 176 | 90% | 6.37 | 0.1 | 3.81 |
| frame-haiku | en | 176 | 93% | 5.21 | 0.07 | 2.95 |
| frame-haiku | zh | 176 | 92% | 5.65 | 0.09 | 3.39 |

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
