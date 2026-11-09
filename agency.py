"""Agent-action rate: what share of a roast's lines hit someone doing something, rather than describe the object.

    uv run python agency.py --run pilot-or --budget 4
    uv run python agency.py --run mock --mock

The owner's reading of the pilot (9 Nov 2026): a roast is about someone doing something. The lines that landed
smuggled a person in ("the official font of mediocre Thai restaurants"); the lines that stayed on the object
read as description with adjectives. One cheap judge call per item labels every sentence:

    A  agent-action   its hit is people doing something: using, buying, choosing, believing, selling or making it
                      (makers and sellers count)
    O  object         a property, look, feature or history of the thing itself
    N  neither        connective, setup, address to the audience

agent_rate = A / (A + O). Writes runs/<run>/agency.jsonl, one row per item x judge, and prints a per-arm table.
Under --mock the labels come from a keyword rule, no model. Failed calls are not persisted (a re-run retries them).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from common import ROOT, append_jsonl, load_targets, read_jsonl, utf8_stdout
from damage import sentences
from llm import LLM, BudgetExceeded

JUDGE_SYSTEM = "You label the sentences of a comedy text. Follow the output format exactly."
LABELS = ("A", "O", "N")
EFFORT_BY_FAMILY = {"deepseek": "none"}  # DeepSeek reasons at length on tiny tasks; labelling needs none
_AGENT_EN = re.compile(r"\b(people|someone|anyone|everyone|guys?|men|women|dad|mom|parents?|kids?|managers?|designers?|developers?|programmers?|engineers?|tourists?|gamblers?|fans?|users?|buyers?|owners?|customers?|compan(?:y|ies)|founders?|investors?|executives?|marketers?|influencers?|hipsters?|bros?)\b", re.I)
# pronouns are left out on purpose: these roasts address the object as "you"
_AGENT_ZH = re.compile(r"(的人|有人|人们|程序员|设计师|老板|公司|游客|顾客|用户|粉丝|买家|创始人|员工|家长|大妈|大哥|小姑娘|赌徒|投资人|厂商|商家|老外|网红|同事|朋友)")


def prompt(sents: list[str], lang: str, name: str) -> str:
    numbered = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(sents))
    if lang == "zh":
        return (f"下面是一段吐槽{name}的段子，已按句编号：\n{numbered}\n\n"
                f"给每一句打一个标签：A = 这句的矛头是某些人在做某件事（用它、买它、选它、信它、卖它、做出它，厂商和设计者也算）；"
                f"O = 这句说的是{name}本身的属性、外观、功能或历史；N = 都不是（过渡、铺垫、对观众说话）。"
                f"只输出一个 JSON 字符串数组，长度等于句数，按顺序一句一个标签，不要别的。")
    return (f"Below is a roast of {name}, one numbered sentence per line:\n{numbered}\n\n"
            f"Label each sentence: A = its hit is people doing something (using, buying, choosing, believing, selling or "
            f"making it; makers and sellers count); O = it describes a property, look, feature or history of {name} itself; "
            f"N = neither (connective, setup, address to the audience). "
            f"Output only a JSON array of strings, one label per sentence in order, nothing else.")


def parse_labels(text: str, n: int) -> list[str] | None:
    m = re.search(r"\[[^\]]*\]", text, re.S)
    if not m:
        return None
    try:
        arr = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    labs = [str(x).strip().upper()[:1] for x in arr]
    if len(labs) != n or any(lab not in LABELS for lab in labs):
        return None
    return labs


def mock_labels(sents: list[str], lang: str) -> list[str]:
    rx = _AGENT_ZH if lang == "zh" else _AGENT_EN
    return ["A" if rx.search(s) else "O" for s in sents]


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--budget", type=float, default=40.0, help="run-wide USD cap (ledger is shared by all stages)")
    ap.add_argument("--judges", default=None, help="comma list; default: config.agency_judges()")
    ap.add_argument("--rule", action="store_true",
                    help="no model: label by the keyword rule (judge name 'rule'); free, crude, runs anywhere")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    run_dir = ROOT / "runs" / args.run
    targets = load_targets()
    items = [r for r in read_jsonl(run_dir / "items.jsonl") if r["text"].strip() and not r["refused"] and not r["error"]]
    if args.rule:
        judges = {"rule": config.MODELS["deepseek"]}  # spec unused; keeps the row shape
    else:
        judge_names = args.judges.split(",") if args.judges else config.agency_judges(args.mock)
        judges = {j: config.MODELS[config.JUDGES[j]] for j in judge_names}
    out_path = run_dir / "agency.jsonl"
    done = {(r["item_id"], r["judge"]) for r in read_jsonl(out_path)} if out_path.exists() else set()
    jobs = [(it, j) for it in items for j in judges if (it["item_id"], j) not in done]
    print(f"{len(items)} items, {len(judges)} judge(s) -> {len(jobs)} calls to do")

    llm = LLM(run_dir, budget_usd=args.budget, mock=args.mock)
    lock = threading.Lock()
    stop = threading.Event()

    def work(job):
        it, jname = job
        if stop.is_set():
            return
        spec = judges[jname]
        t = targets[it["target_id"]]
        sents = sentences(it["text"], it["lang"])
        if not sents:
            return
        cost = 0.0
        if args.mock or args.rule:
            labs = mock_labels(sents, it["lang"])
        else:
            try:
                res = llm.call(spec, JUDGE_SYSTEM, prompt(sents, it["lang"], config.target_name(t, it["lang"])),
                               max_tokens=config.JUDGE_MAX_TOKENS,
                               effort=EFFORT_BY_FAMILY.get(spec.family, config.JUDGE_EFFORT), tag=f"agency:{jname}")
            except BudgetExceeded as e:
                stop.set()
                print(f"BUDGET: {e}")
                return
            if res.error:  # not persisted: the ledger keeps the error and the next run retries the call
                print(f"  failed, will retry next run: {res.error[:80]}", flush=True)
                return
            labs = parse_labels(res.text, len(sents))
            cost = res.cost_usd
        n_a = labs.count("A") if labs else 0
        n_o = labs.count("O") if labs else 0
        n_n = labs.count("N") if labs else 0
        row = {"item_id": it["item_id"], "target_id": it["target_id"], "arm": it["arm"], "kind": it["kind"],
               "lang": it["lang"], "model": it["model"], "judge": jname,
               "judge_family": "rule" if jname == "rule" else spec.family,
               "n_sent": len(sents), "labels": labs, "n_agent": n_a, "n_object": n_o, "n_other": n_n,
               "agent_rate": (n_a / (n_a + n_o)) if labs and (n_a + n_o) else None,
               "parse_fail": labs is None, "cost_usd": cost}
        with lock:
            append_jsonl(out_path, row)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(work, j) for j in jobs]
        for _ in as_completed(futs):
            pass

    rows = read_jsonl(out_path) if out_path.exists() else []
    print(f"spent ${llm.spent_usd:.2f}. Agent-action rate = A / (A + O), pooled over judges; higher = more of the roast "
          f"is about people doing something.")
    print(f"{'judge':15s} {'arm':18s} {'lang':4s} {'n':>4s} {'agent':>6s} {'object':>7s} {'other':>6s} {'parse✗':>7s}")
    keys = sorted({(r["judge"], r["arm"], r["lang"]) for r in rows})
    for jname, arm, lang in keys:
        rs = [r for r in rows if (r["judge"], r["arm"], r["lang"]) == (jname, arm, lang)]
        ok = [r for r in rs if r["agent_rate"] is not None]
        tot = sum(r["n_agent"] + r["n_object"] + r["n_other"] for r in ok) or 1
        agent = sum(r["agent_rate"] for r in ok) / len(ok) if ok else float("nan")
        print(f"{jname:15s} {arm:18s} {lang:4s} {len(rs):4d} {agent:6.2f} {sum(r['n_object'] for r in ok) / tot:7.2f} "
              f"{sum(r['n_other'] for r in ok) / tot:6.2f} {sum(r['parse_fail'] for r in rs) / len(rs):7.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
