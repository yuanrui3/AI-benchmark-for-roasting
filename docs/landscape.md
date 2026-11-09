# Prior work (checked 9 Nov 2026)

No roast-generation benchmark was found, in English or Chinese. The rest of AI humor evaluation is lopsided:
- humor *understanding* (explaining, matching, ranking jokes) is heavily benchmarked and close to saturated;
- *generation* only got its first shared task in 2026;
- targeted humor (roasts) has only linguistics studies.

## Generation

- **SemEval-2026 Task 1, MWAHAHA.** The first shared task on general humor generation.
  - Constrained jokes in English, Spanish and Chinese, plus GIF captions, judged by arena-style pairwise human preference.
  - 37 teams took part. A Gemini 2.5 Flash baseline with simple prompts tied for first, and elaborate pipelines barely beat it, with overlapping intervals.
  - [Overview paper](https://aclanthology.org/2026.semeval-1.454/)
- **HumorRank.** A tournament leaderboard of nine models on the MWAHAHA test set, judged by LLMs grounded in humor theory and ranked with Bradley–Terry. Its two LLM judges agree with each other (Kendall τ = 0.889), but agreement between judges is not the same as validity against humans. [arXiv 2604.19786](https://arxiv.org/abs/2604.19786)
- **A SemEval team's view.** Generating candidates is easy; picking what a given audience prefers is the hard part, and results depend on the rater pool. [arXiv 2606.00022](https://arxiv.org/html/2606.00022)
- **Satire generation (EACL 2026).** LLM funniness leans on more stereotyping and toxicity, closed models included. This is relevant to any harm axis. [ACL Anthology](https://aclanthology.org/2026.eacl-long.373)

## Understanding and ranking

- **New Yorker caption contest data.**
  - Hessel et al. 2023 built the original benchmark.
  - Zhang et al. 2024 assembled over 250M ratings of 2.2M captions; current LLMs underperform top human captions. [arXiv 2406.10522](https://arxiv.org/pdf/2406.10522)
  - With small-scale human alignment, a model reached 82.4% caption-ranking accuracy, up from 67%. [Zhou et al., Findings of EMNLP 2025](https://preview.aclanthology.org/new-sigs/2025.findings-emnlp.884/)
- **HumorBench.** Explaining cartoon captions. Progress on STEM reasoning transfers to this task. [arXiv 2507.21476](https://arxiv.org/pdf/2507.21476)
- **Chumor 2.0 (弱智吧).** Chinese joke explanation. LLMs score only slightly above random and far below humans. [Findings of ACL 2025](https://preview.aclanthology.org/setup/2025.findings-acl.1122)
- **Oogiri-Master.** Japanese oogiri. Models approach human performance; surprisal and semantic distance barely predict funniness. [arXiv 2512.21494](https://www.emergentmind.com/papers/2512.21494)

## Judges and audiences

- **Who Laughs with Whom? (Oogiri voters).** User clusters disagree, some of them negatively. LLM preferences correlate weakly negatively with the overall population (GPT-5.1: −0.22) but match particular clusters. [arXiv 2601.03103](https://www.themoonlight.io/review/who-laughs-with-whom-disentangling-influential-factors-in-humor-preferences-across-user-clusters-and-llms)
- **Game-based human–LLM humor alignment.** LLMs reach only modest accuracy, with significant position bias. [arXiv 2604.08757](https://arxiv.org/html/2604.08757v1)
- **Oogiri six-dimension ratings.** Claude Sonnet 4 correlated best with humans, but overall agreement was limited. [arXiv 2511.09133](https://arxiv.org/html/2511.09133v1)

## Comedians

- **DeepMind workshops with 20 professional comedians.** Most found LLM output bland and safety-filtered, "cruise ship comedy material from the 1950s, but a bit less racist". [arXiv 2405.20956](https://arxiv.org/abs/2405.20956)

## Roasting specifically

- **r/RoastMe in linguistics.**
  - Dynel & Poppi describe it as affiliative humor in a humorous frame, with the target's consent built in. [Journal of Pragmatics 2019](https://www.sciencedirect.com/science/article/pii/S0378216618303047) · [HUMOR 2020](https://www.degruyterbrill.com/document/doi/10.1515/humor-2019-0070/html)
  - An ICWSM study analysed 12,046 RoastMe posts. [AAAI ICWSM](https://ojs.aaai.org/index.php/ICWSM/article/download/15020/14870/18539)
- **Beyond that**: hobby roast bots and generators, none evaluated.
