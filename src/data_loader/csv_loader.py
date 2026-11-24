import pandas as pd
import os
import glob
from typing import List, Dict
from src.core.constants import SKILL_SCORE_MAP, RARITY_BASE_SCORE, SERVER_LANG, DEFAULT_SERVER
from src.data_loader import vocab_loader

def get_available_mission_files(data_dir: str = './data') -> List[str]:
    """List the central missions_YYMMDD.csv files (shared by all servers), oldest first."""
    return sorted(glob.glob(os.path.join(data_dir, 'missions', 'missions_*.csv')))

def load_missions(file_path: str, lang: str) -> List[Dict]:
    """Load a central missions file as task dicts with text in `lang`.

    Rows are `location,trait_1,trait_2` keys. Location/task text comes from
    data/i18n/locations.csv (English fallback). Unknown keys raise ValueError.
    """
    df = pd.read_csv(file_path, dtype=str, encoding="utf-8-sig").fillna("")
    known_traits = vocab_loader._load_table("traits.csv")
    tasks = []
    for _, row in df.iterrows():
        loc_key = row["location"].strip()
        try:
            location, task = vocab_loader.location_text(loc_key, lang)
        except KeyError:
            raise ValueError(f"{file_path}: unknown location key '{loc_key}'")
        bonus_skills = []
        for col in ("trait_1", "trait_2"):
            trait = row[col].strip()
            if not trait:
                continue
            if trait not in known_traits:
                raise ValueError(f"{file_path}: unknown trait key '{trait}'")
            bonus_skills.append(trait)
        tasks.append({'task': f"{location} - {task}", 'bonus_skills': bonus_skills})
    return tasks

def load_pets(server: str = DEFAULT_SERVER, data_dir: str = './data') -> List[Dict]:
    """Load pets available on `server` from the canonical master.

    Availability = the pet has a non-empty name in the server's language.
    Traits are returned as language-neutral keys in `skill_score`.
    """
    lang = SERVER_LANG[server]
    file_path = os.path.join(data_dir, 'pets.csv')
    try:
        df = pd.read_csv(file_path, dtype=str).fillna("")
    except FileNotFoundError:
        raise FileNotFoundError(f"未找到{file_path}文件。")

    name_col = f"name_{lang}"
    pets = []
    for _, row in df.iterrows():
        name = row.get(name_col, "").strip()
        if not name:
            continue

        skill_score = {}
        for trait_col, rank_col in (("trait_1", "rank_1"), ("trait_2", "rank_2")):
            trait_key = row[trait_col].strip()
            rank = row[rank_col].strip()
            if trait_key and rank:
                skill_score[trait_key] = SKILL_SCORE_MAP.get(rank, 0)

        rarity_key = row["rarity_key"].strip()
        pet_id = row["id"].strip()
        icon = os.path.join(data_dir, "pet_images", f"{pet_id}.png")
        pets.append({
            'name': name,
            'id': pet_id or None,
            'icon': icon if pet_id and os.path.exists(icon) else None,
            'rarity_key': rarity_key,
            # localized rarity string kept for backward compat (cli.py, gui.py)
            'rarity': vocab_loader.rarity_name(rarity_key, lang),
            'rarity_score': RARITY_BASE_SCORE.get(rarity_key, 2),
            'skill_score': skill_score,
            'is_borrowed': False,
        })
    return pets
