# Evaluation design

## What can be measured without humans

| Property | How | Trust |
|---|---|---|
| Specificity | Swap test: mask the name and aliases, then have a judge pick the target from five candidates including its near-twin. Chance is 20% (50% on the twin-only test). Add a lexical cross-check that uses no model. | High. Classification against a known answer. |
| Truth | Extract each premise and check it against the target's fact sheet. | High for things. |
| Novelty | Cluster outputs across models and samples and count collisions; match stock templates ("the X equivalent of…", "designed by someone who…"). | High. |
| Nerve | Count softeners: "no offense", "but we love you", "honestly it's great". | High, and no model needed. |
| Economy | Words per hit, against a matched rewrite. | Medium. |
| Surprise | Surprisal of the punchline given the setup. | Low. It barely predicted funniness in Oogiri data. |

Specificity and truth are gates. A roast that fails either gets no funniness score.

## Judge validation (damage tests)

Each pair below has a known right answer: the original beats the damaged version. Run both presentation orders.

1. The joke explained after the punchline.
2. A softener appended.
3. The specific detail replaced with a generic one.
4. The punchline moved to the front.
5. Padded to twice the length.
6. A false premise swapped in.
7. Rewritten as a polite critique.

Report each judge's accuracy, position bias and self-preference. Passing shows that a judge isn't broken; it doesn't show that it has taste.

## Human ratings

- **Who**: the owner plus one or two friends.
- **Task**: blind pairwise, with options left / right / both bad / skip, and a separate "crosses a line" flag.
- **Volume**: about 300–500 votes for the preflight, with every rater rating the same overlapping set so agreement can be computed.
- **Reporting**: a single-rater ranking is legitimate if it is labelled "funny to this rater, with this stated taste" (see `rater-card.md`). Report the LLM judge's ranking next to it, with its agreement rate against the humans.

## Scaling human data without money

Precedents for free annotation at scale:

- the New Yorker caption contest's ratings, where the contest itself was the incentive;
- AI21's "Human or Not", with over 1.5M users and 10M conversations in its first month and no reward ([arXiv 2305.20010](https://ar5iv.labs.arxiv.org/html/2305.20010));
- arena-style voting.

**Game design:**

- A roast battle of two roasts of one target where the player picks the harder hit. The vote is the fun.
- Serve a fixed pre-generated pool so votes cost nothing. Live generation costs money per call.
- Main risks:
  - cold start: there are no players without a distribution channel;
  - self-selected players: report results as audience-conditioned;
  - bots and random clickers: use gold pairs, which double as a check that the measurement tells bad from good;
  - abuse: limit targets to things, or to a verified self.
- If game votes are used to train Roast Anything, keep a frozen held-out set that is never trained on.

**Social media, by mode:**

