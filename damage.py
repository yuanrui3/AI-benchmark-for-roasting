"""Damage tests: validate candidate judges without humans.

    uv run python damage.py --run mock --mock
    uv run python damage.py --run pilot --budget 10 --per-lang 30

Take N good originals per language (non-control arms), build seven damaged variants
whose direction is obvious, and ask each judge which of (original, damaged) is the
better roast, in both presentation orders. A usable judge prefers the original.

Variants: explain (joke explained after the punchline), softener (appended),
generic (specific details made vague), frontload (punchline moved first),
pad (twice the length, no new jokes), false (one premise made false),
polite (rewritten as a polite critique). Mechanical where possible; a cheap
"damager" model (config.DAMAGER_MODEL, Haiku; config.FALLBACK_MODEL without an Anthropic key) writes the rest,
or a mechanical stand-in under --mock.

Output: runs/<run>/damaged.jsonl (variants; rate.html reuses some as gold pairs),
runs/<run>/damage.jsonl (one row per pair x order x judge), and a per-judge summary
with accuracy per damage type, position bias and the explain-rule verdict.
"""
from __future__ import annotations

import argparse
import random
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from common import ROOT, append_jsonl, count_words, load_targets, parse_letter, read_jsonl, utf8_stdout
from llm import LLM, BudgetExceeded

DAMAGES = ["explain", "softener", "generic", "frontload", "pad", "false", "polite"]
JUDGE_SYSTEM = "You are a comedy editor judging roasts. Follow the answer format exactly."

SOFTENER = {"en": " No offense though. Honestly, it's great and we love it.",
            "zh": "开个玩笑啊，其实它挺好的，别介意。"}


def sentences(text: str, lang: str) -> list[str]:
    text = text.strip()
    if lang == "zh":
        parts = re.split(r"(?<=[。！？!?])", text)
    else:
        parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def mechanical(kind: str, text: str, lang: str) -> str | None:
    sents = sentences(text, lang)
    if kind == "softener":
        return text.rstrip() + SOFTENER[lang]
    if kind == "frontload":
        if len(sents) < 3:
            return None
        return (" " if lang == "en" else "").join([sents[-1]] + sents[:-1])
    if kind == "explain":  # mock stand-in only; the real variant is model-written
        tail = {"en": " In other words, the joke works because it points out the gap between how it presents itself "
                      "and what it actually is, which is what makes it funny.",
                "zh": "换句话说，这个笑点在于它表面上一套、实际上另一套，这种反差就是好笑的地方。"}[lang]
        return text.rstrip() + tail
    if kind == "pad":  # mock stand-in
        filler = {"en": " Now, I want to be fair here, and I think most people would agree with this, more or less.",
                  "zh": "当然了，我这么说也不是没有道理，大多数人应该多多少少都会同意的。"}[lang]
        return (" " if lang == "en" else "").join(s + filler for s in sents)
    if kind == "generic":  # mock stand-in
        return re.sub(r"\b\d[\d,\.]*\b", "many", text) if lang == "en" else re.sub(r"\d+", "很多", text)
    if kind == "false":  # mock stand-in
        return re.sub(r"\b(19|20)\d\d\b", "1850", text, count=1) if lang == "en" else re.sub(r"\d{4}", "1850", text, count=1)
    if kind == "polite":  # mock stand-in
        return ({"en": "To be fair, there are some reasonable points to consider. ", "zh": "客观地说，这里有几点值得考虑。"}[lang]
                + text)
    return None


def clean_rewrite(text: str) -> str:
    """Drop wrapping markdown the damager sometimes adds: ---, ``` fences, a leading 'Here is...' line."""
    lines = [ln for ln in text.strip().splitlines()]
    while lines and re.fullmatch(r"\s*(-{3,}|`{3,}\w*|\*{3,})\s*", lines[0]):
        lines.pop(0)
    while lines and re.fullmatch(r"\s*(-{3,}|`{3,})\s*", lines[-1]):
        lines.pop()
    return "\n".join(lines).strip()


