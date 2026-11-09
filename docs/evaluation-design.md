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