- **Mining upvotes** on human roasts (r/RoastMe, Bilibili, Douyin): weak labels at best.
  - They score humans, not models.
  - Upvotes herd: one early upvote raised final ratings by 25% on average in a randomized experiment. ([Muchnik et al. 2013](https://pubmed.ncbi.nlm.nih.gov/23929980/))
  - Platform terms and real people's photos apply.
- **Covertly posting AI content: never.**
  - University of Zurich researchers posted over 1,000 undisclosed AI comments on r/changemyview.
  - Reddit sent formal legal demands, and the researchers chose not to publish. ([NBC News](https://www.nbcnews.com/news/rcna203597))
- **A disclosed AI account running polls: viable**, as the game's distribution channel.
  - You get only aggregate counts and no per-rater data.
  - The platform's algorithm decides which polls get reach.
  - Label AI content: China requires labels on AI-generated content (since September 2025), and EU AI Act transparency rules apply from August 2026.
  - Not legal advice; check each platform's automation rules.

If results will be published from a university, get an ethics-review exemption before collecting any data.

## Revisions after the pilot (9 Nov 2026)

What the first real data showed (two smoke runs and `runs/pilot-or`: four non-Claude plain arms, two judges, the owner's 100 Chinese votes):

- **Specificity is at ceiling for frontier plain arms**: 100% on the swap test (k = 5) while the generic control sits at twin-chance. The gate separates generic from specific; it does not separate models. Harder distractors or a sentence-level test (hit density: how many sentences identify the target on their own) are needed before it ranks anything.
- **Truth works once the judge lists the premises a joke relies on**, not the comic exaggeration itself, and ignores puns and redefinitions used as punchlines ("UGG isn't a brand, it's the sound your feet make").
- **Judges**: GPT-5.5 at low effort passes the damage tests (93%); DeepSeek V4 Pro passes in Chinese; both agree with the one human rater only 57–63% on twenty pairs, which is not yet a verdict either way. Both see the fact sheet, as the raters do, and are told that invented facts and self-explanation count against a roast.
- **Human rating is slow to resolve close arms**: 52 decisive votes gave interval widths of 1.3 log-odds; about 336 are needed for 0.5. 36% of pairs were "both bad". The owner dropped English (boring or opaque to a non-insider). Human votes are therefore the anchor and the instrument for large effects (framings, target families), not for ranking frontier models against each other.
- **A roast is about someone doing something.** Every top-voted roast had an agent and an action (paying for durian and getting pricked while the neighbours suspect the drain; seeing snow and panicking for the UGG suede); roasts that stayed on the object read as description. Targets are re-verbalised as practices (`practice` / `practice_zh` in targets.jsonl), a framing arm roasts the practice and aims at the people doing it, and an agent-action rate (share of sentences whose hit is someone doing something) joins the profile. The framing test (plain-X vs frame-X, same model and target, the owner's votes) is the first experiment sized for human votes: a two-to-one effect shows in 40 pairs.

Measurement plan from here, cheapest layer first:

| Layer | Needs | Examples |
|---|---|---|
| Free | nothing | softeners, stock templates, length and rhythm, token collisions, keyword agent rate (`agency.py --rule`), per-target both-bad and skip rates from the votes |
| Judge | API calls, validated by the damage tests | swap test, truth, agent-action rate (`agency.py`), comic-device collisions (`devices.py`), pairwise judge tournaments |
| Human | the owner and friends, Chinese | framing and target-family effects, gold checks, the anchor that judge agreement is measured against |

A metric earns a place in the headline profile only if it moves in the direction the human votes move on the pairs where both exist.

## Revisions after the Claude-side run (11 Nov 2026)

- **The judge layer has a validated judge.** Opus 5.5 at low effort passes the damage tests in both languages on Claude-written and non-Claude roasts alike (94-100% per language and run, explain 100%, no position bias, 100% on gold pairs). Sonnet 5.5 does not (it prefers an explained joke in 17-27% of cases and takes the first-shown roast three times in four on same-model pairs). So pairwise judging is no longer human-only: Opus can rank arms, models and prompts over thousands of pairs for cents, and human votes are spent where they are irreplaceable.
- **Human votes are a reference, not a golden rule** (owner, 11 Nov 2026). Judge-human agreement (Opus 77% on the owner's 47 decisive pilot-or votes) is reported as calibration; nothing is tuned to one rater. The last rule above now reads: a metric earns its place if it moves with a validated judge over many pairs, or with several raters who agree with each other; a single rater's votes rank arms indicatively and anchor nothing on their own.
- **A model-size ladder is the validity check.** Sonnet 5.5 and Haiku 5.5 generate on the plain and framed prompts next to Opus 5.5. A judge or a metric that cannot put Opus above Haiku on the same prompt is not measuring quality; one that orders them is allowed to be read on the prompt comparisons. Results in CLAUDE.md, Early observations.
- **Labellers agree with each other.** Opus and Sonnet agent-action labels correlate at 0.89 item by item and both put every model's framed arm above its plain arm in all 132 target-model cells; the keyword rule correlates at 0.3 and is a free screen only. Truth verdicts agree on 92% of items (Opus the more lenient). Device grouping by Opus has no parse failures and shows the first cross-model attractors once three Claude models are in the same cell.
- **The judge has a public human anchor** (11 Nov 2026, late). With the owner no longer rating, judge-human agreement is measured on public crowd-preference sets instead: Opus 5.5 picks the crowd-preferred New Yorker caption 77% of the time (GPT-4 in the literature 67%, a judge fine-tuned on the crowd data 82-85%) and the funnier edited headline 67% (71% at a clear crowd margin); Sonnet 65% and 59% with heavy position bias. The anchor vouches for taste in English caption and headline humor; the damage tests vouch for discipline on roasts; Chinese has no public preference set and rests on the damage tests and the owner's 100 votes. A LoRA judge fine-tuned on the caption preferences is the known route to the 82-85% level, in English only.
- **A Chinese human anchor exists after all** (12 Nov 2026). The house style's source, the stand-up script 《人比AI更像AI》, comes with the owner's 0-10 scores on 379 of its punchlines and a per-paragraph attribution map (private data, analysed in `ext-data/renbi/`). One rater who co-wrote the material, so calibration and not ground truth; but it is Chinese, it is material the rater cares about, and the scores drove real edits (deleted lines 5.8 against 7.9 kept). `rated_pairs.py` makes pairs at least two points apart for `external_anchor.py --lang zh`; the deleted-line-versus-rewrite pairs are a small human-edited gold set. Free findings: authorship (human or AI share) does not predict the score, no surface feature does, and the section a line belongs to explains a fifth of the variance, so what a joke is about matters more than how it is built.
