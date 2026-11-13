"""Judge validation against an external human-preference humor set: does the judge pick what humans picked?

    uv run python external_anchor.py --run ext-anchor --pairs <pairs.jsonl> --judges judge-opus,judge-sonnet --n 600
    uv run python external_anchor.py --run ext-anchor --pairs <zh pairs> --lang zh --bands 3,2   # Chinese instructions, rating-gap bands
    uv run python external_anchor.py --run mock-anchor --pairs <pairs.jsonl> --mock               # plumbing test, no network

The pairs file is prepared outside the repo (third-party text stays out of git): one JSON object per line with
`id`, `source`, `context` (text shown to the judge first, may be empty), `a`, `b`, `human` ("a" or "b"), and an
optional `confidence` (a margin in the human ratings; larger = clearer human verdict). Each pair is judged in both
orders. Only ids, picks and costs are written to runs/<run>/<pairs-stem>.jsonl, never the texts.

The report gives accuracy against the human pick per judge, overall and by confidence band, P(first) (position
bias), and the share of pairs where the judge flips with the order. Humans who rated these sets disagreed with each
other too, so a ceiling is a few points below 100 even for a perfect judge; compare judges to each other and to the
published numbers for the same set (New Yorker ranking: GPT-4 about 67%, humans aligned on crowd data 82-85%).
"""
from __future__ import annotations

import argparse
import random
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import config
from common import ROOT, append_jsonl, parse_letter, read_jsonl, utf8_stdout
from llm import LLM, BudgetExceeded

SYSTEM = ("You judge short comedic texts for a sharp, well-read room. You are shown some context and two candidates. "
          "Pick the one that gets the bigger laugh. Cleverness and surprise win; being longer, safer or more explained "
          "is not a win. Answer with a single letter.")


SYSTEM_ZH = ("你给短的喜剧文本打分，观众是一屋子懂行、读书多的人。你会看到一段背景和两个候选。"
             "选出能拿到更大笑声的那一个。巧和意外赢；更长、更稳妥、把笑点解释一遍，都不算赢。只回答一个字母。")


def prompt(context: str, first: str, second: str, lang: str = "en") -> str:
    ctx = f"{context.strip()}\n\n" if context and context.strip() else ""
    if lang == "zh":
        return (f"{ctx}候选 A：\n{first}\n\n候选 B：\n{second}\n\n"
                f"哪一个更好笑？只回答一个字母：A 或 B。")
    return (f"{ctx}Candidate A:\n{first}\n\nCandidate B:\n{second}\n\n"
            f"Which one is funnier? Answer with a single letter: A or B.")


BANDS = [1.0, 0.6]   # confidence cut points, high to low; --bands overrides (e.g. 3,2 for a ten-point rating gap)


