# Framing test: run `pilot`, pool `rate-frame`

100 pairs in the pool (90 framing pairs, 10 gold).

_No human votes yet. Rate rate-frame/index.html and drop the exports into votes-frame/._

## Judge votes (both orders)

| group | framed wins | plain wins | both bad | skipped | framed share | 95% CI | p (vs 50%) |
|---|---:|---:|---:|---:|---:|---|---:|
| judge-opus | 95 | 85 | 0 | 0 | 53% | [46%, 60%] | 0.502 |
| judge-sonnet | 72 | 108 | 0 | 0 | 40% | [33%, 47%] | 0.009 |
| **all** | 167 | 193 | 0 | 0 | 46% | [41%, 52%] | 0.188 |
- judge-opus: order-inconsistent on 19 of 90 pairs
- judge-sonnet: order-inconsistent on 50 of 90 pairs

## Agent-action rate (agency.jsonl)

| labeller | framing | lang | items | mean agent rate |
|---|---|---|---:|---:|
| judge-sonnet | frame | zh | 88 | 0.74 |
| judge-sonnet | plain | zh | 88 | 0.35 |
| rule | frame | zh | 88 | 0.15 |
| rule | plain | zh | 88 | 0.07 |
