from typing import List, Dict, Tuple
from src.core.constants import SERVER_REWARD_LEVELS

def calculate_pet_score_for_task(pet: Dict, task: Dict) -> int:
    """计算单个宠物在特定任务下的得分"""
    bonus_score = sum(
        score for skill, score in pet['skill_score'].items() 
        if skill in task['bonus_skills']
    )
    # 如果没有技能加成，则使用稀有度基础分
    return bonus_score if bonus_score > 0 else pet['rarity_score']

def precompute_pet_task_scores(pets: List[Dict], tasks: List[Dict]) -> Dict[Tuple[str, str], int]:
    """预计算每个宠物对每个任务的得分"""
    return {
        (pet['name'], task['task']): calculate_pet_score_for_task(pet, task)
        for pet in pets
        for task in tasks
    }

def calculate_team_score(combo: List[Dict], task: Dict, pet_task_scores: Dict[Tuple[str, str], int]) -> int:
    """计算宠物组合的总得分"""
    return sum(pet_task_scores[(pet['name'], task['task'])] for pet in combo)

def get_reward_level(score: int, server: str = 'cn') -> str:
    """根据总得分获取奖励等级"""
    levels = SERVER_REWARD_LEVELS.get(server, SERVER_REWARD_LEVELS['cn'])
    for threshold, level in levels:
        if score >= threshold:
            return level
    return levels[-1][1]
