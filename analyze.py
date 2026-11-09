"""Analyze a run: gates, profile, Bradley-Terry rankings, agreement, projection, report.

    uv run python analyze.py --run pilot

Reads whatever exists under runs/<run>/: items.jsonl, specificity.jsonl, truth.jsonl,
damage.jsonl, rate/pairs.json, judge_pairs.jsonl and runs/<run>/votes/*.json (the
files raters export from rate.html). Missing pieces are reported as missing, not
faked. Writes runs/<run>/report.md and runs/<run>/summary.json.

Go/no-go gates (fixed in CLAUDE.md before any data was seen):
  controls behave   bland control below every real arm; generic control near chance on the twin test
  spread            at least two arms with non-overlapping 95% CIs on human votes
  raters agree      pairwise agreement >= 0.6, ties excluded
  specificity varies differs across arms and is below ceiling for at least one
  judge usable      >= 90% on damage tests and never prefers an explained joke
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from common import ROOT, count_words, jaccard, read_jsonl, tokens, utf8_stdout

SOFTENERS = {
    "en": [r"\bno offen[cs]e\b", r"\bbut (?:we|i) (?:still )?love\b", r"\bhonestly,? (?:it'?s|it is) (?:great|fine|good)\b",
           r"\bjokes? aside\b", r"\bin all seriousness\b", r"\bto be fair\b", r"\bjust kidding\b", r"\bjk\b",
           r"\bdon'?t get me wrong\b", r"\bI'?m (?:only|just) (?:joking|kidding)\b", r"\bwith (?:all due )?respect\b"],
    "zh": [r"开个玩笑", r"别介意", r"无意冒犯", r"说实话.{0,6}(?:挺好|不错)", r"其实.{0,6}(?:挺好|不错|也没)", r"玩笑归玩笑",
           r"认真(?:地)?说", r"不是针对", r"没有恶意", r"开玩笑的"],
}
STOCK = {
    "en": [r"\bthe \w+ equivalent of\b", r"\bdesigned by someone who\b", r"\bclown at a funeral\b", r"\blooks like (?:a|the)\b.*\bhad a baby\b",
           r"\bparticipation trophy\b", r"\bheld together (?:with|by) duct tape\b", r"\bthe \w+ of \w+s\b"],
    "zh": [r"界的\w+", r"\w+版的\w+", r"像是\w+生的孩子", r"小丑", r"参与奖"],
}
COLLISION_J = 0.30


# ---------------- Bradley-Terry ----------------

def bt_fit(wins: dict[tuple[str, str], int], arms: list[str], prior: float = 0.5, iters: int = 300) -> dict[str, float]:
    """MM algorithm (Hunter 2004) with a symmetric pseudo-count prior. Returns centered log-strengths."""
    p = {a: 1.0 for a in arms}
    W = {a: sum(wins.get((a, b), 0) for b in arms if b != a) + prior * (len(arms) - 1) for a in arms}
    n = {(a, b): wins.get((a, b), 0) + wins.get((b, a), 0) + 2 * prior for a in arms for b in arms if a != b}
    for _ in range(iters):
        new = {}
        for a in arms:
            denom = sum(n[(a, b)] / (p[a] + p[b]) for b in arms if b != a)
            new[a] = W[a] / denom if denom > 0 else p[a]
        g = math.exp(sum(math.log(v) for v in new.values()) / len(new))
        p = {a: v / g for a, v in new.items()}
    return {a: math.log(v) for a, v in p.items()}


def bt_with_ci(decisions: list[tuple[str, str]], arms: list[str], boots: int = 500, seed: int = 1) -> dict[str, dict]:
    """decisions: (winner_arm, loser_arm). Returns per arm: score, lo, hi, n."""
    if not decisions:
        return {}
    wins = Counter(decisions)
    point = bt_fit(wins, arms)
    rng = random.Random(seed)
    samples = defaultdict(list)
    for _ in range(boots):
        resampled = Counter(rng.choice(decisions) for _ in decisions)
        fit = bt_fit(resampled, arms, iters=120)
        for a in arms:
            samples[a].append(fit[a])
    out = {}
    counts = Counter(w for w, _ in decisions) + Counter(l for _, l in decisions)
    for a in arms:
        s = sorted(samples[a])
        out[a] = {"score": round(point[a], 3), "lo": round(s[int(0.025 * boots)], 3), "hi": round(s[int(0.975 * boots) - 1], 3),
                  "n": counts[a]}
    return out


# ---------------- loading ----------------

def load_votes(run_dir: Path) -> list[dict]:
    rows = []
    for f in sorted(glob.glob(str(run_dir / "votes" / "*.json"))):
        try:
            d = json.loads(Path(f).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        rater = (d.get("rater") or {}).get("name") or Path(f).stem
        for v in d.get("votes", []):
            rows.append({**v, "rater": rater, "lang": d.get("lang"), "file": Path(f).name})
    return rows


def vote_winner(v: dict, pair: dict) -> str | None:
    """Return 'a' / 'b' for decisive votes, None for both_bad/skip."""
    if v["choice"] == "left":
        return "a" if v["left_item"] == pair["a"]["item_id"] else "b"
    if v["choice"] == "right":
        return "a" if v["right_item"] == pair["a"]["item_id"] else "b"
    return None


def fmt_pct(x) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.0f}%"


# ---------------- main ----------------

def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--boots", type=int, default=500)
    args = ap.parse_args()
    run_dir = ROOT / "runs" / args.run
    items = read_jsonl(run_dir / "items.jsonl")
    by_item = {r["item_id"]: r for r in items}
    arm_of = lambda iid: by_item[iid.split("~")[0]]["arm"] if iid.split("~")[0] in by_item else None  # noqa: E731
    langs = sorted({r["lang"] for r in items})
    arms = [a for a in dict.fromkeys(r["arm"] for r in items)]
    real_arms = [a for a in arms if not a.startswith("control-")]
    S: dict = {"run": args.run, "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "langs": langs, "arms": arms}
    md = [f"# Preflight report: run `{args.run}`", "", f"Generated {S['generated']}. Gates were fixed before data was seen (CLAUDE.md).", ""]

    # ---- generation summary ----
    md += ["## Generation", "", "| arm | lang | items | refused | errors | mean words | cost $ |", "|---|---|---:|---:|---:|---:|---:|"]
    gen = {}
    for a in arms:
        for lang in langs:
            rs = [r for r in items if r["arm"] == a and r["lang"] == lang]
            if not rs:
                continue
            ok = [r for r in rs if not r["refused"] and not r["error"]]
            words = [count_words(r["text"], lang) for r in ok]
            gen[f"{a}|{lang}"] = {"n": len(rs), "refused": sum(r["refused"] for r in rs), "errors": sum(bool(r["error"]) for r in rs),
                                  "mean_words": round(sum(words) / len(words), 1) if words else None,
                                  "cost": round(sum(r["cost_usd"] for r in rs), 3)}
            g = gen[f"{a}|{lang}"]
            md.append(f"| {a} | {lang} | {g['n']} | {g['refused']} | {g['errors']} | {g['mean_words']} | {g['cost']:.2f} |")
    S["generation"] = gen
    md.append("")

    # ---- profile: nerve, novelty, economy ----
    md += ["## Profile (no model needed)", "", "Nerve = softeners per item (lower is braver). Novelty = share of items whose text collides "
           f"(token Jaccard > {COLLISION_J}) with another arm's item on the same target, plus stock-template hits. Economy = words per sentence.", "",
           "| arm | lang | softeners/item | stock hits/item | collision rate | words/sentence |", "|---|---|---:|---:|---:|---:|"]
    prof = {}
    toks = {r["item_id"]: tokens(r["text"]) for r in items if r["text"]}
    for lang in langs:
        same_target = defaultdict(list)
        for r in items:
            if r["lang"] == lang and r["text"] and not r["refused"] and r["kind"] in ("plain", "facts", "skill"):
                same_target[r["target_id"]].append(r)
        collided = set()
        for tid, rs in same_target.items():
            for x, y in combinations(rs, 2):
                if x["arm"] != y["arm"] and jaccard(toks[x["item_id"]], toks[y["item_id"]]) > COLLISION_J:
                    collided.update([x["item_id"], y["item_id"]])
        for a in arms:
            rs = [r for r in items if r["arm"] == a and r["lang"] == lang and r["text"] and not r["refused"]]
            if not rs:
                continue
            soft = sum(len(re.findall(p, r["text"], re.I)) for r in rs for p in SOFTENERS[lang]) / len(rs)
            stock = sum(len(re.findall(p, r["text"], re.I)) for r in rs for p in STOCK[lang]) / len(rs)
            coll = sum(r["item_id"] in collided for r in rs) / len(rs)
            sents = [max(1, len(re.split(r"(?<=[.!?。！？])\s*", r["text"].strip()))) for r in rs]
            wps = sum(count_words(r["text"], lang) for r in rs) / sum(sents)
            prof[f"{a}|{lang}"] = {"softeners": round(soft, 2), "stock": round(stock, 2), "collision": round(coll, 2), "wps": round(wps, 1)}
            md.append(f"| {a} | {lang} | {soft:.2f} | {stock:.2f} | {fmt_pct(coll)} | {wps:.1f} |")
    S["profile"] = prof
    md.append("")

    # ---- novelty at the level of the joke (devices.py) ----
    dev_path = run_dir / "devices.jsonl"
    if dev_path.exists():
        dev_rows = [r for r in read_jsonl(dev_path) if not r.get("parse_fail")]
        md += ["## Novelty (comic device)", "",
               "One judge call per target and language groups that target's roasts by the image or angle each is built on "
               "(devices.py). Cross-arm = share of an arm's items whose device another arm also used on the same target; "
               "self-repeat = the arm's own samples share a device. Attractors are devices three or more arms reached on their own.", "",
               "| arm | lang | items | cross-arm | self-repeat |", "|---|---|---:|---:|---:|"]
        dstat: dict = defaultdict(lambda: {"n": 0, "cross": 0, "self": 0})
        attract = []
        for r in dev_rows:
            for g in r["groups"]:
                garms = [by_item[i]["arm"] for i in g["item_ids"] if i in by_item]
                if len(set(garms)) >= 3:
                    attract.append((len(set(garms)), r["target_id"], r["lang"], g["device"]))
                for iid in g["item_ids"]:
                    it = by_item.get(iid)
                    if not it:
                        continue
                    st = dstat[(it["arm"], it["lang"])]
                    st["n"] += 1
                    others = [by_item[j]["arm"] for j in g["item_ids"] if j != iid and j in by_item]
                    st["cross"] += any(a != it["arm"] for a in others)
                    st["self"] += any(a == it["arm"] for a in others)
        devp = {}
        for (a, lang), st in sorted(dstat.items(), key=lambda kv: (arms.index(kv[0][0]) if kv[0][0] in arms else 99, kv[0][1])):
            devp[f"{a}|{lang}"] = {"n": st["n"], "cross": round(st["cross"] / st["n"], 2), "self": round(st["self"] / st["n"], 2)}
            md.append(f"| {a} | {lang} | {st['n']} | {fmt_pct(st['cross'] / st['n'])} | {fmt_pct(st['self'] / st['n'])} |")
        md.append("")
        if attract:
            md += ["Attractors:", ""] + [f"- {n} arms, {tid} ({lang}): {dev or '(unlabelled)'}"
                                        for n, tid, lang, dev in sorted(attract, reverse=True)[:12]] + [""]
        S["devices"] = {"per_arm": devp,
                        "attractors": [{"arms": n, "target": t, "lang": l, "device": d} for n, t, l, d in attract]}

    # ---- specificity ----
    spec_path = run_dir / "specificity.jsonl"
    spec_rows = read_jsonl(spec_path) if spec_path.exists() else []
    spec = {}
    gate_spec_varies = None
    generic_near_chance = None
    if spec_rows:
        md += ["## Specificity gate (masked swap test, k=5)", "", "Chance 20%; twin-only chance 50%. Pooled over judges.", "",
               "| arm | lang | n | picked target | target vs twin | residual leak | lexical contrast |", "|---|---|---:|---:|---:|---:|---:|"]
        for a in arms:
            for lang in langs:
                rs = [r for r in spec_rows if r["arm"] == a and r["lang"] == lang and not r["parse_fail"]]
                if not rs:
                    continue
                pair = [r for r in rs if r["correct"] or r["picked_twin"]]
                spec[f"{a}|{lang}"] = {"n": len(rs), "acc": round(sum(r["correct"] for r in rs) / len(rs), 3),
                                       "twin_acc": round(sum(r["correct"] for r in pair) / len(pair), 3) if pair else None,
                                       "leak": round(sum(bool(r["leaks"]) for r in rs) / len(rs), 3),
                                       "lex": round(sum(r["lex_contrast"] for r in rs) / len(rs), 4)}
                s = spec[f"{a}|{lang}"]
                md.append(f"| {a} | {lang} | {s['n']} | {fmt_pct(s['acc'])} | {fmt_pct(s['twin_acc'])} | {fmt_pct(s['leak'])} | {s['lex']:.3f} |")
        accs = [v["acc"] for k, v in spec.items() if not k.startswith("control-")]
        gate_spec_varies = bool(accs) and (max(accs) - min(accs) >= 0.15) and min(accs) < 0.9
        gen_accs = [v["twin_acc"] for k, v in spec.items() if k.startswith("control-generic") and v["twin_acc"] is not None]
        generic_near_chance = bool(gen_accs) and all(abs(x - 0.5) <= 0.15 for x in gen_accs)
        md += ["", f"Specificity varies across arms (range >= 15 points, some arm < 90%): **{gate_spec_varies}**. "
               f"Generic control near chance on the twin test: **{generic_near_chance}**.", ""]
    else:
        md += ["## Specificity gate", "", "_specificity.jsonl missing: run specificity.py_", ""]
    S["specificity"] = spec

    # ---- truth ----
    truth_path = run_dir / "truth.jsonl"
    truth_rows = read_jsonl(truth_path) if truth_path.exists() else []
    truth = {}
    if truth_rows:
        md += ["## Truth gate", "", "An item fails only on a contradicted premise; facts absent from the sheet do not count against it.", "",
               "| arm | lang | n | pass | claims/item | contradicted/item | absent/item |", "|---|---|---:|---:|---:|---:|---:|"]
        for a in arms:
            for lang in langs:
                rs = [r for r in truth_rows if r["arm"] == a and r["lang"] == lang and not r["parse_fail"]]
                if not rs:
                    continue
                n = len(rs)
                truth[f"{a}|{lang}"] = {"n": n, "pass": round(sum(r["passes"] for r in rs) / n, 3),
                                        "claims": round(sum(r["n_supported"] + r["n_contradicted"] + r["n_absent"] for r in rs) / n, 2),
                                        "contra": round(sum(r["n_contradicted"] for r in rs) / n, 2),
                                        "absent": round(sum(r["n_absent"] for r in rs) / n, 2)}
                t = truth[f"{a}|{lang}"]
                md.append(f"| {a} | {lang} | {n} | {fmt_pct(t['pass'])} | {t['claims']} | {t['contra']} | {t['absent']} |")
        md.append("")
    else:
        md += ["## Truth gate", "", "_truth.jsonl missing: run truth.py_", ""]
    S["truth"] = truth

    # ---- damage tests ----
    dmg_path = run_dir / "damage.jsonl"
    dmg_rows = read_jsonl(dmg_path) if dmg_path.exists() else []
    judges_usable = {}
    if dmg_rows:
        kinds = sorted({r["damage"] for r in dmg_rows})
        md += ["## Judge validation (damage tests)", "", "A usable judge prefers the original >= 90% of the time and never prefers an explained joke. "
               "P(first) is position bias (0.5 is none). Self-pref = accuracy on its own family's roasts minus others'.", "",
               "| judge | lang | " + " | ".join(kinds) + " | overall | P(first) | self-pref | verdict |",
               "|---|---|" + "---:|" * len(kinds) + "---:|---:|---:|---|"]
        for j in sorted({r["judge"] for r in dmg_rows}):
            for lang in langs:
                rs = [r for r in dmg_rows if r["judge"] == j and r["lang"] == lang and not r["parse_fail"]]
                if not rs:
                    continue
                per = {}
                for k in kinds:
                    ks = [r for r in rs if r["damage"] == k]
                    per[k] = sum(r["correct"] for r in ks) / len(ks) if ks else None
                overall = sum(r["correct"] for r in rs) / len(rs)
                p_first = sum(r["chose_A"] for r in rs) / len(rs)
                own = [r for r in rs if r["gen_family"] == r["judge_family"]]
                other = [r for r in rs if r["gen_family"] != r["judge_family"]]
                self_pref = (sum(r["correct"] for r in own) / len(own) - sum(r["correct"] for r in other) / len(other)) if own and other else None
                explain_fail = any(not r["correct"] for r in rs if r["damage"] == "explain")
                verdict = "discard" if explain_fail else ("usable" if overall >= 0.9 else "weak")
                judges_usable[f"{j}|{lang}"] = {"overall": round(overall, 3), "p_first": round(p_first, 3), "per": per,
                                                "self_pref": None if self_pref is None else round(self_pref, 3), "verdict": verdict}
                md.append(f"| {j} | {lang} | " + " | ".join(fmt_pct(per[k]) for k in kinds) +
                          f" | {fmt_pct(overall)} | {p_first:.2f} | {'n/a' if self_pref is None else f'{self_pref:+.2f}'} | {verdict} |")
        md.append("")
    else:
        md += ["## Judge validation", "", "_damage.jsonl missing: run damage.py_", ""]
    S["judges"] = judges_usable
    gate_judge = any(v["verdict"] == "usable" for v in judges_usable.values()) if judges_usable else None

    # ---- human votes ----
    pairs_path = run_dir / "rate" / "pairs.json"
    pairs = {p["pair_id"]: p for p in json.loads(pairs_path.read_text(encoding="utf-8"))["pairs"]} if pairs_path.exists() else {}
    votes = load_votes(run_dir)
    S["votes"] = {"n": len(votes), "raters": sorted({v["rater"] for v in votes})}
    bt_human = {}
    agreement = {}
    gate_spread = None
    gate_controls = None
    gate_raters = None
    judge_human = {}
    # gate status per item: truth passes (if checked) and the specificity judges' majority picked the target (if checked)
    truth_pass = defaultdict(list)
    for r in truth_rows:
        if not r["parse_fail"]:
            truth_pass[r["item_id"]].append(r["passes"])
    spec_ok = defaultdict(list)
    for r in spec_rows:
        if not r["parse_fail"]:
            spec_ok[r["item_id"]].append(r["correct"])

    def passes_gates(iid: str) -> bool:
        iid = iid.split("~")[0]
        t_ok = all(truth_pass[iid]) if truth_pass.get(iid) else True
        s_ok = (sum(spec_ok[iid]) * 2 > len(spec_ok[iid])) if spec_ok.get(iid) else True
        return t_ok and s_ok

    if votes and pairs:
        md += ["## Human votes", "", f"{len(votes)} votes from {len(S['votes']['raters'])} rater(s): {', '.join(S['votes']['raters'])}.", ""]
        cards = {}
        for f in sorted(glob.glob(str(run_dir / "votes" / "*.json"))):
            try:
                d = json.loads(Path(f).read_text(encoding="utf-8"))
                r = d.get("rater") or {}
                if r.get("name"):
                    cards[r["name"]] = r
            except json.JSONDecodeError:
                pass
        if cards:
            md += ["Rater cards (stated taste, so a ranking reads as 'funny to these people'):", ""]
            for name, c in cards.items():
                md.append(f"- **{name}**: languages {c.get('languages') or '?'}; likes {c.get('humor') or '?'}; dark-humor tolerance "
                          f"{c.get('dark', '?')}/5; aggressive-humor {c.get('hsq_agg', '?')}/7; off-limits: {c.get('offlimits') or 'none stated'}")
            md.append("")
        S["rater_cards"] = cards
        # per-rater summary incl. gold accuracy and both-bad rate
        md += ["Aggressive-humor is the rater's 1–7 score from the four card items; line flags is the share of their votes "
               "where they flagged a roast as crossing a line. A higher score should go with fewer flags.", "",
               "| rater | lang | votes | decisive | both bad | skipped | gold acc | median s/vote | aggressive-humor | line flags |",
               "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for rater in S["votes"]["raters"]:
            for lang in langs:
                vs = [v for v in votes if v["rater"] == rater and v["lang"] == lang and v["pair_id"] in pairs]
                if not vs:
                    continue
                dec = [v for v in vs if v["choice"] in ("left", "right")]
                gold = [(v, pairs[v["pair_id"]]) for v in vs if pairs[v["pair_id"]].get("gold") and v["choice"] in ("left", "right")]
                gacc = sum(vote_winner(v, p) == p["gold"]["better"] for v, p in gold) / len(gold) if gold else None
                ms = sorted(v.get("ms", 0) for v in vs)
                med = ms[len(ms) // 2] / 1000 if ms else 0
                flags = sum(bool(v.get("line_left") or v.get("line_right")) for v in vs) / len(vs)
                hsq = (cards.get(rater) or {}).get("hsq_agg")
                md.append(f"| {rater} | {lang} | {len(vs)} | {len(dec)} | {sum(v['choice'] == 'both_bad' for v in vs)} | "
                          f"{sum(v['choice'] == 'skip' for v in vs)} | {fmt_pct(gacc)} | {med:.1f} | "
                          f"{hsq if hsq is not None else '?'} | {fmt_pct(flags)} |")
        md.append("")
        for lang in langs:
            decisions = []
            both_bad = Counter()
            seen = Counter()
            for v in votes:
                p = pairs.get(v["pair_id"])
                if not p or v["lang"] != lang or p.get("gold"):
                    continue
                aa, ab = arm_of(p["a"]["item_id"]), arm_of(p["b"]["item_id"])
                if not aa or not ab:
                    continue
                seen[aa] += 1
                seen[ab] += 1
                w = vote_winner(v, p)
                if w == "a":
                    decisions.append((aa, ab))
                elif w == "b":
                    decisions.append((ab, aa))
                elif v["choice"] == "both_bad":
                    both_bad[aa] += 1
                    both_bad[ab] += 1
            arms_here = [a for a in arms if seen[a]]
            if len(decisions) >= 10 and len(arms_here) >= 2:
                bt = bt_with_ci(decisions, arms_here, boots=args.boots)
                for a in arms_here:
                    bt[a]["both_bad_rate"] = round(both_bad[a] / seen[a], 3) if seen[a] else None
                bt_human[lang] = bt
                md += [f"### Bradley-Terry on human votes, {lang} ({len(decisions)} decisive votes, all items)", "",
                       "| arm | score | 95% CI | both-bad rate | appearances |", "|---|---:|---|---:|---:|"]
                for a, s in sorted(bt.items(), key=lambda kv: -kv[1]["score"]):
                    md.append(f"| {a} | {s['score']:+.2f} | [{s['lo']:+.2f}, {s['hi']:+.2f}] | {fmt_pct(s['both_bad_rate'])} | {s['n']} |")
                md.append("")
                # gates before taste: the same ranking on votes where both items passed specificity and truth
                if truth_pass or spec_ok:
                    gated = []
                    for v in votes:
                        p = pairs.get(v["pair_id"])
                        if not p or v["lang"] != lang or p.get("gold"):
                            continue
                        if passes_gates(p["a"]["item_id"]) and passes_gates(p["b"]["item_id"]):
                            w = vote_winner(v, p)
                            aa, ab = arm_of(p["a"]["item_id"]), arm_of(p["b"]["item_id"])
                            if w == "a":
                                gated.append((aa, ab))
                            elif w == "b":
                                gated.append((ab, aa))
                    arms_g = [a for a in arms_here if any(a in d for d in gated)]
                    if len(gated) >= 10 and len(arms_g) >= 2:
                        btg = bt_with_ci(gated, arms_g, boots=args.boots)
                        bt_human[f"{lang}_gated"] = btg
                        md += [f"### Bradley-Terry, {lang}, gated ({len(gated)} votes where both items passed specificity and truth)", "",
                               "| arm | score | 95% CI | appearances |", "|---|---:|---|---:|"]
                        for a, s in sorted(btg.items(), key=lambda kv: -kv[1]["score"]):
                            md.append(f"| {a} | {s['score']:+.2f} | [{s['lo']:+.2f}, {s['hi']:+.2f}] | {s['n']} |")
                        md.append("")
                    else:
                        md += [f"Gated ranking for {lang}: too few votes where both items passed the gates ({len(gated)}).", ""]
                # gates: spread, controls
                reals = [bt[a] for a in arms_here if a in real_arms]
                spread = any(x["lo"] > y["hi"] for x in reals for y in reals if x is not y)
                bland = bt.get("control-bland")
                controls_ok = bland is not None and all(bland["score"] < bt[a]["score"] for a in arms_here if a in real_arms)
                gate_spread = spread if gate_spread is None else (gate_spread or spread)
                gate_controls = controls_ok if gate_controls is None else (gate_controls and controls_ok)
                # projection: CI half-width shrinks ~ 1/sqrt(n)
                widths = [s["hi"] - s["lo"] for s in reals]
                mean_w = sum(widths) / len(widths) if widths else float("nan")
                target_w = 0.5
                need = len(decisions) * (mean_w / target_w) ** 2 if mean_w else float("nan")
                S.setdefault("projection", {})[lang] = {"decisive_votes": len(decisions), "mean_ci_width": round(mean_w, 3),
                                                        "votes_for_width_0.5": int(need) if need == need else None}
                md += [f"Mean 95% CI width across real arms: {mean_w:.2f} log-odds. To reach a width of {target_w} "
                       f"(arms one notch apart become distinguishable) you need about **{int(need) if need == need else 'n/a'} decisive votes** "
                       f"in {lang}, vs {len(decisions)} now.", ""]
            # rater agreement, ties excluded
            per_pair = defaultdict(dict)
            for v in votes:
                p = pairs.get(v["pair_id"])
                if p and v["lang"] == lang and not p.get("gold"):
                    w = vote_winner(v, p)
                    if w:
                        per_pair[v["pair_id"]][v["rater"]] = w
            raters = sorted({r for d in per_pair.values() for r in d})
            pairwise = {}
            for r1, r2 in combinations(raters, 2):
                shared = [d for d in per_pair.values() if r1 in d and r2 in d]
                if shared:
                    pairwise[f"{r1} vs {r2}"] = {"n": len(shared), "agreement": round(sum(d[r1] == d[r2] for d in shared) / len(shared), 3)}
            if pairwise:
                agreement[lang] = pairwise
                mean_agree = sum(v["agreement"] for v in pairwise.values()) / len(pairwise)
                ok = mean_agree >= 0.6
                gate_raters = ok if gate_raters is None else (gate_raters and ok)
                md += [f"### Rater agreement, {lang} (ties excluded; chance 50%)", ""]
                md += [f"- {k}: {fmt_pct(v['agreement'])} on {v['n']} shared decisive pairs" for k, v in pairwise.items()]
                md += [f"- mean pairwise agreement **{fmt_pct(mean_agree)}** (gate: >= 60%)", ""]
            # judge vs human
            jp_path = run_dir / "judge_pairs.jsonl"
            jp = read_jsonl(jp_path) if jp_path.exists() else []
            if jp and per_pair:
                md += [f"### Judge vs human, {lang}", ""]
                for j in sorted({r["judge"] for r in jp}):
                    jd = defaultdict(set)
                    for r in jp:
                        if r["judge"] == j and r["lang"] == lang and r["winner"]:
                            jd[r["pair_id"]].add(r["winner"])
                    consistent = {pid: next(iter(ws)) for pid, ws in jd.items() if len(ws) == 1}  # same answer in both orders
                    agree_n = agree = 0
                    for pid, d in per_pair.items():
                        if pid in consistent:
                            for rater, w in d.items():
                                agree_n += 1
                                agree += (w == consistent[pid])
                    flip = 1 - len(consistent) / len(jd) if jd else None
                    judge_human[f"{j}|{lang}"] = {"agreement_with_humans": round(agree / agree_n, 3) if agree_n else None, "n": agree_n,
                                                  "order_flip_rate": None if flip is None else round(flip, 3)}
                    jh = judge_human[f"{j}|{lang}"]
                    md.append(f"- {j}: agrees with human votes {fmt_pct(jh['agreement_with_humans'])} (n={agree_n}); flips its answer when "
                              f"order is swapped {fmt_pct(jh['order_flip_rate'])}. Human-human ceiling: "
                              f"{fmt_pct(sum(v['agreement'] for v in agreement.get(lang, {}).values()) / len(agreement[lang])) if agreement.get(lang) else 'n/a'}.")
                md.append("")
    else:
        md += ["## Human votes", "", "_No votes yet. Open runs/<run>/rate/index.html, rate, export, and drop the JSON files into runs/<run>/votes/._", ""]
    S["bt_human"] = bt_human
    S["agreement"] = agreement
    S["judge_human"] = judge_human

    # ---- gates ----
    gates = {"controls_behave": (gate_controls if gate_controls is not None else None, generic_near_chance),
             "spread": gate_spread, "raters_agree": gate_raters, "specificity_varies": gate_spec_varies, "judge_usable": gate_judge}

    def show(g):
        if isinstance(g, tuple):
            return " / ".join(show(x) for x in g)
        return "PASS" if g is True else "FAIL" if g is False else "no data"

    md += ["## Gates", "", "| gate | result |", "|---|---|"]
    md += [f"| controls behave (bland below real arms / generic near chance) | {show(gates['controls_behave'])} |",
           f"| spread (two arms, non-overlapping 95% CIs) | {show(gates['spread'])} |",
           f"| raters agree (>= 0.6, ties excluded) | {show(gates['raters_agree'])} |",
           f"| specificity varies | {show(gates['specificity_varies'])} |",
           f"| a judge is usable (>= 90% damage, never prefers explained) | {show(gates['judge_usable'])} |", ""]
    decided = [g for g in [gates["controls_behave"][0], gates["spread"], gates["raters_agree"], gates["specificity_varies"]] if g is not None]
    verdict = "no verdict yet (human data missing)" if not decided or gate_spread is None else ("GO" if all(decided) else "NO-GO as designed; see failed gates")
    if gate_judge is False:
        verdict += "; benchmark stays human-rated (no judge passed)"
    md += [f"**Verdict: {verdict}**", ""]
    S["gates"] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in gates.items()}
    S["verdict"] = verdict

    (run_dir / "report.md").write_text("\n".join(md), encoding="utf-8")
    (run_dir / "summary.json").write_text(json.dumps(S, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(md))
    print(f"\nwrote {run_dir / 'report.md'} and summary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
