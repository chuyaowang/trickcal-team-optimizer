from typing import List, Dict, Tuple
from src.core.constants import SERVER_REWARD_LEVELS, TIER_REWARD_MAP

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

def get_reward_range(score: int) -> Tuple[int, int]:
    """获取得分对应的奖励范围 (min, max)"""
    if score >= 37: return (13, 13)
    if score >= 25: return (11, 11)
    if score >= 13: return (9, 9)
    if score >= 5: return (7, 8)
    if score >= 1: return (5, 5)
    return (0, 0)

def format_reward_range(lower: int, upper: int) -> str:
    """格式化奖励范围为字符串"""
    if lower == upper:
        return str(lower)
    return f"{lower}-{upper}"

def get_carrot_reward(score: int) -> str:
    """根据得分获取对应的胡萝卜奖励显示字符串"""
    low, high = get_reward_range(score)
    return format_reward_range(low, high)
