# Preflight report: run `pilot`

Generated 2026-11-11T08:03:29+00:00. Gates were fixed before data was seen (CLAUDE.md).

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

## Profile

Nerve = softeners per item (lower is braver). Novelty = share of items whose text collides (token Jaccard > 0.3) with another arm's item on the same target, plus stock-template hits. Economy = words per sentence. Agent-action = share of a roast's lines whose hit is someone doing something rather than a property of the object (agency.py; one column per labeller: a judge model, or `rule`, the free keyword rule; n/a until it has run). The other columns need no model.

| arm | lang | softeners/item | stock hits/item | collision rate | words/sentence | agent-action (judge-sonnet) | agent-action (rule) |
|---|---|---:|---:|---:|---:|---:|---:|
| plain-opus | en | 0.00 | 0.03 | 0% | 10.1 | 34% | 14% |
| facts-opus | en | 0.00 | 0.02 | 32% | 9.0 | 36% | 11% |
| skill-opus | en | 0.00 | 0.05 | 31% | 6.2 | 44% | 7% |
| frame-opus | en | 0.00 | 0.05 | 0% | 10.7 | 84% | 21% |
| control-bland | en | 0.00 | 0.02 | 0% | 14.8 | 21% | 12% |
| control-generic | en | 0.00 | 0.06 | 0% | 10.4 | 48% | 16% |
| plain-opus | zh | 0.00 | 0.01 | 0% | 15.2 | 35% | 7% |
| facts-opus | zh | 0.00 | 0.05 | 2% | 14.9 | 36% | 8% |
| skill-opus | zh | 0.00 | 0.10 | 2% | 12.4 | 37% | 7% |
| frame-opus | zh | 0.01 | 0.01 | 0% | 15.7 | 74% | 15% |
| control-bland | zh | 0.00 | 0.02 | 0% | 28.1 | 10% | 13% |
| control-generic | zh | 0.00 | 0.05 | 0% | 16.2 | 51% | 12% |

## Novelty (comic device)

One judge call per target and language groups that target's roasts by the image or angle each is built on (devices.py). Cross-arm = share of an arm's items whose device another arm also used on the same target; self-repeat = the arm's own samples share a device. Attractors are devices three or more arms reached on their own.

| arm | lang | items | cross-arm | self-repeat |
|---|---|---:|---:|---:|
| plain-opus | en | 88 | 22% | 84% |
| plain-opus | zh | 88 | 18% | 80% |
| facts-opus | en | 88 | 73% | 86% |
| facts-opus | zh | 88 | 72% | 89% |
| skill-opus | en | 88 | 58% | 75% |
| skill-opus | zh | 88 | 60% | 70% |

Attractors:

- 3 arms, vim (en): Vim users as hostages/captives
- 3 arms, pmma (zh): 博士生就是光刻胶
- 3 arms, luosifen (zh): 螺蛳背锅酸笋干活
- 3 arms, keurig (zh): 发明人后悔亲爹不认
- 3 arms, beanie-babies (en): Beanie Babies as a fake retirement plan

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

Specificity varies across arms (range >= 15 points, some arm < 90%): **False**. Generic control near chance on the twin test: **True**.

## Truth gate

An item fails only on a contradicted premise; facts absent from the sheet do not count against it.

| arm | lang | n | pass | claims/item | contradicted/item | absent/item |
|---|---|---:|---:|---:|---:|---:|
| plain-opus | en | 88 | 85% | 10.18 | 0.15 | 5.82 |
| plain-opus | zh | 88 | 91% | 8.11 | 0.1 | 4.88 |
| facts-opus | en | 88 | 97% | 10.17 | 0.03 | 0.74 |
| facts-opus | zh | 88 | 93% | 10.5 | 0.07 | 0.69 |
| skill-opus | en | 88 | 92% | 10.85 | 0.08 | 1.51 |
| skill-opus | zh | 88 | 97% | 11.19 | 0.03 | 1.7 |
| frame-opus | en | 88 | 94% | 7.59 | 0.07 | 4.43 |
| frame-opus | zh | 88 | 92% | 7.82 | 0.08 | 4.7 |
| control-bland | en | 88 | 99% | 9.36 | 0.01 | 6.48 |
| control-bland | zh | 88 | 97% | 9.39 | 0.03 | 6.23 |

## Judge validation (damage tests)

A usable judge prefers the original >= 90% of the time and never prefers an explained joke. P(first) is position bias (0.5 is none). Self-pref = accuracy on its own family's roasts minus others'.

| judge | lang | explain | false | frontload | generic | pad | polite | softener | overall | P(first) | self-pref | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
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
| a judge is usable (>= 90% damage, never prefers explained) | FAIL |

**Verdict: no verdict yet (human data missing); benchmark stays human-rated (no judge passed)**
