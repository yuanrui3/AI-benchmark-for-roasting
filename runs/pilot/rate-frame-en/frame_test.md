# Framing test: run `pilot`, pool `rate-frame-en`

100 pairs in the pool (90 framing pairs, 10 gold).

_No human votes yet. Rate rate-frame-en/index.html and drop the exports into votes-frame-en/._

## Judge votes (both orders)

| group | framed wins | plain wins | both bad | skipped | framed share | 95% CI | p (vs 50%) |
|---|---:|---:|---:|---:|---:|---|---:|
| judge-opus | 55 | 125 | 0 | 0 | 31% | [24%, 38%] | 0.000 |
| judge-sonnet | 58 | 122 | 0 | 0 | 32% | [26%, 39%] | 0.000 |
| **all** | 113 | 247 | 0 | 0 | 31% | [27%, 36%] | 0.000 |
- judge-opus: order-inconsistent on 15 of 90 pairs
- judge-sonnet: order-inconsistent on 52 of 90 pairs

## Agent-action rate (agency.jsonl)

| labeller | framing | lang | items | mean agent rate |
|---|---|---|---:|---:|
| judge-sonnet | frame | en | 88 | 0.84 |
| judge-sonnet | plain | en | 85 | 0.34 |
| rule | frame | en | 88 | 0.21 |
| rule | plain | en | 88 | 0.14 |
