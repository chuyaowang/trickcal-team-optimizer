import pandas as pd
import os
import glob
from typing import List, Dict
from src.core.constants import SKILL_SCORE_MAP, RARITY_BASE_SCORE, SERVER_LANG
from src.data_loader import vocab_loader

def get_available_job_files(server: str = 'cn', data_dir: str = './data') -> List[str]:
    """获取指定服务器目录下的所有jobs_*.csv文件"""
    pattern = os.path.join(data_dir, server, 'jobs_*.csv')
    return sorted(glob.glob(pattern))

def load_pets(server: str = 'cn', data_dir: str = './data') -> List[Dict]:
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

def load_tasks(file_path: str) -> List[Dict]:
    """从指定路径读取任务信息"""
    locations = []
    try:
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            location_name = row['Location']
            if pd.isna(location_name):
                continue

            bonus_skills = []
            if pd.notna(row['Trait 1']):
                bonus_skills.append(row['Trait 1'])
            if pd.notna(row['Trait 2']):
                bonus_skills.append(row['Trait 2'])

            locations.append({
                'task': f"{location_name} - {row['Task']}",
                'bonus_skills': bonus_skills
            })
    except FileNotFoundError:
        print(f"警告：未找到{file_path}文件。")

    return locations
