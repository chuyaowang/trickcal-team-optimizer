import pandas as pd
import os
import glob
from typing import List, Dict
from src.core.constants import RARITY_BASE_MAP, SKILL_SCORE_MAP

def get_available_job_files(data_dir: str = './data') -> List[str]:
    """获取data目录下所有jobs_*.csv文件"""
    pattern = os.path.join(data_dir, 'jobs_*.csv')
    return sorted(glob.glob(pattern))

def load_pets(file_path: str = './data/pets.csv') -> List[Dict]:
    """从CSV读取宠物列表"""
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"未找到{file_path}文件。")
    
    pets = []
    for idx, row in df.iterrows():
        pet_name = row['Pet']
        if pd.isna(pet_name):
            continue
        
        rarity = row['Rarity']
        skill_score = {}
        
        if pd.notna(row['Trait_1']) and pd.notna(row['Rank_1']):
            skill_score[row['Trait_1']] = SKILL_SCORE_MAP.get(row['Rank_1'], 0)
        if pd.notna(row['Trait_2']) and pd.notna(row['Rank_2']):
            skill_score[row['Trait_2']] = SKILL_SCORE_MAP.get(row['Rank_2'], 0)
            
        pets.append({
            'name': pet_name,
            'rarity': rarity,
            'rarity_score': RARITY_BASE_MAP.get(rarity, 2),
            'skill_score': skill_score,
            'is_borrowed': False
        })
    return pets

def load_tasks(file_path: str = './data/jobs_1.csv') -> List[Dict]:
    """从CSV读取任务信息"""
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

    # 填充空任务
    while len(locations) < 5:
        locations.append({
            'task': '',
            'bonus_skills': []
        })
    return locations
