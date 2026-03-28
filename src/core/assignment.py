import itertools
from typing import List, Dict, Tuple
from src.core.constants import CONSTRAINTS
from src.core.scoring import calculate_team_score

def assign_no_borrow(task_list: List[Dict], used_pet_mask: int, current_assignments: List[Dict],
                     available_pets: List[Dict], pet_task_scores: Dict[int, Dict[str, int]],
                     task_max_scores_no_borrow: Dict[str, int],
                     best_score: Dict, best_assignments: List[List[Dict]], all_special_found: List[bool]):
    """尝试不使用借用宠物的全特级方案"""
    if all_special_found[0]:
        return

    if not task_list:
        total = sum([assign['score'] for assign in current_assignments])
        borrowed = sum([1 for assign in current_assignments for pet in assign['team'] if pet.get('is_borrowed', False)])
        total_pets = sum([len(assign['team']) for assign in current_assignments])
        all_special = all([assign['score'] > CONSTRAINTS['SPECIAL_SCORE_THRESHOLD'] for assign in current_assignments])

        if all_special:
            all_special_found[0] = True
            best_score['total'] = total
            best_score['borrowed'] = borrowed
            best_score['total_pets'] = total_pets
            best_assignments.clear()
            best_assignments.append([a.copy() for a in current_assignments])
        return

    current_task = task_list[0]
    if task_max_scores_no_borrow[current_task['task']] <= CONSTRAINTS['SPECIAL_SCORE_THRESHOLD']:
        return

    available = []
    for pet in available_pets:
        if not pet.get('is_borrowed', False):
            if not (used_pet_mask & (1 << (pet['id'] - 1))):
                available.append(pet)

    current_task_max = 0
    pet_scores = [pet_task_scores[pet['id']][current_task['task']] for pet in available]
    pet_scores.sort(reverse=True)
    if pet_scores:
        current_task_max = sum(pet_scores[:min(CONSTRAINTS['MAX_PETS_PER_TASK'], len(pet_scores))])

    if current_task_max <= CONSTRAINTS['SPECIAL_SCORE_THRESHOLD']:
        return

    valid_combos = []
    for i in range(1, CONSTRAINTS['MAX_PETS_PER_TASK'] + 1):
        if len(available) >= i:
            for combo in itertools.combinations(available, i):
                score = calculate_team_score(combo, current_task, pet_task_scores)
                if score > CONSTRAINTS['SPECIAL_SCORE_THRESHOLD']:
                    valid_combos.append((list(combo), score, i, 0))

    if not valid_combos:
        return

    valid_combos.sort(key=lambda x: (-x[1], x[2]))

    for combo, score, combo_size, combo_borrowed in valid_combos:
        pet_names = [pet['name'] for pet in combo]
        if len(set(pet_names)) != len(pet_names):
            continue

        combo_owned_ids = [pet['id'] for pet in combo if not pet.get('is_borrowed', False)]
        conflict = False
        new_used_mask = used_pet_mask
        for pet_id in combo_owned_ids:
            if used_pet_mask & (1 << (pet_id - 1)):
                conflict = True
                break
            new_used_mask |= (1 << (pet_id - 1))
        if conflict:
            continue

        assign_no_borrow(task_list[1:], new_used_mask, current_assignments + [{'task': current_task, 'team': combo, 'score': score}],
                         available_pets, pet_task_scores, task_max_scores_no_borrow,
                         best_score, best_assignments, all_special_found)
        if all_special_found[0]:
            return

