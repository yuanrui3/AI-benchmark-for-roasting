# Leaderboard: run `pilot`, judge `judge-opus`

Bradley-Terry log-odds over every judged pool (rate (900 judgements), rate-opus (4224 judgements), rate-ladder-plain (2112 judgements), rate-ladder-frame (2111 judgements), rate-frame (180 judgements), rate-frame-en (180 judgements)), centred on zero; a one-point gap is about a 73% win rate. 95% intervals: percentile bootstrap over pairs (100 resamples). The judge's credentials are in report.md (damage tests) and CLAUDE.md (external anchor); this is the judge's opinion, not human votes.

## en: 2427 pairs, 4854 judgements

| arm | score | 95% CI | win rate | judgements |
|---|---:|---|---:|---:|
| skill-opus | +1.94 | [+1.74, +2.19] | 0.63 | 1248 |
| facts-opus | +1.86 | [+1.65, +2.09] | 0.60 | 1242 |
| plain-opus | +1.71 | [+1.49, +1.93] | 0.68 | 2106 |
| frame-opus | +0.83 | [+0.67, +1.03] | 0.46 | 2102 |
| frame-sonnet | +0.26 | [-0.03, +0.57] | 0.64 | 704 |
| plain-sonnet | -0.00 | [-0.28, +0.30] | 0.44 | 704 |
| plain-haiku | -1.02 | [-1.37, -0.72] | 0.16 | 704 |
| frame-haiku | -2.29 | [-2.78, -1.88] | 0.06 | 704 |
| control-bland | -3.28 | [-4.41, -2.49] | 0.01 | 194 |

## zh: 2427 pairs, 4853 judgements

| arm | score | 95% CI | win rate | judgements |
|---|---:|---|---:|---:|
| skill-opus | +2.16 | [+1.99, +2.30] | 0.68 | 1260 |
| plain-opus | +1.58 | [+1.45, +1.71] | 0.62 | 2094 |
| frame-opus | +1.58 | [+1.46, +1.71] | 0.60 | 2135 |
| facts-opus | +1.29 | [+1.15, +1.46] | 0.40 | 1222 |
| frame-sonnet | +0.80 | [+0.48, +1.04] | 0.60 | 704 |
| plain-sonnet | +0.51 | [+0.31, +0.73] | 0.60 | 704 |
| frame-haiku | -1.33 | [-1.67, -1.01] | 0.08 | 703 |
| plain-haiku | -2.33 | [-2.80, -1.92] | 0.04 | 704 |
| control-bland | -4.25 | [-4.44, -4.05] | 0.00 | 180 |

