"""Load and look up the trait/rarity translation tables.

Translation tables live in data/i18n/*.csv with columns:
    key, en, zh_hans, zh_hant, ko
The `key` is a language-neutral token (e.g. KIND, UNIQUE). Blank cells mean
"no translation yet" and are ignored for reverse lookups.
"""

import os
from functools import lru_cache
from typing import Dict, Optional

import pandas as pd

_I18N_DIR = os.path.join("data", "i18n")
_LANGS = ("en", "zh_hans", "zh_hant", "ko")


@lru_cache(maxsize=None)
def _load_table(filename: str) -> Dict[str, Dict[str, str]]:
    """Return {key: {lang: name}} for non-empty cells."""
    path = os.path.join(_I18N_DIR, filename)
    df = pd.read_csv(path, dtype=str).fillna("")
    table: Dict[str, Dict[str, str]] = {}
    for _, row in df.iterrows():
        key = row["key"].strip()
        if not key:
            continue
        table[key] = {
            lang: row[lang].strip()
            for lang in _LANGS
            if row[lang].strip()
        }
    return table


@lru_cache(maxsize=None)
def _reverse_table(filename: str) -> Dict[str, Dict[str, str]]:
    """Return {lang: {localized_name: key}} from a forward table."""
    reverse: Dict[str, Dict[str, str]] = {}
    for key, names in _load_table(filename).items():
        for lang, name in names.items():
            reverse.setdefault(lang, {})[name] = key
    return reverse


def trait_name(key: str, lang: str) -> str:
    return _load_table("traits.csv").get(key, {}).get(lang, key)


def rarity_name(key: str, lang: str) -> str:
    return _load_table("rarity.csv").get(key, {}).get(lang, key)


def trait_key_from_localized(text: str, lang: str) -> Optional[str]:
    if not text:
        return None
    return _reverse_table("traits.csv").get(lang, {}).get(text.strip())


def rarity_key_from_localized(text: str, lang: str) -> Optional[str]:
    if not text:
        return None
    return _reverse_table("rarity.csv").get(lang, {}).get(text.strip())