def assign_with_borrow(task_list: List[Dict], used_pet_mask: int, current_assignments: List[Dict],
                       available_pets: List[Dict], pet_task_scores: Dict[int, Dict[str, int]],
                       task_max_scores: Dict[str, int],
                       best_score: Dict, best_assignments: List[List[Dict]], all_special_found: List[bool]):
    """尝试使用借用宠物的全特级方案"""
    if all_special_found[0]:
        return

    if not task_list:
        total = sum([assign['score'] for assign in current_assignments])
        borrowed = sum([1 for assign in current_assignments for pet in assign['team'] if pet.get('is_borrowed', False)])
        total_pets = sum([len(assign['team']) for assign in current_assignments])
        all_special = all([assign['score'] > CONSTRAINTS['SPECIAL_SCORE_THRESHOLD'] for assign in current_assignments])

        if all_special:
            all_special_found[0] = True
            best_score['total'] = total
            best_score['borrowed'] = borrowed
            best_score['total_pets'] = total_pets
            best_assignments.clear()
            best_assignments.append([a.copy() for a in current_assignments])
        return

    current_task = task_list[0]
    if task_max_scores[current_task['task']] <= CONSTRAINTS['SPECIAL_SCORE_THRESHOLD']:
        return

    available = []
    for pet in available_pets:
        if pet.get('is_borrowed', False) or not (used_pet_mask & (1 << (pet['id'] - 1))):
            available.append(pet)

    current_task_max = 0
    pet_scores = [pet_task_scores[pet['id']][current_task['task']] for pet in available]
    pet_scores.sort(reverse=True)
    if pet_scores:
        current_task_max = sum(pet_scores[:min(CONSTRAINTS['MAX_PETS_PER_TASK'], len(pet_scores))])

    if current_task_max <= CONSTRAINTS['SPECIAL_SCORE_THRESHOLD']:
        return

    valid_combos = []
    for i in range(1, CONSTRAINTS['MAX_PETS_PER_TASK'] + 1):
        if len(available) >= i:
            for combo in itertools.combinations(available, i):
                score = calculate_team_score(combo, current_task, pet_task_scores)
                if score > CONSTRAINTS['SPECIAL_SCORE_THRESHOLD']:
                    borrowed = sum(1 for pet in combo if pet.get('is_borrowed', False))
                    if borrowed <= CONSTRAINTS['MAX_BORROWED_PER_TASK']:
                        valid_combos.append((list(combo), score, i, borrowed))

    if not valid_combos:
        return

    valid_combos.sort(key=lambda x: (-x[1], x[3], x[2]))

    current_borrowed_total = sum(1 for assign in current_assignments for pet in assign['team'] if pet.get('is_borrowed', False))

    for combo, score, combo_size, combo_borrowed in valid_combos:
        if current_borrowed_total + combo_borrowed > CONSTRAINTS['MAX_BORROWED_TOTAL']:
            continue

        pet_names = [pet['name'] for pet in combo]
        if len(set(pet_names)) != len(pet_names):
            continue

        combo_owned_ids = [pet['id'] for pet in combo if not pet.get('is_borrowed', False)]
        conflict = False
        new_used_mask = used_pet_mask
        for pet_id in combo_owned_ids:
            if used_pet_mask & (1 << (pet_id - 1)):
                conflict = True
                break
            new_used_mask |= (1 << (pet_id - 1))
        if conflict:
            continue

        assign_with_borrow(task_list[1:], new_used_mask, current_assignments + [{'task': current_task, 'team': combo, 'score': score}],
                           available_pets, pet_task_scores, task_max_scores,
                           best_score, best_assignments, all_special_found)
        if all_special_found[0]:
            return

