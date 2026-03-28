from typing import List, Dict
from src.core.constants import REWARD_LEVELS

def calculate_pet_task_score(pet: Dict, task: Dict):
    """计算宠物对任务的得分"""
    total = 0
    


def precompute_pet_task_scores(pets: List[Dict], tasks: List[Dict]) -> Dict[str, Dict[str, int]]:
    """预计算每个宠物对每个任务的得分"""
    pet_task_scores = {}
    for pet in pets:
        pet_scores = {}
        for task in tasks:
            total = 0
            for skill, score in pet['skill_score'].items():
                if skill in task['bonus_skills']:
                    total += score
            pet_scores[task['task']] = total if total != 0 else pet['rarity_score']
        pet_task_scores[pet['name']] = pet_scores
    return pet_task_scores

def calculate_team_score(combo: List[Dict], task: Dict, pet_task_scores: Dict[str, Dict[str, int]]) -> int:
    """计算宠物组合的总得分"""
    return sum([pet_task_scores[pet['name']][task['task']] for pet in combo])

def get_reward_level(score: int) -> str:
    """根据总得分获取奖励等级"""
    for threshold, level in REWARD_LEVELS:
        if score > threshold:
            return level
    return REWARD_LEVELS[-1][1]
