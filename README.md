# Roast Anything: an LLM humor benchmark for roast generation, with a validated LLM judge (English and Chinese)

**Roast Anything** measures whether a large language model can write a roast that is **funny, true, and about *this*
thing**. It is a bilingual (English + Chinese 吐槽) benchmark for computational humor with three parts that most humor
evaluations lack: **gates before taste** (a specificity test against a near-twin and a truth check against a
verified fact sheet), an **LLM-as-a-judge for humor that is validated without human raters** (seven damage tests,
plus an anchor to 250 million public New Yorker caption-contest ratings), and a **Bradley–Terry leaderboard** of
models and prompts. First results cover Claude Opus 5.5, Claude Sonnet 5.5 and Claude Haiku 5.5; GPT-5.5, Gemini
3.1 Pro, DeepSeek V4 and Qwen 3.8 are wired in and wait for OpenRouter credit.

Working log and every decision: [`CLAUDE.md`](CLAUDE.md). Design: [`docs/evaluation-design.md`](docs/evaluation-design.md).
Full report of the main run: [`runs/pilot/report.md`](runs/pilot/report.md). Leaderboard: [`runs/pilot/leaderboard.md`](runs/pilot/leaderboard.md).

## Key findings (November 2026, Claude side)

- **Claude Opus 5.5 is a usable humor judge in English and Chinese.** It passes all seven damage tests (explained
  joke, padding, politeness, softeners, generic rewrite, front-loaded punchline, false premise) at 99–100% on
  Claude-written roasts and 94–99% on other models' roasts, never prefers an explained joke, and shows no position
  bias. **Claude Sonnet 5.5 is not**: it prefers explained jokes 17–27% of the time and takes the first-shown roast
  up to three times in four.
- **The judge agrees with human crowds.** Opus picks the crowd-preferred New Yorker caption-contest caption **77%**
  of the time (GPT-4 in the literature: 67%; a judge fine-tuned on the crowd data: 82–85%) and the funnier FunLines
  headline 67% (71% at a clear crowd margin). It agreed 77% with a single human rater's 47 decisive votes on roasts.
- **The benchmark orders models by size.** On the same prompt, Opus beats Sonnet 74–85% and Sonnet beats Haiku
  74–94%, with non-overlapping intervals.
- **Prompting matters more than facts.** Among Opus prompts, a house-style comedy skill wins in both languages;
  feeding the fact sheet is neutral in English and a handicap in Chinese; aiming the roast at *the people doing the
  thing* beats roasting the thing when the target is itself a practice (70% English, 57% Chinese) and loses when the
  target is an object.
- **Facts make models tell the same joke.** Fact-fed prompts share a comic device with another prompt on 73–86% of
  items; three Claude models independently reach the same device on oat milk, NFTs, nuclear fusion and Emacs.
- **The truth gate catches invention.** Sonnet's plain English roasts fail it most (76–78% pass); on Chinese-internet
  topics plain Opus falls to 62%. The judge prefers the truthful roast in 85–90% of decided pairs where truth differs.
- **What predicts a win, for free:** truth, more sentences, fewer words per sentence, and fact density. Novelty of
  comic device does not (the shared obvious joke wins). Sentence-level **specificity depth** (how much of the roast
  would not land on the twin) spreads the arms from 0.04 (generic control) to 0.81 (fact-fed Opus) and predicts the
  judge's pick in 64–79% of decided pairs.

## Leaderboard (judge opinion, Bradley–Terry over 5,600 English and 5,200 Chinese judgements)

| arm | English score [95% CI] | Chinese score [95% CI] |
|---|---:|---:|
| skill-opus (Opus 5.5, house-style skill) | +2.03 [+1.86, +2.27] | +2.16 [+2.01, +2.33] |
| facts-opus (Opus 5.5 + fact sheet) | +1.91 [+1.71, +2.13] | +1.31 [+1.17, +1.46] |
| plain-opus (Opus 5.5) | +1.53 [+1.39, +1.73] | +1.57 [+1.45, +1.71] |
| frame-opus (Opus 5.5, roast the people doing it) | +0.95 [+0.80, +1.16] | +1.58 [+1.47, +1.72] |
| frame-sonnet (Sonnet 5.5) | +0.37 [+0.16, +0.68] | +0.80 [+0.55, +1.00] |
| plain-sonnet (Sonnet 5.5) | -0.18 [-0.52, +0.21] | +0.49 [+0.21, +0.75] |
| plain-haiku (Haiku 5.5) | -1.19 [-1.55, -0.79] | -2.34 [-2.91, -1.93] |
| frame-haiku (Haiku 5.5) | -2.17 [-2.58, -1.81] | -1.33 [-1.74, -0.97] |
| control-bland (polite critique, no jokes) | -3.24 [-4.37, -2.38] | -4.25 [-4.44, -3.99] |

A one-point gap is about a 73% win rate. These are a validated judge's preferences, not human votes; the judge's
credentials are the damage tests in `runs/pilot/report.md` and the crowd anchor above.

