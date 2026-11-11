# Preflight report: run `claude-smoke`

Generated 2026-11-11T06:36:45+00:00. Gates were fixed before data was seen (CLAUDE.md).

## Generation

| arm | lang | items | refused | errors | mean words | cost $ |
|---|---|---:|---:|---:|---:|---:|
| plain-opus | en | 4 | 0 | 0 | 147.5 | 0.05 |
| plain-opus | zh | 4 | 0 | 0 | 202.2 | 0.07 |
| facts-opus | en | 4 | 0 | 0 | 135.8 | 0.09 |
| facts-opus | zh | 4 | 0 | 0 | 192.2 | 0.09 |
| skill-opus | en | 4 | 0 | 0 | 136.2 | 0.13 |
| skill-opus | zh | 4 | 0 | 0 | 198.2 | 0.12 |
| frame-opus | en | 4 | 0 | 0 | 141.5 | 0.08 |
| frame-opus | zh | 4 | 0 | 0 | 196.0 | 0.08 |
| control-bland | en | 4 | 0 | 0 | 151.0 | 0.01 |
| control-bland | zh | 4 | 0 | 0 | 293.8 | 0.02 |
| control-generic | en | 4 | 0 | 0 | 158.5 | 0.02 |
| control-generic | zh | 4 | 0 | 0 | 226.8 | 0.04 |

## Profile

Nerve = softeners per item (lower is braver). Novelty = share of items whose text collides (token Jaccard > 0.3) with another arm's item on the same target, plus stock-template hits. Economy = words per sentence. Agent-action = share of a roast's lines whose hit is someone doing something rather than a property of the object (agency.py; one column per labeller: a judge model, or `rule`, the free keyword rule; n/a until it has run). The other columns need no model.

| arm | lang | softeners/item | stock hits/item | collision rate | words/sentence | agent-action (judge-sonnet) |
|---|---|---:|---:|---:|---:|---:|
| plain-opus | en | 0.00 | 0.00 | 0% | 11.1 | 43% |
| facts-opus | en | 0.00 | 0.25 | 0% | 8.6 | 43% |
| skill-opus | en | 0.00 | 0.25 | 0% | 6.9 | 44% |
| frame-opus | en | 0.00 | 0.00 | 0% | 9.8 | 85% |
| control-bland | en | 0.00 | 0.00 | 0% | 15.1 | 29% |
| control-generic | en | 0.00 | 0.00 | 0% | 9.9 | 60% |
| plain-opus | zh | 0.00 | 0.00 | 0% | 16.5 | 40% |
| facts-opus | zh | 0.00 | 0.00 | 0% | 15.1 | 45% |
| skill-opus | zh | 0.00 | 0.25 | 0% | 13.0 | 40% |
| frame-opus | zh | 0.00 | 0.00 | 0% | 19.1 | 77% |
| control-bland | zh | 0.00 | 0.00 | 0% | 27.3 | 20% |
| control-generic | zh | 0.00 | 0.00 | 0% | 17.1 | 54% |

## Novelty (comic device)

One judge call per target and language groups that target's roasts by the image or angle each is built on (devices.py). Cross-arm = share of an arm's items whose device another arm also used on the same target; self-repeat = the arm's own samples share a device. Attractors are devices three or more arms reached on their own.

| arm | lang | items | cross-arm | self-repeat |
|---|---|---:|---:|---:|
| plain-opus | en | 4 | 50% | 0% |
| plain-opus | zh | 4 | 25% | 0% |
| facts-opus | en | 4 | 100% | 0% |
| facts-opus | zh | 4 | 75% | 0% |
| skill-opus | en | 4 | 75% | 0% |
| skill-opus | zh | 4 | 75% | 0% |

Attractors:

- 3 arms, crocs (zh): 先卖洞再卖堵洞挂件
- 3 arms, comic-sans (en): Gritty Watchmen inspiration versus silly result

## Specificity gate (masked swap test, k=5)

Chance 20%; twin-only chance 50%. Pooled over judges.

| arm | lang | n | picked target | target vs twin | residual leak | lexical contrast |
|---|---|---:|---:|---:|---:|---:|
| plain-opus | en | 4 | 100% | 100% | 0% | 0.047 |
| plain-opus | zh | 4 | 100% | 100% | 0% | 0.000 |
| facts-opus | en | 4 | 100% | 100% | 0% | 0.276 |
| facts-opus | zh | 4 | 100% | 100% | 0% | 0.008 |
| skill-opus | en | 4 | 100% | 100% | 0% | 0.227 |
| skill-opus | zh | 4 | 100% | 100% | 0% | 0.004 |
| frame-opus | en | 4 | 100% | 100% | 0% | 0.014 |
| frame-opus | zh | 4 | 100% | 100% | 0% | 0.000 |
| control-bland | en | 4 | 100% | 100% | 0% | 0.005 |
| control-bland | zh | 4 | 100% | 100% | 0% | 0.001 |
| control-generic | en | 4 | 75% | 75% | 0% | -0.005 |
| control-generic | zh | 4 | 100% | 100% | 0% | 0.000 |

Specificity varies across arms (range >= 15 points, some arm < 90%): **False**. Generic control near chance on the twin test: **False**.

## Truth gate

An item fails only on a contradicted premise; facts absent from the sheet do not count against it.

| arm | lang | n | pass | claims/item | contradicted/item | absent/item |
|---|---|---:|---:|---:|---:|---:|
| plain-opus | en | 4 | 75% | 9.5 | 0.25 | 5.5 |
| plain-opus | zh | 4 | 100% | 7.5 | 0.0 | 5.25 |
| facts-opus | en | 4 | 100% | 9.75 | 0.0 | 0.75 |
| facts-opus | zh | 4 | 100% | 10.0 | 0.0 | 0.5 |
| skill-opus | en | 4 | 100% | 9.75 | 0.0 | 1.25 |
| skill-opus | zh | 4 | 100% | 10.5 | 0.0 | 1.75 |
| frame-opus | en | 4 | 100% | 5.5 | 0.0 | 4.0 |
| frame-opus | zh | 4 | 100% | 6.25 | 0.0 | 4.25 |
| control-bland | en | 4 | 100% | 9.0 | 0.0 | 7.5 |
| control-bland | zh | 4 | 100% | 9.0 | 0.0 | 7.25 |

## Judge validation (damage tests)

A usable judge prefers the original >= 90% of the time and never prefers an explained joke. P(first) is position bias (0.5 is none). Self-pref = accuracy on its own family's roasts minus others'.

| judge | lang | explain | false | frontload | generic | pad | polite | softener | overall | P(first) | self-pref | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| judge-sonnet | en | 50% | 92% | 100% | 100% | 100% | 100% | 100% | 92% | 0.51 | n/a | discard |
| judge-sonnet | zh | 100% | 100% | 83% | 100% | 100% | 100% | 100% | 98% | 0.52 | n/a | usable |

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