def band(conf) -> str:
    if conf is None:
        return "n/a"
    for i, cut in enumerate(BANDS):
        if conf >= cut:
            return f">={cut:g}" if i == 0 else f"{cut:g}-{BANDS[i - 1]:g}"
    return f"<{BANDS[-1]:g}"


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="ext-anchor", help="folder under runs/ for the ledger, cache and judgements")
    ap.add_argument("--pairs", required=True, help="prepared pairs file (outside the repo)")
    ap.add_argument("--judges", default="judge-opus,judge-sonnet")
    ap.add_argument("--n", type=int, default=None, help="use at most N pairs (seeded shuffle)")
    ap.add_argument("--min-conf", type=float, default=None, help="keep pairs with confidence >= this")
    ap.add_argument("--budget", type=float, default=60.0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--effort", default=config.PAIR_JUDGE_EFFORT)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--lang", default="en", choices=["en", "zh"], help="language of the judge's instructions")
    ap.add_argument("--bands", default=None, help="confidence cut points, high to low, e.g. 3,2 (default 1.0,0.6)")
    ap.add_argument("--mock", action="store_true", help="no network: a coin-flip judge, to test the plumbing")
    args = ap.parse_args()
    if args.bands:
        BANDS[:] = sorted((float(x) for x in args.bands.split(",")), reverse=True)

    pairs = read_jsonl(Path(args.pairs))
    if args.min_conf is not None:
        pairs = [p for p in pairs if p.get("confidence") is not None and p["confidence"] >= args.min_conf]
    rng = random.Random(args.seed)
    rng.shuffle(pairs)
    if args.n:
        pairs = pairs[:args.n]
    by_id = {p["id"]: p for p in pairs}
    judges = {j: config.MODELS[config.JUDGES[j]] for j in args.judges.split(",")}

    run_dir = ROOT / "runs" / args.run
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / (Path(args.pairs).stem + ".jsonl")
    done = {(r["id"], r["judge"], r["order"]) for r in read_jsonl(out_path)} if out_path.exists() else set()
    jobs = [(p, j, order) for p in pairs for j in judges for order in ("ab", "ba") if (p["id"], j, order) not in done]
    print(f"{len(pairs)} pairs x {len(judges)} judges x 2 orders -> {len(jobs)} calls to do ({len(done)} done)")

    llm = LLM(run_dir, budget_usd=args.budget, mock=args.mock)
    system = SYSTEM_ZH if args.lang == "zh" else SYSTEM
    lock = threading.Lock()
    stop = threading.Event()

    def work(job):
        p, jname, order = job
        if stop.is_set():
            return
        first, second = (p["a"], p["b"]) if order == "ab" else (p["b"], p["a"])
        if args.mock:
            import hashlib
            letter = "AB"[hashlib.sha256(f"{p['id']}|{jname}|{order}".encode()).digest()[0] % 2]
            cost = 0.0
        else:
            try:
                res = llm.call(judges[jname], system, prompt(p.get("context", ""), first, second, args.lang),
                               max_tokens=config.JUDGE_MAX_TOKENS, effort=args.effort, tag=f"anchor:{jname}")
            except BudgetExceeded as e:
                stop.set()
                print(f"BUDGET: {e}")
                return
            if res.error:
                return
            letter = parse_letter(res.text, "AB")
            cost = res.cost_usd
        pick = None
        if letter:
            pick = ("a" if letter == "A" else "b") if order == "ab" else ("b" if letter == "A" else "a")
        row = {"id": p["id"], "source": p.get("source"), "judge": jname, "order": order, "pick": pick,
               "chose_first": (letter == "A") if letter else None, "human": p["human"],
               "correct": (pick == p["human"]) if pick else None, "confidence": p.get("confidence"),
               "parse_fail": pick is None, "cost_usd": cost}
        with lock:
            append_jsonl(out_path, row)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for _ in as_completed([ex.submit(work, j) for j in jobs]):
            pass

    rows = [r for r in read_jsonl(out_path) if r["id"] in by_id] if out_path.exists() else []
    if not rows:
        print(f"spent ${llm.spent_usd:.2f}; no judgements written (every call failed?)")
        return 1
    print(f"spent ${llm.spent_usd:.2f}; {len(rows)} judgements -> {out_path}")
    print(f"{'judge':13s} {'band / source':22s} {'n':>5s} {'acc':>6s} {'P(first)':>9s} {'flip':>6s} {'parse✗':>7s}")
    for j in judges:
        jr = [r for r in rows if r["judge"] == j]
        picks: dict[str, dict[str, str | None]] = defaultdict(dict)
        for r in jr:
            picks[r["id"]][r["order"]] = r["pick"]
        labels = ["all"] + sorted({band(r.get("confidence")) for r in jr}, reverse=True)
        sources = sorted({str(r.get("source")) for r in jr})
        if len(sources) > 1:
            labels += [f"src:{x}" for x in sources]
        for b in labels:
            sel = [r for r in jr if b == "all" or band(r.get("confidence")) == b
                   or (b.startswith("src:") and str(r.get("source")) == b[4:])]
            if not sel:
                continue
            ok = [r for r in sel if r["correct"] is not None]
            acc = sum(r["correct"] for r in ok) / len(ok) if ok else float("nan")
            pf = [r["chose_first"] for r in sel if r["chose_first"] is not None]
            ids = {r["id"] for r in sel}
            flips = sum(1 for i in ids if len(picks[i]) == 2 and picks[i]["ab"] and picks[i]["ba"]
                        and picks[i]["ab"] != picks[i]["ba"])
            both = sum(1 for i in ids if len(picks[i]) == 2)
            print(f"{j:13s} {b:22s} {len(sel):5d} {acc:6.2f} {sum(pf) / len(pf) if pf else float('nan'):9.2f} "
                  f"{flips / both if both else float('nan'):6.2f} {sum(r['parse_fail'] for r in sel) / len(sel):7.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
