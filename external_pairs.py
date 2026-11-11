"""Build the external human-preference pair files that external_anchor.py judges. Third-party text stays out of git.

    uv run --with huggingface_hub --with pandas --with pyarrow python external_pairs.py            # -> ext-data/ (git-ignored)
    uv run --with huggingface_hub --with pandas --with pyarrow python external_pairs.py --out <dir>

Sets:
- FunLines / Humicroedit, SemEval-2020 Task 7 subtask 2 (Hossain et al. 2020; Zenodo record 3969509, CC BY 4.0): two
  edits of the same news headline, five crowd grades 0-3 each; the pair's human pick is the higher mean grade and
  `confidence` is the gap between the two means. Test and dev splits, ties dropped: 4727 pairs.
- New Yorker caption contest ranking task (Hessel et al. 2023; Hugging Face jmhessel/newyorker_caption_contest,
  CC BY 4.0): a finalist caption against a non-finalist for the same cartoon, the cartoon given as the corpus's text
  descriptions (location, description, what is unusual). Test splits of three cross-validation folds: 1554 pairs,
  `confidence` None (no margin is published).
Each line: {id, source, context, a, b, human: "a"|"b", confidence}.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

from common import ROOT, utf8_stdout

FUNLINES_URL = "https://zenodo.org/records/3969509/files/semeval-2020-task-7-dataset.zip?download=1"
NYER_REPO = "jmhessel/newyorker_caption_contest"
NYER_FOLDS = ["ranking", "ranking_1", "ranking_2"]


def funlines(out_dir: Path) -> int:
    zpath = out_dir / "semeval-2020-task-7-dataset.zip"
    if not zpath.exists():
        urllib.request.urlretrieve(FUNLINES_URL, zpath)
    z = zipfile.ZipFile(zpath)
    n = 0
    with (out_dir / "pairs_funlines_test.jsonl").open("w", encoding="utf-8") as f:
        for split in ["test", "dev"]:
            data = z.read(f"semeval-2020-task-7-dataset/subtask-2/{split}.csv").decode("utf-8")
            for r in csv.DictReader(io.StringIO(data)):
                if r["label"] not in ("1", "2"):
                    continue
                orig = re.sub(r"<([^<>]+)/>", r"\1", r["original1"])
                rec = {"id": f"funlines-{split}-{r['id']}", "source": "funlines",
                       "context": f"Original headline: {orig}",
                       "a": re.sub(r"<([^<>]+)/>", r["edit1"], r["original1"], count=1),
                       "b": re.sub(r"<([^<>]+)/>", r["edit2"], r["original2"], count=1),
                       "human": "a" if r["label"] == "1" else "b",
                       "confidence": round(abs(float(r["meanGrade1"]) - float(r["meanGrade2"])), 2)}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
    return n


def nyer(out_dir: Path) -> int:
    import pandas as pd
    from huggingface_hub import hf_hub_download

    n = 0
    with (out_dir / "pairs_nyer_test.jsonl").open("w", encoding="utf-8") as f:
        for fold in NYER_FOLDS:
            p = hf_hub_download(NYER_REPO, f"{fold}/test-00000-of-00001.parquet", repo_type="dataset",
                                local_dir=out_dir / "nyer")
            df = pd.read_parquet(p, columns=["image_location", "image_description", "image_uncanny_description",
                                             "caption_choices", "winner_source", "label", "instance_id"])
            for _, r in df.iterrows():
                choices = list(r["caption_choices"])
                if len(choices) != 2 or r["label"] not in ("A", "B"):
                    continue
                ctx = (f"A New Yorker cartoon. Scene: {r['image_location']}. Description: {r['image_description']} "
                       f"What is unusual: {r['image_uncanny_description']} Two candidate captions follow.")
                rec = {"id": f"nyer-{fold}-{r['instance_id']}", "source": f"nyer-{r['winner_source']}",
                       "context": ctx, "a": choices[0], "b": choices[1],
                       "human": "a" if r["label"] == "A" else "b", "confidence": None}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
    return n


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "ext-data"), help="folder for downloads and pair files (git-ignored)")
    ap.add_argument("--sets", default="funlines,nyer")
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in args.sets.split(","):
        n = {"funlines": funlines, "nyer": nyer}[name](out_dir)
        print(f"{name}: {n} pairs -> {out_dir / ('pairs_' + name + '_test.jsonl')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
