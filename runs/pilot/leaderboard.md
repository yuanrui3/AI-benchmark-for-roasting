# Leaderboard: run `pilot`, judge `judge-opus`

Bradley-Terry log-odds over every judged pool (rate (900 judgements), rate-opus (4224 judgements), rate-ladder-plain (2112 judgements), rate-ladder-frame (2111 judgements), rate-frame (180 judgements), rate-frame-en (180 judgements), rate-cn (1111 judgements)), centred on zero; a one-point gap is about a 73% win rate. 95% intervals: percentile bootstrap over pairs (200 resamples). The judge's credentials are in report.md (damage tests) and CLAUDE.md (external anchor); this is the judge's opinion, not human votes.

## en: 2811 pairs, 5622 judgements

| arm | score | 95% CI | win rate | judgements |
|---|---:|---|---:|---:|
| skill-opus | +2.03 | [+1.86, +2.27] | 0.65 | 1632 |
| facts-opus | +1.91 | [+1.71, +2.13] | 0.61 | 1626 |
| plain-opus | +1.53 | [+1.39, +1.73] | 0.61 | 2490 |
| frame-opus | +0.95 | [+0.80, +1.16] | 0.45 | 2486 |
| frame-sonnet | +0.37 | [+0.16, +0.68] | 0.64 | 704 |
| plain-sonnet | -0.18 | [-0.52, +0.21] | 0.44 | 704 |
| plain-haiku | -1.19 | [-1.55, -0.79] | 0.16 | 704 |
| frame-haiku | -2.17 | [-2.58, -1.81] | 0.06 | 704 |
| control-bland | -3.24 | [-4.37, -2.38] | 0.01 | 194 |

## zh: 2599 pairs, 5196 judgements

| arm | score | 95% CI | win rate | judgements |
|---|---:|---|---:|---:|
| skill-opus | +2.16 | [+2.01, +2.33] | 0.67 | 1440 |
| frame-opus | +1.58 | [+1.47, +1.72] | 0.59 | 2298 |
| plain-opus | +1.57 | [+1.45, +1.71] | 0.60 | 2275 |
| facts-opus | +1.31 | [+1.17, +1.46] | 0.40 | 1384 |
| frame-sonnet | +0.80 | [+0.55, +1.00] | 0.60 | 704 |
| plain-sonnet | +0.49 | [+0.21, +0.75] | 0.60 | 704 |
| frame-haiku | -1.33 | [-1.74, -0.97] | 0.08 | 703 |
| plain-haiku | -2.34 | [-2.91, -1.93] | 0.04 | 704 |
| control-bland | -4.25 | [-4.44, -3.99] | 0.00 | 180 |

