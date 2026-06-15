"""One-time migration: build data/pets.csv from the old per-server pets.csv.

Pure merge logic lives in merge_rows() and is unit-tested. The __main__ block
reads the per-server files, converts localized rarity/traits to keys via the
i18n tables, merges by signature, writes data/pets.csv (with empty `id`), and
prints any collisions for manual resolution.
"""

import itertools
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


def _record(sig, names_by_lang: Dict[str, str]) -> dict:
    record = {col: "" for col in MASTER_COLS}
    (record["rarity_key"], record["trait_1"], record["rank_1"],
     record["trait_2"], record["rank_2"]) = sig
    for lang, name in names_by_lang.items():
        record[f"name_{lang}"] = name
    return record


def merge_rows(rows: List[PetRow]):
    """Build master records from per-server rows, grouped by signature.

    Returns (records, expanded). When a signature is unambiguous (at most one
    pet per language) it becomes a single merged record. When a signature is
    shared by multiple pets in some language, we cannot auto-link the names, so
    every combination of names across languages is emitted as a candidate row
    (cartesian product) for the maintainer to prune by deleting wrong matches.
    `expanded` lists those ambiguous signatures with their per-language counts.
    """
    by_sig: Dict[tuple, Dict[str, List[str]]] = {}
    for row in rows:
        by_sig.setdefault(row.signature(), {}).setdefault(row.lang, []).append(row.name)

    records: List[dict] = []
    expanded: List[dict] = []
    for sig, names_by_lang in by_sig.items():
        if all(len(names) <= 1 for names in names_by_lang.values()):
            flat = {lang: names[0] for lang, names in names_by_lang.items()}
            records.append(_record(sig, flat))
            continue
        # ambiguous: cartesian product over each language's candidates
        langs = [lang for lang in LANGS if names_by_lang.get(lang)]
        candidate_lists = [names_by_lang[lang] for lang in langs]
        for combo in itertools.product(*candidate_lists):
            records.append(_record(sig, dict(zip(langs, combo))))
        expanded.append({"signature": sig,
                         "counts": {lang: len(names_by_lang[lang]) for lang in langs}})
    return records, expanded


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

    records, expanded = merge_rows(all_rows)
    out = pd.DataFrame(records, columns=MASTER_COLS)
    out.to_csv("data/pets.csv", index=False, encoding="utf-8-sig")
    print(f"Wrote data/pets.csv with {len(records)} rows (ids blank - fill manually).")
    if expanded:
        print(f"\n{len(expanded)} ambiguous signature(s) emitted as duplicate "
              f"candidate rows - delete the wrong matches:")
        for e in expanded:
            print(f"  {e['signature']}  candidates per lang: {e['counts']}")