def assign_normal(task_list: List[Dict], used_pet_mask: int, current_assignments: List[Dict],
                  available_pets: List[Dict], pet_task_scores: Dict[int, Dict[str, int]],
                  best_score: Dict, best_assignments: List[List[Dict]]):
    """普通最优方案寻找"""
    if not task_list:
        total = sum([assign['score'] for assign in current_assignments])
        borrowed = sum([1 for assign in current_assignments for pet in assign['team'] if pet.get('is_borrowed', False)])
        total_pets = sum([len(assign['team']) for assign in current_assignments])

        if total > best_score['total']:
            best_score.update({'total': total, 'borrowed': borrowed, 'total_pets': total_pets})
            best_assignments.clear()
            best_assignments.append([a.copy() for a in current_assignments])
        elif total == best_score['total']:
            if borrowed < best_score['borrowed']:
                best_score.update({'borrowed': borrowed, 'total_pets': total_pets})
                best_assignments.clear()
                best_assignments.append([a.copy() for a in current_assignments])
            elif borrowed == best_score['borrowed']:
                if total_pets < best_score['total_pets']:
                    best_score['total_pets'] = total_pets
                    best_assignments.clear()
                    best_assignments.append([a.copy() for a in current_assignments])
                elif total_pets == best_score['total_pets']:
                    best_assignments.append([a.copy() for a in current_assignments])
        return

    available = [pet for pet in available_pets if pet.get('is_borrowed', False) or not (used_pet_mask & (1 << (pet['id'] - 1)))]
    
    current_total = sum([assign['score'] for assign in current_assignments])
    remaining_max = 0
    for task in task_list:
        pet_scores = sorted([pet_task_scores[pet['id']][task['task']] for pet in available], reverse=True)
        remaining_max += sum(pet_scores[:CONSTRAINTS['MAX_PETS_PER_TASK']]) if pet_scores else 0

    if best_score['total'] != -1 and current_total + remaining_max <= best_score['total']:
        return

    current_task = task_list[0]
    
    max_two_score = 0
    if len(available) >= 2:
        for combo in itertools.combinations(available, 2):
            score = calculate_team_score(combo, current_task, pet_task_scores)
            if score > max_two_score:
                max_two_score = score

    for i in range(1, CONSTRAINTS['MAX_PETS_PER_TASK'] + 1):
        if i == CONSTRAINTS['MAX_PETS_PER_TASK'] and max_two_score > CONSTRAINTS['SPECIAL_SCORE_THRESHOLD']:
            continue
        if len(available) < i:
            continue

        for combo in itertools.combinations(available, i):
            combo_borrowed = sum(1 for pet in combo if pet.get('is_borrowed', False))
            if combo_borrowed > CONSTRAINTS['MAX_BORROWED_PER_TASK']:
                continue

            pet_names = [pet['name'] for pet in combo]
            if len(set(pet_names)) != len(pet_names):
                continue

            current_borrowed = sum(1 for assign in current_assignments for pet in assign['team'] if pet.get('is_borrowed', False))
            if current_borrowed + combo_borrowed > CONSTRAINTS['MAX_BORROWED_TOTAL']:
                continue

            combo_owned_ids = [pet['id'] for pet in combo if not pet.get('is_borrowed', False)]
            conflict = False
            new_used_mask = used_pet_mask
            for pet_id in combo_owned_ids:
                if used_pet_mask & (1 << (pet_id - 1)):
                    conflict = True
                    break
                new_used_mask |= (1 << (pet_id - 1))
            if conflict:
                continue

            score = calculate_team_score(combo, current_task, pet_task_scores)
            assign_normal(task_list[1:], new_used_mask, current_assignments + [{'task': current_task, 'team': list(combo), 'score': score}],
                          available_pets, pet_task_scores, best_score, best_assignments)

def calculate_best_assignment(task_combination: Tuple[Dict], available_pets: List[Dict], pet_task_scores: Dict[int, Dict[str, int]]) -> Tuple[Dict, List[List[Dict]], bool]:
    """计算给定任务组合的最佳宠物分配"""
    best_score = {'total': -1, 'borrowed': float('inf'), 'total_pets': float('inf')}
    best_assignments = []
    all_special_found = [False]

    def calculate_task_max_score(task, use_borrowed=True):
        pet_scores = sorted([pet_task_scores[pet['id']][task['task']] for pet in available_pets if use_borrowed or not pet.get('is_borrowed', False)], reverse=True)
        return sum(pet_scores[:CONSTRAINTS['MAX_PETS_PER_TASK']]) if pet_scores else 0

    task_max_scores = {task['task']: calculate_task_max_score(task) for task in task_combination}
    task_max_scores_no_borrow = {task['task']: calculate_task_max_score(task, use_borrowed=False) for task in task_combination}

    assign_no_borrow(list(task_combination), 0, [], available_pets, pet_task_scores, task_max_scores_no_borrow, best_score, best_assignments, all_special_found)

    if not all_special_found[0]:
        assign_with_borrow(list(task_combination), 0, [], available_pets, pet_task_scores, task_max_scores, best_score, best_assignments, all_special_found)

    if not all_special_found[0]:
        assign_normal(list(task_combination), 0, [], available_pets, pet_task_scores, best_score, best_assignments)

    return best_score, best_assignments, all_special_found[0]

def generate_task_combinations(tasks: List[Dict], task_count: int) -> List[Tuple[Dict]]:
    """生成指定数量的任务组合，优先选择加成技能多的任务"""
    valid_tasks = sorted([task for task in tasks if task['task']], key=lambda x: len(x['bonus_skills']), reverse=True)
    if len(valid_tasks) >= task_count:
        return list(itertools.combinations(valid_tasks, task_count))
    return []