def damager_prompt(kind: str, text: str, lang: str, target: dict) -> str:
    facts = "\n".join(f"- {f}" for f in target["facts"])
    name = config.target_name(target, lang)
    if lang == "zh":
        head = f"下面是一段吐槽{name}的段子：\n---\n{text}\n---\n"
        tail = "只输出改写后的全文，不要任何说明。"
        body = {
            "explain": "在最后一个笑点之后，追加一两句话，用平铺直叙的说明文语气把这个笑话为什么好笑讲清楚，像老师讲课一样点明梗在哪里。"
                       "不要写新的俏皮话、比喻或金句，不要押韵，不要再抖包袱。原文一字不改。",
            "generic": f"把段子里所有具体、可查证的细节（名字、数字、年份、具体特征）换成模糊的泛泛之词，让它换成任何一种{config.category_name(target, lang)}都成立。长度和结构不变。",
            "pad": "把这段话改写成原来两倍左右的长度：加铺垫、加口水话、加重复和客套，不要加新的笑点和新的事实，保留每一句原话。",
            "false": f"参考事实清单：\n{facts}\n挑出段子依赖的一条事实性前提（年份、数字、人名、公司、来历），换成一个听起来像真的、"
                     f"但与事实清单明显矛盾的说法：年代差一截、换一家公司、数字差好几倍。不要只改一个无关紧要的小数字。"
                     f"如果段子里没有这样的前提，就改最像事实的那处细节。其他一字不改。",
            "polite": "把这段话改写成礼貌、客观、平衡的评价：不开玩笑、不讽刺、不夸张，要点不变，长度相近。",
        }[kind]
        return head + body + tail
    head = f"Here is a roast of {name}:\n---\n{text}\n---\n"
    tail = " Output only the full rewritten text, no commentary."
    body = {
        "explain": "After the final punchline, append one or two sentences in flat expository prose, like a teacher, that explain why the joke is funny and spell out the reference. Add no new wit, metaphor or punchline. Leave the original text unchanged.",
        "generic": f"Rewrite it replacing every specific, checkable detail (names, numbers, dates, particular features) with a vague generic equivalent that could apply to any {config.category_name(target, lang)}. Keep the length and structure.",
        "pad": "Rewrite it at about twice the length by adding filler, hedging, throat-clearing and restatement. Add no new jokes or facts. Keep every original sentence.",
        "false": f"Fact sheet for reference:\n{facts}\nPick one factual premise the roast relies on (a year, a number, a name, a company, an origin) "
                 f"and replace it with a plausible-sounding one that the fact sheet clearly contradicts: the wrong decade, a different "
                 f"company, a figure off by several times. Do not merely tweak an incidental digit. If the roast states no such premise, "
                 f"change its most fact-like detail. Change nothing else.",
        "polite": "Rewrite it as a polite, balanced critique with no jokes, sarcasm or exaggeration. Same points, similar length.",
    }[kind]
    return head + body + tail


