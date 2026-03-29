import pytest
from src.core.scoring import calculate_pet_score_for_task, get_reward_level

def test_calculate_pet_score_for_task():
    # Mock data
    pet = {
        'name': 'TestPet',
        'rarity_score': 5,
        'skill_score': {'Confident': 22, 'Sharp': 12}
    }
    task_with_match = {
        'task': 'TestTask',
        'bonus_skills': ['Confident']
    }
    task_with_multiple_matches = {
        'task': 'TestTaskMulti',
        'bonus_skills': ['Confident', 'Sharp']
    }
    task_with_no_match = {
        'task': 'TestTaskNone',
        'bonus_skills': ['Social']
    }

    # Test match
    assert calculate_pet_score_for_task(pet, task_with_match) == 22
    # Test multiple matches
    assert calculate_pet_score_for_task(pet, task_with_multiple_matches) == 34
    # Test no match (returns rarity score)
    assert calculate_pet_score_for_task(pet, task_with_no_match) == 5

def test_get_reward_level():
    # Test CN server labels
    assert get_reward_level(37, 'cn') == '特阶'
    assert get_reward_level(25, 'cn') == '一阶'
    assert get_reward_level(0, 'cn') == '无奖励'

    # Test GL server labels
    assert get_reward_level(37, 'gl-cn') == 'S'
    assert get_reward_level(25, 'gl-cn') == 'A'
    assert get_reward_level(0, 'gl-cn') == 'N/A'
    
    # Test GL-EN server labels
    assert get_reward_level(37, 'gl-en') == 'S'
