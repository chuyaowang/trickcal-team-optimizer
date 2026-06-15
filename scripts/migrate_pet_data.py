"""One-time migration: build data/pets.csv from the old per-server pets.csv.

Pure merge logic lives in merge_rows() and is unit-tested. The __main__ block
reads the per-server files, converts localized rarity/traits to keys via the
i18n tables, merges by signature, writes data/pets.csv (with empty `id`), and
prints any collisions for manual resolution.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd

from src.core.constants import SERVER_LANG
from src.data_loader import vocab_loader

LANGS = ["en", "zh_hans", "zh_hant", "ko"]
NAME_COLS = [f"name_{lang}" for lang in LANGS]
MASTER_COLS = (
    ["id", "rarity_key", "trait_1", "rank_1", "trait_2", "rank_2"] + NAME_COLS
)


@dataclass(frozen=True)
class PetRow:
    lang: str
    name: str
    rarity: str  # rarity KEY
    t1: str
    r1: str
    t2: str
    r2: str

    def signature(self) -> Tuple[str, str, str, str, str]:
        return (self.rarity, self.t1, self.r1, self.t2, self.r2)


def merge_rows(rows: List[PetRow]):
    """Merge rows sharing a signature into one master record per signature.

    Returns (merged_records, collisions). A collision is two rows with the same
    signature AND the same language (ambiguous - can't tell which pet is which).
    """
    by_sig: Dict[tuple, List[PetRow]] = {}
    for row in rows:
        by_sig.setdefault(row.signature(), []).append(row)

    merged: List[dict] = []
    collisions: List[dict] = []
    for sig, group in by_sig.items():
        seen_lang: Dict[str, List[str]] = {}
        for r in group:
            seen_lang.setdefault(r.lang, []).append(r.name)
        clash = {lang: names for lang, names in seen_lang.items() if len(names) > 1}
        if clash:
            for lang, names in clash.items():
                collisions.append({"signature": sig, "lang": lang, "names": names})
            continue
        record = {col: "" for col in MASTER_COLS}
        (record["rarity_key"], record["trait_1"], record["rank_1"],
         record["trait_2"], record["rank_2"]) = sig
        for r in group:
            record[f"name_{r.lang}"] = r.name
        merged.append(record)
    return merged, collisions


def _read_server(server: str) -> List[PetRow]:
    lang = SERVER_LANG[server]
    path = os.path.join("data", server, "pets.csv")
    df = pd.read_csv(path, dtype=str).fillna("")
    rows: List[PetRow] = []
    for _, r in df.iterrows():
        name = r["Pet"].strip()
        if not name:
            continue
        rarity_key = vocab_loader.rarity_key_from_localized(r["Rarity"], lang) or ""
        t1 = vocab_loader.trait_key_from_localized(r["Trait_1"], lang) or ""
        t2 = vocab_loader.trait_key_from_localized(r["Trait_2"], lang) or ""
        rows.append(PetRow(lang, name, rarity_key, t1, r["Rank_1"].strip(),
                           t2, r["Rank_2"].strip()))
    return rows


if __name__ == "__main__":
    all_rows: List[PetRow] = []
    for srv in ["cn", "gl-cn", "gl-en", "kr"]:
        # kr is placeholder Chinese test data -> leave name_ko blank per spec
        if srv == "kr":
            continue
        all_rows.extend(_read_server(srv))

    merged, collisions = merge_rows(all_rows)
    out = pd.DataFrame(merged, columns=MASTER_COLS)
    out.to_csv("data/pets.csv", index=False, encoding="utf-8-sig")
    print(f"Wrote data/pets.csv with {len(merged)} pets (ids blank - fill manually).")
    if collisions:
        print(f"\n{len(collisions)} collision(s) need manual resolution:")
        for c in collisions:
            print(f"  {c['lang']} {c['signature']}: {c['names']}")