## How it works

1. **Targets** (`targets.jsonl`): 60 things and practices, each with a near-twin (Comic Sans vs Papyrus, PHP vs
   JavaScript, 考研 vs 国考), names in both languages, and four to five web-verified facts with sources.
2. **Arms** (`config.py`): a prompt kind × a model. Prompt kinds: plain, with fact sheet, house-style skill, people
   framing, plus a bland control (no jokes) and a generic control (no target).
3. **Gates**: `specificity.py` (masked swap test, five candidates including the twin), `depth.py` (sentence-level
   specificity depth), `truth.py` (premises vs fact sheet; exaggeration, puns and redefinitions excluded).
4. **Profile**: `agency.py` (agent-action rate: is the hit on people doing something?), `devices.py` (comic-device
   collisions across arms), length and rhythm.
5. **Judge validation**: `damage.py` (seven degradations, both orders; a judge is admitted at ≥90% and must never
   prefer an explained joke) and `external_anchor.py` (accuracy against public crowd preferences).
6. **Taste**: `build_pairs.py` + `judge_pairs.py` (blind pairwise, both orders) and `rate.html` for human raters;
   `analyze.py`, `leaderboard.py`, `pool_rank.py`, `metric_check.py` read the results.

## FAQ

**Can an LLM judge humor?** Opus 5.5 can, at the level of the best published zero-shot judges (77% on caption-contest
crowd pairs, where humans agree with each other at roughly 50–65%). Sonnet 5.5 cannot be trusted on close pairs.

**How do you validate a humor judge without human raters?** Degrade real roasts in seven known ways and check the judge
prefers the original every time; then check it against a public human-preference set. Both are in this repo and are
generic to any subjective judge.

**Is there a Chinese humor benchmark here?** Yes: every target is roasted in Chinese with native prompts, judged by a
judge validated on Chinese damage tests. There is no public Chinese humor-preference dataset, so the Chinese anchor is
the damage tests plus 100 votes from one rater.

**What does it cost?** Opus judge calls are about $0.008 each at low effort; a 250-pair pool judged both ways is about
$4. The full Claude-side run (2,080 roasts, every stage) was about $175.

## Quick start

Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```
uv sync                          # add --extra anchor for the public-dataset downloads
cp .env.example .env             # ANTHROPIC_API_KEY and/or OPENROUTER_API_KEY; .env is git-ignored
uv run python check_keys.py      # free: what each key can reach
uv run python test_common.py     # unit checks, no network
uv run python run_all.py --mock  # whole pipeline on a fake provider, zero cost
uv run python run_all.py --run pilot --smoke     # a few dollars on real models
uv run python run_all.py --run pilot --budget 40 # full run; resumes, nothing paid twice
```

Either key alone works; missing providers are skipped and reported. On Windows set `PYTHONUTF8=1`.

**Add a model**: an entry in `MODELS` and an arm in `config.py`, then `generate.py --arms <name>`, the gate stages, and
`judge_pairs.py --judges judge-opus` on a pool built with `build_pairs.py`. **Add a judge**: an entry in `JUDGES`, then
`damage.py --judges <name>`. **Add a target**: a line in `targets.jsonl` with a twin and checked facts.

## Related datasets and work

New Yorker caption contest ([Hessel et al. 2023](https://github.com/jmhessel/caption_contest_corpus); [Zhang et al.
2024, 250M ratings](https://arxiv.org/abs/2406.10522)); [Zhou et al. 2025](https://aclanthology.org/2025.findings-emnlp.884/)
(small-scale alignment lifts caption ranking to 82–85%); [SemEval-2020 Task 7 FunLines](https://zenodo.org/records/3969509);
[HumorRank](https://arxiv.org/abs/2604.19786) and [HumorGen](https://arxiv.org/abs/2604.09629) (LLM humor leaderboards);
[Chumor](https://huggingface.co/datasets/MichiganNLP/Chumor) (Chinese humor understanding).

## Citation

```bibtex
@misc{chen2026roastanything,
  title  = {Roast Anything: a roast-generation benchmark with specificity and truth gates and a damage-test-validated LLM judge},
  author = {Chen, Yuanrui},
  year   = {2026},
  url    = {https://github.com/yuanrui3/AI-benchmark-for-roasting}
}
```

## Licence

Code is MIT; targets, run data and docs are CC BY 4.0; the house-style skill and the chapters under `reference/`
are the author's, all rights reserved (see `LICENSE`). The public humour datasets fetched by `external_pairs.py` are
not included and keep their own licences.

## Limits

Generation is Claude-only until the other families run; the judge and most generators share a family, so
self-preference is bounded (at most five points across runs) but not measured. Human calibration is one rater and
two public English sets. The Chinese half of the practice-target pool is part-judged.

*Keywords: LLM humor benchmark, roast generation, computational humor, LLM-as-a-judge, humor evaluation, Chinese
humor, 吐槽, comedy writing evaluation, Claude Opus 5.5, Bradley–Terry leaderboard, New Yorker caption contest.*
