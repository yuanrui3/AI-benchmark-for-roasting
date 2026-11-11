"""Novelty at the level of the joke, not the wording: group each target's roasts by comic device.

    uv run python devices.py --run pilot-or --budget 4
    uv run python devices.py --run mock --mock

The profile's token-Jaccard collision metric misses what the smoke runs showed: three models reaching
"a clown at a funeral" for Comic Sans in different words. Here one judge call per (target, language)
sees every roast of that target and groups them by the image, analogy or angle each is built on
(GTVH: same script opposition and logical mechanism). Two roasts in one group from different arms are
a cross-arm collision; two from the same arm are a self-repeat (two samples, one joke).

Writes runs/<run>/devices.jsonl, one row per (target, lang, judge). analyze.py reports it as
"Novelty (comic device)". Under --mock the grouping is union-find over token Jaccard, no model.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from common import ROOT, append_jsonl, jaccard, load_targets, read_jsonl, tokens, utf8_stdout
from llm import LLM, BudgetExceeded

JUDGE_SYSTEM = "You are a comedy editor. Follow the output format exactly."


def prompt(texts: list[str], lang: str, name: str) -> str:
    numbered = "\n\n".join(f"{i + 1}. {t.strip()}" for i, t in enumerate(texts))
    if lang == "zh":
        return (f"下面是{len(texts)}段吐槽同一个对象（{name}）的段子，已编号。请按“核心梗”把它们分组：段子赖以成立的那个画面、"
                f"比喻、场景或角度（比如“葬礼上的小丑”“翻垃圾桶的浣熊”“寻猫启事专用字体”）。两段段子只要会让听众觉得"
                f"“这不是同一个梗吗”，哪怕措辞不同，就算同一组。一段里有好几个梗的，按主梗归组。梗独一份的，自己一组。\n\n"
                f"{numbered}\n\n"
                f"Return a JSON array of groups, each an object with keys \"device\" (a label of at most 12 Chinese characters) "
                f"and \"items\" (the list of roast numbers), covering every number exactly once, and nothing else.")
    return (f"Below are {len(texts)} roasts of the same target ({name}), numbered. Group them by their central comic device: "
            f"the image, analogy, scenario or angle the roast is built on (for example 'a clown at a funeral', 'a raccoon "
            f"in a dumpster', 'the font of missing-cat posters'). Two roasts share a device when a listener would say "
            f"'that's the same joke', even if the wording differs. A roast with several devices goes with its main one. "
            f"A roast whose device no other roast uses forms a group of its own.\n\n"
            f"{numbered}\n\n"
            f"Return a JSON array of groups, each an object with keys \"device\" (a label of at most 8 words) and "
            f"\"items\" (the list of roast numbers), covering every number exactly once, and nothing else.")


def parse_groups(text: str, n: int) -> list[dict] | None:
    """[{'device': str, 'items': [int]}] covering 1..n; uncovered numbers become singletons; None if unparseable.
    Takes the LAST JSON array of objects in the text: a judge sometimes writes one, then "Corrected:" and another,
    and a greedy bracket match would span both."""
    data = None
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != "[":
            continue
        try:
            obj, _ = dec.raw_decode(text, i)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, list) and obj and all(isinstance(g, dict) for g in obj):
            data = obj
    if data is None:
        return None
    groups, seen = [], set()
    for g in data:
        if not isinstance(g, dict):
            continue
        nums = []
        for x in g.get("items") or []:
            try:
                k = int(x)
            except (TypeError, ValueError):
                continue
            if 1 <= k <= n and k not in seen:
                seen.add(k)
                nums.append(k)
        if nums:
            groups.append({"device": str(g.get("device") or "").strip()[:60], "items": nums})
    for k in range(1, n + 1):
        if k not in seen:
            groups.append({"device": "", "items": [k]})
    return groups


def mock_groups(texts: list[str], lang: str) -> list[dict]:
    toks = [set(tokens(t)) for t in texts]
    parent = list(range(len(texts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if jaccard(toks[i], toks[j]) > 0.3:
                parent[find(i)] = find(j)
    by_root: dict[int, list[int]] = defaultdict(list)
    for i in range(len(texts)):
        by_root[find(i)].append(i + 1)
    out = []
    for nums in by_root.values():
        shared = set.intersection(*(toks[k - 1] for k in nums)) if len(nums) > 1 else set()
        out.append({"device": " ".join(sorted(shared)[:3]), "items": sorted(nums)})
    return out


def summarize(rows: list[dict], items_by_id: dict[str, dict]) -> None:
    arm_stats: dict[tuple[str, str], dict] = defaultdict(lambda: {"n": 0, "cross": 0, "self": 0})
    attractors = []
    for r in rows:
        if r.get("parse_fail"):
            continue
        for g in r["groups"]:
            arms = [items_by_id[i]["arm"] for i in g["item_ids"] if i in items_by_id]
            if len(set(arms)) >= 3:
                attractors.append((len(set(arms)), r["target_id"], r["lang"], g["device"], sorted(set(arms))))
            for iid in g["item_ids"]:
                it = items_by_id.get(iid)
                if not it:
                    continue
                st = arm_stats[(it["arm"], it["lang"])]
                st["n"] += 1
                others = [items_by_id[j]["arm"] for j in g["item_ids"] if j != iid and j in items_by_id]
                if any(a != it["arm"] for a in others):
                    st["cross"] += 1
                if any(a == it["arm"] for a in others):
                    st["self"] += 1
    print(f"{'arm':18s} lang    n  cross-arm  self-repeat")
    for (arm, lang), st in sorted(arm_stats.items()):
        print(f"{arm:18s} {lang:4s} {st['n']:4d}   {st['cross'] / st['n']:6.2f}     {st['self'] / st['n']:6.2f}")
    if attractors:
        print("\nattractors (one device, three or more arms):")
        for n_arms, tid, lang, dev, arms in sorted(attractors, reverse=True)[:15]:
            print(f"  {n_arms} arms  {tid:18s} {lang}  {dev!r}  {arms}")


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--budget", type=float, default=40.0, help="run-wide USD cap (ledger is shared by all stages)")
    ap.add_argument("--judges", default=None, help="comma list; default: the truth judge (config.TRUTH_JUDGE_ORDER)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--max-tokens", type=int, default=config.JUDGE_MAX_TOKENS,
                    help="OpenRouter refuses a call whose cap times the output price exceeds the balance; lower this when funds are low")
    ap.add_argument("--effort", default=config.JUDGE_EFFORT, help="low | medium | high | none (no reasoning)")
    args = ap.parse_args()

    run_dir = ROOT / "runs" / args.run
    targets = load_targets()
    items = [r for r in read_jsonl(run_dir / "items.jsonl")
             if r["kind"] in ("plain", "facts", "skill") and not r["refused"] and not r["error"] and r["text"].strip()]
    items_by_id = {r["item_id"]: r for r in items}
    judge_names = args.judges.split(",") if args.judges else config.truth_judges(args.mock)
    judges = {j: config.MODELS[config.JUDGES[j]] for j in judge_names}
    out_path = run_dir / "devices.jsonl"
    done = {(r["target_id"], r["lang"], r["judge"]) for r in read_jsonl(out_path)} if out_path.exists() else set()

    groups_in: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in items:
        groups_in[(r["target_id"], r["lang"])].append(r)
    jobs = [(tid, lang, rs, j) for (tid, lang), rs in sorted(groups_in.items()) for j in judges
            if len(rs) >= 2 and (tid, lang, j) not in done]
    print(f"{len(groups_in)} target-language cells, {len(judges)} judge(s) -> {len(jobs)} calls to do")

    llm = LLM(run_dir, budget_usd=args.budget, mock=args.mock)
    lock = threading.Lock()
    stop = threading.Event()

    def work(job):
        tid, lang, rs, jname = job
        if stop.is_set():
            return
        rs = sorted(rs, key=lambda r: (r["arm"], r["sample"]))
        texts = [r["text"] for r in rs]
        name = config.target_name(targets[tid], lang)
        if args.mock:
            groups, cost, err = mock_groups(texts, lang), 0.0, None
        else:
            try:
                res = llm.call(judges[jname], JUDGE_SYSTEM, prompt(texts, lang, name), max_tokens=args.max_tokens,
                               effort=args.effort, tag=f"devices:{jname}")
            except BudgetExceeded as e:
                stop.set()
                print(f"BUDGET: {e}")
                return
            groups, cost, err = parse_groups(res.text, len(texts)), res.cost_usd, res.error
        row = {"target_id": tid, "lang": lang, "judge": jname, "n_items": len(rs),
               "groups": [{"device": g["device"], "item_ids": [rs[k - 1]["item_id"] for k in g["items"]],
                           "arms": sorted({rs[k - 1]["arm"] for k in g["items"]})} for g in groups] if groups else [],
               "parse_fail": groups is None, "cost_usd": cost, "error": err}
        with lock:
            append_jsonl(out_path, row)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for _ in as_completed([ex.submit(work, j) for j in jobs]):
            pass

    rows = read_jsonl(out_path) if out_path.exists() else []
    print(f"spent ${llm.spent_usd:.2f}; {len(rows)} cells, {sum(bool(r['parse_fail']) for r in rows)} parse failures")
    summarize(rows, items_by_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
