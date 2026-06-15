#!/usr/bin/env python3
"""Validate pet data integrity. Exits non-zero on errors; warnings don't fail.

Checks:
  - every trait in every jobs_*.csv resolves to a key (per server language);
    servers whose language has no translations yet (e.g. kr/ko) are skipped
  - every trait_*/rarity_key in pets.csv exists in the i18n tables
  - warn on pets whose id has no icon file, and on duplicate ids
"""

import glob
import os
import sys

import pandas as pd

from src.core.constants import SERVER_LANG
from src.data_loader import vocab_loader


def find_unknown_job_traits(jobs_path, known_localized_to_key):
    df = pd.read_csv(jobs_path).fillna("")
    unknown = []
    for _, row in df.iterrows():
        for col in ("Trait 1", "Trait 2"):
            text = str(row.get(col, "")).strip()
            if text and text not in known_localized_to_key:
                unknown.append(text)
    return unknown


def main(data_dir="data"):
    errors, warnings = [], []

    traits = vocab_loader._load_table("traits.csv")
    rarity = vocab_loader._load_table("rarity.csv")
    trait_keys = set(traits)
    rarity_keys = set(rarity)

    # jobs traits resolve (skip languages with no translations yet)
    for server, lang in SERVER_LANG.items():
        known = vocab_loader._reverse_table("traits.csv").get(lang, {})
        if not known:
            warnings.append(f"{server}: language '{lang}' has no trait "
                            f"translations yet; skipping its jobs files")
            continue
        for jobs_path in glob.glob(os.path.join(data_dir, server, "jobs_*.csv")):
            for text in find_unknown_job_traits(jobs_path, known):
                errors.append(f"{jobs_path}: trait '{text}' has no key for {lang}")

    # master keys exist + icon/id checks
    master = pd.read_csv(os.path.join(data_dir, "pets.csv"), dtype=str).fillna("")
    seen_ids = {}
    for i, row in master.iterrows():
        for col in ("trait_1", "trait_2"):
            k = row[col].strip()
            if k and k not in trait_keys:
                errors.append(f"pets.csv row {i}: unknown trait key '{k}'")
        rk = row["rarity_key"].strip()
        if rk and rk not in rarity_keys:
            errors.append(f"pets.csv row {i}: unknown rarity key '{rk}'")
        pid = row["id"].strip()
        if pid:
            seen_ids[pid] = seen_ids.get(pid, 0) + 1
            icon = os.path.join(data_dir, "pet_images", f"{pid}.png")
            if not os.path.exists(icon):
                warnings.append(f"pets.csv row {i}: no icon for id {pid}")
    for pid, n in seen_ids.items():
        if n > 1:
            errors.append(f"pets.csv: duplicate id {pid} ({n} rows)")

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if errors:
        print(f"\n{len(errors)} error(s).")
        return 1
    print(f"OK ({len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
