"""Generate the fixed item pool: every arm x target x language x sample.

    uv run python generate.py --mock                 # zero-cost pipeline test -> runs/mock
    uv run python generate.py --run pilot --dry-run  # count calls, estimate cost, call nothing
    uv run python generate.py --run pilot --budget 40 --targets 4 --samples 1   # small real smoke
    uv run python generate.py --run pilot --budget 40                            # the real thing
    uv run python generate.py --list-models gpt-5    # search OpenRouter ids

Output: runs/<run>/items.jsonl (one line per generation, including refusals and
errors), runs/<run>/manifest.json, runs/<run>/ledger.jsonl (cost), runs/<run>/raw/.
Re-running the same --run resumes: finished items are skipped.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import config
from llm import LLM, PRICES_PER_M, BudgetExceeded

ROOT = Path(__file__).resolve().parent


def load_targets(path: Path = ROOT / "targets.jsonl") -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def item_id(arm: str, target: str, lang: str, sample: int) -> str:
    return hashlib.sha1(f"{arm}|{target}|{lang}|{sample}".encode("utf-8")).hexdigest()[:12]


def openrouter_model_ids() -> set[str]:
    import httpx2 as httpx
    r = httpx.get("https://openrouter.ai/api/v1/models", timeout=30)
    r.raise_for_status()
    return {m["id"] for m in r.json().get("data", [])}


def check_models(arms: list[dict]) -> bool:
    needed = {config.MODELS[a["model"]] for a in arms}
    or_needed = [s for s in needed if s.provider == "openrouter"]
    ok = True
    if or_needed:
        try:
            ids = openrouter_model_ids()
        except Exception as e:  # noqa: BLE001
            print(f"warning: could not fetch OpenRouter model list ({e}); skipping id check")
            return True
        for s in or_needed:
            if s.model not in ids:
                ok = False
                stem = s.model.split("/")[-1].split("-")[0]
                near = sorted(i for i in ids if i.split("/")[0] == s.model.split("/")[0] and stem in i)[:8]
                print(f"OpenRouter id not found: {s.model}. Nearby: {near}")
    return ok


def estimate_cost(jobs: list[dict]) -> float:
    total = 0.0
    for j in jobs:
        spec = config.MODELS[j["arm"]["model"]]
        p_in, p_out = PRICES_PER_M.get(spec.model, (1.5, 6.0))
        n_in = len(j["system"]) / 3.5 + len(j["user"]) / 3.5
        n_out = 350 if j["arm"]["kind"] != "skill" else 600
        if spec.provider == "anthropic":
            n_out += 600  # thinking tokens, billed as output
        total += (n_in * p_in + n_out * p_out) / 1e6
    return total


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles default to cp1252
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None, help="run name under runs/ (default: date)")
    ap.add_argument("--mock", action="store_true", help="no network, zero cost; run name defaults to 'mock'")
    ap.add_argument("--budget", type=float, default=40.0, help="hard USD cap for this run")
    ap.add_argument("--arms", default=None, help="comma list of arm names (default: all in config.ARMS)")
    ap.add_argument("--langs", default=",".join(config.LANGS))
    ap.add_argument("--samples", type=int, default=config.SAMPLES)
    ap.add_argument("--targets", type=int, default=None, help="use only the first N targets (smoke tests)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--dry-run", action="store_true", help="plan and estimate only")
    ap.add_argument("--list-models", metavar="QUERY", help="search OpenRouter ids and exit")
    args = ap.parse_args()

    if args.list_models:
        q = args.list_models.lower()
        for i in sorted(openrouter_model_ids()):
            if q in i.lower():
                print(i)
        return 0

    run = args.run or ("mock" if args.mock else datetime.now().strftime("%Y%m%d"))
    run_dir = ROOT / "runs" / run
    run_dir.mkdir(parents=True, exist_ok=True)

    arms = config.usable_arms(args.mock)
    if args.arms:
        wanted = set(args.arms.split(","))
        arms = [a for a in arms if a["name"] in wanted]
        missing = wanted - {a["name"] for a in arms}
        if missing:
            print(f"unknown arms: {sorted(missing)}")
            return 2
    langs = args.langs.split(",")
    targets = load_targets()
    if args.targets:
        targets = targets[: args.targets]

    jobs = []
    for arm in arms:
        for t in targets:
            for lang in langs:
                system, user = config.build_prompt(arm, t, lang)
                for s in range(args.samples):
                    jobs.append({"arm": arm, "target": t, "lang": lang, "sample": s, "system": system, "user": user,
                                 "item_id": item_id(arm["name"], t["id"], lang, s)})

    items_path = run_dir / "items.jsonl"
    done_ids = set()
    if items_path.exists():
        with items_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    done_ids.add(json.loads(line)["item_id"])
                except (json.JSONDecodeError, KeyError):
                    pass
    todo = [j for j in jobs if j["item_id"] not in done_ids]

    print(f"run={run} arms={len(arms)} targets={len(targets)} langs={langs} samples={args.samples} "
          f"-> {len(jobs)} items, {len(todo)} to do, est. ${estimate_cost(todo):.2f} (cap ${args.budget:.2f})")
    if args.dry_run:
        return 0
    if not args.mock and not check_models(arms):
        print("fix config.MODELS (see generate.py --list-models) and rerun")
        return 2

    manifest = {
        "run": run, "created": datetime.now(timezone.utc).isoformat(timespec="seconds"), "mock": args.mock,
        "budget_usd": args.budget, "langs": langs, "samples": args.samples, "n_targets": len(targets),
        "arms": [{**a, "spec": config.MODELS[a["model"]].__dict__} for a in arms],
        "sampling_policy": "provider default; Claude 5.5 models accept no temperature",
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    llm = LLM(run_dir, budget_usd=args.budget, mock=args.mock)
    lock = threading.Lock()
    stop = threading.Event()
    counts = {"ok": 0, "refused": 0, "error": 0}

    def work(j: dict) -> dict | None:
        if stop.is_set():
            return None
        arm = j["arm"]
        spec = config.MODELS[arm["model"]]
        try:
            res = llm.call(spec, j["system"], j["user"], max_tokens=config.GEN_MAX_TOKENS,
                           key=f"gen|{run}|{j['item_id']}", tag=f"gen:{arm['name']}:{j['lang']}")
        except BudgetExceeded as e:
            stop.set()
            print(f"\nBUDGET: {e}")
            return None
        row = {
            "item_id": j["item_id"], "target_id": j["target"]["id"], "twin_id": j["target"]["twin"],
            "lang": j["lang"], "arm": arm["name"], "kind": arm["kind"], "model": spec.model,
            "provider": res.provider, "family": spec.family, "sample": j["sample"],
            "text": res.text, "refused": res.refused, "stop_reason": res.stop_reason, "error": res.error,
            "input_tokens": res.input_tokens, "output_tokens": res.output_tokens, "cost_usd": res.cost_usd,
            "latency_s": res.latency_s, "timestamp": res.timestamp, "cached": res.cached,
        }
        with lock:
            with items_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            counts["error" if res.error else "refused" if res.refused else "ok"] += 1
            n = sum(counts.values())
            if n % 25 == 0 or n == len(todo):
                print(f"  {n}/{len(todo)} done  ok={counts['ok']} refused={counts['refused']} "
                      f"error={counts['error']}  spent=${llm.spent_usd:.2f}", flush=True)
        return row

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(work, j) for j in todo]
        for _ in as_completed(futures):
            pass
    print(f"finished in {time.time() - t0:.0f}s: {counts}, spent ${llm.spent_usd:.2f}; items -> {items_path}")
    return 0 if not stop.is_set() else 3


if __name__ == "__main__":
    sys.exit(main())
