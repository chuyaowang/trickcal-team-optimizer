import pytest
from src.core.assignment import calculate_best_assignment

def test_milp_solver_sanity():
    # A very simple case with a guaranteed solution
    my_pets = [
        {'name': 'StrongPet', 'rarity_score': 5, 'skill_score': {'Fight': 22}}
    ]
    tasks = [
        {'task': 'BossFight', 'bonus_skills': ['Fight']}
    ]
    # (Pet, Task) Score Matrix
    pet_task_scores = {
        ('StrongPet', 'BossFight'): 22
    }
    
    result = calculate_best_assignment(
        my_pets=my_pets,
        aux_pets_counts={},
        tasks=tasks,
        pet_task_scores=pet_task_scores,
        max_active_jobs=1
    )
    
    assert result['status'] == 'Optimal'
    assert len(result['assignments']) == 1
    assert result['assignments'][0]['task']['task'] == 'BossFight'
    assert result['assignments'][0]['team'][0]['name'] == 'StrongPet'
    assert result['assignments'][0]['score'] == 22

def test_borrow_limit_constraint():
    # 2 tasks requiring specific skills
    # User only has 1 matching pet, needs to borrow
    my_pets = [
        # Give MyPet a very high score to ensure it's picked to hit a higher tier
        {'name': 'MyPet', 'rarity_score': 2, 'skill_score': {'A': 37}}
    ]
    # Friends have pets
    aux_pets_counts = {'FriendPet': 2}
    
    tasks = [
        {'task': 'Task1', 'bonus_skills': ['A']},
        {'task': 'Task2', 'bonus_skills': ['A']}
    ]
    
    # Precomputed scores
    pet_task_scores = {
        ('MyPet', 'Task1'): 37,
        ('MyPet', 'Task2'): 37,
        ('FriendPet', 'Task1'): 22,
        ('FriendPet', 'Task2'): 22
    }
    
    result = calculate_best_assignment(
        my_pets=my_pets,
        aux_pets_counts=aux_pets_counts,
        tasks=tasks,
        pet_task_scores=pet_task_scores,
        max_active_jobs=2
    )
    assert len(result['assignments']) == 2
    
    # Total borrowed should be 1 because MyPet hits a higher tier (37) than FriendPet (22)
    assert result['borrowed'] == 1