def judge_prompt(a: str, b: str, lang: str, name: str, facts: list[str] | None = None) -> str:
    """Same brief the human raters get in rate.html: the fact sheet is shown so an invented premise can be held
    against a roast (without it a judge cannot see the 'false' damage at all)."""
    sheet = "\n".join(f"- {f}" for f in facts or [])
    if lang == "zh":
        head = f"关于{name}的事实清单（已核实，英文）：\n{sheet}\n\n" if sheet else ""
        return (f"{head}下面是两段吐槽同一个对象（{name}）的段子。\n\nA:\n{a}\n\nB:\n{b}\n\n"
                f"哪一段作为吐槽更好：更好笑、更狠、更具体？编造事实的段子要扣分，自己解释笑点的段子也要扣分。Answer with a single letter: A or B.")
    head = f"Fact sheet about {name} (verified):\n{sheet}\n\n" if sheet else ""
    return (f"{head}Below are two roasts of the same target ({name}).\n\nA:\n{a}\n\nB:\n{b}\n\n"
            f"Which is the better roast: funnier, sharper, more specific? Hold invented facts against a roast, and a roast "
            f"that explains its own joke. "
            f"Answer with a single letter: A or B.")


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--budget", type=float, default=40.0, help="run-wide USD cap (ledger is shared by all stages)")
    ap.add_argument("--per-lang", type=int, default=30, help="originals per language")
    ap.add_argument("--judges", default=None, help="comma list; default: every judge whose key exists")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()

    run_dir = ROOT / "runs" / args.run
    targets = load_targets()
    items = [r for r in read_jsonl(run_dir / "items.jsonl")
             if r["kind"] in ("plain", "facts", "skill") and not r["refused"] and not r["error"]
             and count_words(r["text"], r["lang"]) >= (40 if r["lang"] == "en" else 60)]
    rng = random.Random(args.seed)
    variants_path = run_dir / "damaged.jsonl"
    existing = {(r["item_id"], r["damage"]): r for r in read_jsonl(variants_path)} if variants_path.exists() else {}
    prior_ids = {item_id for item_id, _ in existing}  # originals from an earlier pass keep their place
    originals = []
    for lang in sorted({r["lang"] for r in items}):
        pool = [r for r in items if r["lang"] == lang]
        rng.shuffle(pool)
        picked = [r for r in pool if r["item_id"] in prior_ids][: args.per_lang]
        by_arm: dict[str, list] = {}
        for r in pool:
            if r["item_id"] not in prior_ids:
                by_arm.setdefault(r["arm"], []).append(r)
        arms = sorted(by_arm)
        while len(picked) < args.per_lang and any(by_arm.values()):
            for a in arms:
                if by_arm[a] and len(picked) < args.per_lang:
                    picked.append(by_arm[a].pop())
        originals += picked
    per_lang = {lang: sum(r["lang"] == lang for r in originals) for lang in sorted({r["lang"] for r in originals})}
    print(f"{len(originals)} originals {per_lang}")

    llm = LLM(run_dir, budget_usd=args.budget, mock=args.mock)
    damager = config.damager_spec(args.mock)
    judge_names = args.judges.split(",") if args.judges else config.usable_judges(args.mock)
    judges = {j: config.MODELS[config.JUDGES[j]] for j in judge_names}

    # 1) build variants
    variants = []
    for it in originals:
        t = targets[it["target_id"]]
        for kind in DAMAGES:
            if (it["item_id"], kind) in existing:
                variants.append(existing[(it["item_id"], kind)])
                continue
            text = None
            if args.mock or kind in ("softener", "frontload"):
                text = mechanical(kind, it["text"], it["lang"])
            else:
                try:
                    res = llm.call(damager, "You rewrite text exactly as instructed. Output only the text.",
                                   damager_prompt(kind, it["text"], it["lang"], t), max_tokens=6000, effort="none",
                                   tag=f"damager:{kind}")
                except BudgetExceeded as e:
                    print(f"BUDGET while damaging: {e}")
                    return 3
                text = clean_rewrite(res.text) if res.text.strip() and not res.refused else None
            if not text or text == it["text"]:
                continue
            row = {"item_id": it["item_id"], "damage": kind, "lang": it["lang"], "arm": it["arm"], "gen_family": it["family"],
                   "target_id": it["target_id"], "original": it["text"], "damaged": text}
            append_jsonl(variants_path, row)
            variants.append(row)
    print(f"{len(variants)} damaged variants ready")

    # 2) judge every (variant, order, judge)
    out_path = run_dir / "damage.jsonl"
    done = {(r["item_id"], r["damage"], r["order"], r["judge"]) for r in read_jsonl(out_path)} if out_path.exists() else set()
    jobs = [(v, order, j) for v in variants for order in ("orig_first", "dmg_first") for j in judges
            if (v["item_id"], v["damage"], order, j) not in done]
    print(f"{len(jobs)} judge calls to do")
    lock = threading.Lock()
    stop = threading.Event()

    def work(job):
        v, order, jname = job
        if stop.is_set():
            return
        spec = judges[jname]
        a, b = (v["original"], v["damaged"]) if order == "orig_first" else (v["damaged"], v["original"])
        name = config.target_name(targets[v["target_id"]], v["lang"])
        try:
            res = llm.call(spec, JUDGE_SYSTEM, judge_prompt(a, b, v["lang"], name, targets[v["target_id"]]["facts"]),
                           max_tokens=config.JUDGE_MAX_TOKENS,
                           effort=config.JUDGE_EFFORT, 
                           tag=f"damage:{jname}")
        except BudgetExceeded as e:
            stop.set()
            print(f"BUDGET: {e}")
            return
        if res.error:  # not persisted: the ledger keeps the error and the next run retries the call
            print(f"  failed, will retry next run: {res.error[:80]}", flush=True)
            return
        ans = parse_letter(res.text)
        orig_letter = "A" if order == "orig_first" else "B"
        row = {"item_id": v["item_id"], "damage": v["damage"], "lang": v["lang"], "arm": v["arm"],
               "gen_family": v["gen_family"], "order": order, "judge": jname, "judge_family": spec.family,
               "answer": ans, "correct": ans == orig_letter, "chose_A": ans == "A", "parse_fail": ans is None,
               "cost_usd": res.cost_usd, "error": res.error}
        with lock:
            append_jsonl(out_path, row)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for _ in as_completed([ex.submit(work, j) for j in jobs]):
            pass

    rows = read_jsonl(out_path)
    print(f"\nspent ${llm.spent_usd:.2f}\n{'judge':14s} {'lang':4s} " + " ".join(f"{d[:7]:>7s}" for d in DAMAGES)
          + f" {'all':>6s} {'P(A)':>6s} {'verdict'}")
    for j in sorted({r["judge"] for r in rows}):
        for lang in sorted({r["lang"] for r in rows}):
            rs = [r for r in rows if r["judge"] == j and r["lang"] == lang]
            if not rs:
                continue
            accs = []
            for d in DAMAGES:
                ds = [r for r in rs if r["damage"] == d]
                accs.append(sum(r["correct"] for r in ds) / len(ds) if ds else float("nan"))
            overall = sum(r["correct"] for r in rs) / len(rs)
            p_a = sum(r["chose_A"] for r in rs) / len(rs)
            explain_fail = any(not r["correct"] and not r["parse_fail"] for r in rs if r["damage"] == "explain")
            verdict = "DISCARD (preferred an explained joke)" if explain_fail else ("usable" if overall >= 0.9 else "weak")
            print(f"{j:14s} {lang:4s} " + " ".join(f"{a:7.2f}" for a in accs) + f" {overall:6.2f} {p_a:6.2f} {verdict}")
    return 0 if not stop.is_set() else 3


if __name__ == "__main__":
    sys.exit(main())
