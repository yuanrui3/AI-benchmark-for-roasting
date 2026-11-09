"""Run the whole preflight in order, stopping at the first failing stage.

    uv run python run_all.py --mock                       # zero-cost end-to-end test -> runs/mock
    uv run python run_all.py --run pilot --smoke          # 4 targets x 1 sample, real models, a few dollars
    uv run python run_all.py --run pilot --budget 40      # the real thing

The budget is a single run-wide cap: every stage shares runs/<run>/ledger.jsonl, so
the number is the most this run can ever spend. Re-running resumes; nothing is paid twice.

Stages: generate -> specificity -> truth -> damage -> build_pairs -> judge_pairs -> analyze.
Human votes are not part of this: open runs/<run>/rate/index.html, rate, export, drop the
JSON files into runs/<run>/votes/, then run analyze.py again.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(script: str, *args: str) -> int:
    cmd = [sys.executable, str(ROOT / script), *args]
    print(f"\n=== {script} {' '.join(args)} ===", flush=True)
    return subprocess.call(cmd, cwd=ROOT)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--budget", type=float, default=40.0)
    ap.add_argument("--smoke", action="store_true", help="4 targets, 1 sample, 6 damage originals per language")
    ap.add_argument("--targets", type=int, default=None, help="first N targets")
    ap.add_argument("--target-ids", default=None, help="comma list of target ids")
    ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--damage-per-lang", type=int, default=None, help="damage originals per language")
    ap.add_argument("--judge-pairs-per-lang", type=int, default=None, help="judges rate only the first N pairs per language")
    ap.add_argument("--per-lang-pairs", type=int, default=250)
    ap.add_argument("--skip-keys-check", action="store_true")
    args = ap.parse_args()
    run_name = args.run or ("mock" if args.mock else "pilot")
    mock = ["--mock"] if args.mock else []
    budget = ["--budget", str(args.budget)]

    if not args.mock and not args.skip_keys_check:
        if run("check_keys.py") != 0:
            print("no usable key; add keys to .env or use --mock")
            return 2

    gen_extra = ["--targets", "4", "--samples", "1"] if args.smoke else []
    if args.targets:
        gen_extra += ["--targets", str(args.targets)]
    if args.target_ids:
        gen_extra += ["--target-ids", args.target_ids]
    if args.samples:
        gen_extra += ["--samples", str(args.samples)]
    if run("generate.py", "--run", run_name, *mock, *budget, *gen_extra) not in (0,):
        return 1
    if run("specificity.py", "--run", run_name, *mock, *budget) != 0:
        return 1
    if run("truth.py", "--run", run_name, *mock, *budget) != 0:
        return 1
    dmg_extra = ["--per-lang", "6"] if args.smoke else []
    if args.damage_per_lang is not None:
        dmg_extra = ["--per-lang", str(args.damage_per_lang)]
    if run("damage.py", "--run", run_name, *mock, *budget, *dmg_extra) != 0:
        return 1
    pairs_extra = ["--per-lang", "40"] if args.smoke else ["--per-lang", str(args.per_lang_pairs)]
    if run("build_pairs.py", "--run", run_name, *pairs_extra) != 0:
        return 1
    jp_extra = ["--per-lang", str(args.judge_pairs_per_lang)] if args.judge_pairs_per_lang else []
    if run("judge_pairs.py", "--run", run_name, *mock, *budget, *jp_extra) != 0:
        return 1
    if run("analyze.py", "--run", run_name) != 0:
        return 1
    print(f"\nAll stages done. Report: runs/{run_name}/report.md. Rating page: runs/{run_name}/rate/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
