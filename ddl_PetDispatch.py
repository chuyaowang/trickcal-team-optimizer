import pandas as pd
import itertools
from tqdm import tqdm
from typing import List, Dict, Tuple, Optional
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# 技能分值映射
skill_score_map = {
    'C':7,
    'B':12,
    'A':17,
    'S':22
}

def check_dependencies():
    try:
        import pandas
        import openpyxl
    except ImportError:
        print("需要安装pandas和openpyxl库，请运行以下命令：")
        print("pip install pandas openpyxl")
        exit(1)

def read_pet_list() -> List[Dict]:
    """读取宠物列表.xlsx文件"""
    try:
        df = pd.read_excel('./data/宠物列表.xlsx', sheet_name='Sheet1')
    except FileNotFoundError:
        print("错误：未找到./data/宠物列表.xlsx文件，请确保文件存在于data文件夹中。")
        exit(1)
    pets = []
    # 稀有度基础分映射
    rarity_base_map = {
        '普通宠物':2,
        '高级宠物':2,
        '稀有宠物':3,
        '传说宠物':5
    }
    for idx, row in df.iterrows():
        pet_name = row.iloc[0]
        if pd.isna(pet_name):
            continue
        rarity = row.iloc[1]
        skill1 = row.iloc[2]
        skill1_level = row.iloc[3]
        skill2 = row.iloc[4]
        skill2_level = row.iloc[5]

        base_score = rarity_base_map.get(rarity, 2)
        skills = {}
        if pd.notna(skill1) and pd.notna(skill1_level):
            skills[skill1] = skill_score_map.get(skill1_level, 0)
        if pd.notna(skill2) and pd.notna(skill2_level):
            skills[skill2] = skill_score_map.get(skill2_level, 0)

        pets.append({
            'id': idx+1,
            'name': pet_name,
            'rarity': rarity,
            'base_score': base_score,
            'skills': skills,
            'is_borrowed': False  # 默认不是借用的
        })
    return pets

def read_regions() -> Dict[str, List[Dict]]:
    """读取跑腿地区.xlsx文件"""
    try:
        df = pd.read_excel('./data/跑腿地区.xlsx', sheet_name='Sheet1')
    except FileNotFoundError:
        print("错误：未找到./data/跑腿地区.xlsx文件，请确保文件存在于data文件夹中。")
        exit(1)
    regions = {}
    current_region = None
    for idx, row in df.iterrows():
        region_name = row.iloc[0]
        if pd.notna(region_name):
            current_region = region_name
            if current_region not in regions:
                regions[current_region] = []
        if current_region is None:
            continue
        area = row.iloc[1]
        task = row.iloc[2]
        bonus1 = row.iloc[3]
        bonus2 = row.iloc[4]
        bonus_skills = []
        if pd.notna(bonus1):
            bonus_skills.append(bonus1)
        if pd.notna(bonus2):
            bonus_skills.append(bonus2)
        if pd.notna(area) and pd.notna(task):
            regions[current_region].append({
                'area': area,
                'task': task,
                'bonus_skills': bonus_skills,
                'id': len(regions[current_region])  # 任务ID
            })
    # 确保每个区域有5个任务，不足的用空任务填充
    for region in regions:
        while len(regions[region]) <5:
            regions[region].append({
                'area': '',
                'task': '',
                'bonus_skills': [],
                'id': len(regions[region])
            })
    return regions

def show_regions(regions: Dict[str, List[Dict]]) -> str:
    """显示可选区域，让用户选择"""
    print("===== 可选派遣大区域 =====")
    region_list = list(regions.keys())
    for i, region in enumerate(region_list, 1):
        print(f"{i}. {region}")
    while True:
        try:
            choice = input("请选择派遣大区域（输入序号）：")
            selected_idx = int(choice)-1
            if 0 <= selected_idx < len(region_list):
                return region_list[selected_idx]
            else:
                print(f"请输入1到{len(region_list)}之间的序号。")
        except ValueError:
            print("请输入有效的数字序号。")

def show_pets(pets: List[Dict]):
    """显示所有宠物列表"""
    print("===== 所有宠物列表 =====")
    # 创建分值到等级的反向映射
    score_to_level = {v:k for k,v in skill_score_map.items()}
    for pet in pets:
        skill_str = ', '.join([f"{k}({score_to_level[v]})" for k, v in pet['skills'].items()])
        print(f"{pet['id']}. {pet['name']} - {pet['rarity']} - 特性：{skill_str}")

def select_owned_pets(pets: List[Dict]) -> List[Dict]:
    """让用户选择自己拥有的宠物"""
    print("===== 选择自己拥有的宠物 =====")
    while True:
        try:
            choice = input("请选择自己拥有的宠物（输入序号，用空格分隔）：")
            selected_ids = [int(x) for x in choice.split()]
            # 去重
            selected_ids = list(set(selected_ids))
            # 验证序号是否有效
            valid_ids = [pet['id'] for pet in pets]
            invalid_ids = [id for id in selected_ids if id not in valid_ids]
            if invalid_ids:
                print(f"以下序号无效：{', '.join(map(str, invalid_ids))}，请重新输入。")
                continue
            # 返回选中的宠物
            return [pet.copy() for pet in pets if pet['id'] in selected_ids]
        except ValueError:
            print("请输入有效的数字序号，用空格分隔。")

def select_farm_pets(pets: List[Dict]) -> List[Dict]:
    """让用户选择农场拥有的宠物"""
    print("===== 选择农场拥有的宠物 =====")
    while True:
        try:
            choice = input("请选择农场拥有的宠物（输入序号，用空格分隔）：")
            selected_ids = [int(x) for x in choice.split()]
            # 验证序号是否有效
            valid_ids = [pet['id'] for pet in pets]
            invalid_ids = [id for id in selected_ids if id not in valid_ids]
            if invalid_ids:
                print(f"以下序号无效：{', '.join(map(str, invalid_ids))}，请重新输入。")
                continue
            # 生成农场宠物列表，添加is_borrowed标记
            farm_pets = []
            for pet_id in selected_ids:
                for pet in pets:
                    if pet['id'] == pet_id:
                        new_pet = pet.copy()
                        new_pet['is_borrowed'] = True
                        farm_pets.append(new_pet)
                        break
            return farm_pets
        except ValueError:
            print("请输入有效的数字序号，用空格分隔。")

def select_task_count() -> int:
    """让用户选择可执行任务数量"""
    print("===== 选择任务数量 =====")
    while True:
        try:
            choice = input("请选择可执行任务数量（1-5）：")
            count = int(choice)
            if 1 <= count <=5:
                return count
            else:
                print("请输入1到5之间的数字。")
        except ValueError:
            print("请输入有效的数字。")

def precompute_pet_task_scores(pets: List[Dict], tasks: List[Dict]) -> Dict[int, Dict[int, int]]:
    """预计算每个宠物对每个任务的得分"""
    pet_task_scores = {}
    for pet in pets:
        pet_scores = {}
        for task in tasks:
            total = 0
            for skill, score in pet['skills'].items():
                if skill in task['bonus_skills']:
                    total += score
            pet_scores[task['id']] = total if total !=0 else pet['base_score']
        pet_task_scores[pet['id']] = pet_scores
    return pet_task_scores

def calculate_team_score(combo: List[Dict], task: Dict, pet_task_scores: Dict[int, Dict[int, int]]) -> int:
    """计算宠物组合的总得分"""
    return sum([pet_task_scores[pet['id']][task['id']] for pet in combo])

def generate_task_combinations(tasks: List[Dict], task_count: int) -> List[Tuple[Dict]]:
    """生成指定数量的任务组合，优先选择加成技能多的任务"""
    # 过滤掉空任务
    valid_tasks = [task for task in tasks if task['task']]

    # 按加成技能数量排序，优先计算加成技能多的任务组合
    valid_tasks.sort(key=lambda x: len(x['bonus_skills']), reverse=True)

    # 生成指定数量的任务组合
    if len(valid_tasks) >= task_count:
        return list(itertools.combinations(valid_tasks, task_count))
    else:
        # 如果有效任务数量不足，返回空列表
        print(f"警告：该区域只有{len(valid_tasks)}个有效任务，无法选择{task_count}个任务。")
        return []

def assign_no_borrow(task_list: List[Dict], used_pet_mask: int, current_assignments: List[Dict],
                     available_pets: List[Dict], pet_task_scores: Dict[int, Dict[int, int]],
                     task_max_scores_no_borrow: Dict[int, int],
                     best_score: Dict, best_assignments: List[List[Dict]], all_special_found: List[bool]):
    """尝试不使用借用宠物的全特级方案"""
    # 如果已经找到所有任务都达到特级的方案，直接返回
    if all_special_found[0]:
        return

    if not task_list:
        # 计算总得分
        total = sum([assign['score'] for assign in current_assignments])
        # 计算借用的宠物数量
        borrowed = sum([1 for assign in current_assignments for pet in assign['team'] if pet.get('is_borrowed', False)])
        total_pets = sum([len(assign['team']) for assign in current_assignments])

        # 检查是否所有任务都达到特级
        all_special = all([assign['score'] > 37 for assign in current_assignments])

        # 如果找到所有任务都达到特级的方案，标记并保存
        if all_special:
            all_special_found[0] = True
            best_score['total'] = total
            best_score['borrowed'] = borrowed
            best_score['total_pets'] = total_pets
            best_assignments.clear()
            best_assignments.append([a.copy() for a in current_assignments])
        return

    # 处理当前任务
    current_task = task_list[0]

    # 剪枝：如果当前任务不使用借用宠物的最大可能得分都无法达到特级，直接返回
    if task_max_scores_no_borrow[current_task['id']] <= 37:
        return

    # 生成可用宠物列表（只使用自有宠物）
    available = []
    for pet in available_pets:
        if not pet.get('is_borrowed', False):
            # 只使用自己的宠物，且未被使用（使用位运算检查）
            if not (used_pet_mask & (1 << (pet['id'] - 1))):
                available.append(pet)

    # 计算当前任务的最大可能得分（使用可用宠物）
    current_task_max = 0
    pet_scores = []
    for pet in available:
        pet_scores.append(pet_task_scores[pet['id']][current_task['id']])
    pet_scores.sort(reverse=True)
    if pet_scores:
        current_task_max = sum(pet_scores[:min(3, len(pet_scores))])

    # 剪枝：如果当前任务的最大可能得分都无法达到特级，直接返回
    if current_task_max <= 37:
        return

    # 先计算1-3只宠物的组合，优先尝试能达到特级的组合
    # 先生成所有可能的组合，并按得分从高到低排序
    valid_combos = []

    # 优先尝试1只宠物的组合
    for pet in available:
        score = pet_task_scores[pet['id']][current_task['id']]
        if score > 37:
            valid_combos.append(([pet], score, 1, 0))  # 0表示没有借用宠物

    # 尝试2只宠物的组合
    if len(valid_combos) == 0 or current_task_max > max([c[1] for c in valid_combos], default=0):
        if len(available) >=2:
            for combo in itertools.combinations(available, 2):
                score = calculate_team_score(combo, current_task, pet_task_scores)
                if score > 37:
                    valid_combos.append((list(combo), score, 2, 0))

    # 尝试3只宠物的组合
    if len(valid_combos) == 0 or current_task_max > max([c[1] for c in valid_combos], default=0):
        if len(available) >=3:
            for combo in itertools.combinations(available, 3):
                score = calculate_team_score(combo, current_task, pet_task_scores)
                if score > 37:
                    valid_combos.append((list(combo), score, 3, 0))

    # 如果没有能达到特级的组合，返回
    if not valid_combos:
        return

    # 按得分从高到低排序，优先尝试得分高的组合
    valid_combos.sort(key=lambda x: (-x[1], x[2]))

    for combo, score, combo_size, combo_borrowed in valid_combos:
        # 检查任务中没有相同的宠物
        pet_names = [pet['name'] for pet in combo]
        if len(set(pet_names)) != len(pet_names):
            continue

        # 检查自有宠物是否已经被使用（使用位运算）
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

        # 记录分配
        new_assignments = current_assignments + [
            {
                'task': current_task,
                'team': combo,
                'score': score
            }
        ]

        # 递归处理下一个任务
        assign_no_borrow(task_list[1:], new_used_mask, new_assignments,
                         available_pets, pet_task_scores, task_max_scores_no_borrow,
                         best_score, best_assignments, all_special_found)

        # 如果已经找到全特级方案，直接返回
        if all_special_found[0]:
            return

def assign_with_borrow(task_list: List[Dict], used_pet_mask: int, current_assignments: List[Dict],
                       available_pets: List[Dict], pet_task_scores: Dict[int, Dict[int, int]],
                       task_max_scores: Dict[int, int],
                       best_score: Dict, best_assignments: List[List[Dict]], all_special_found: List[bool]):
    """尝试使用借用宠物的全特级方案"""
    # 如果已经找到所有任务都达到特级的方案，直接返回
    if all_special_found[0]:
        return

    if not task_list:
        # 计算总得分
        total = sum([assign['score'] for assign in current_assignments])
        # 计算借用的宠物数量
        borrowed = sum([1 for assign in current_assignments for pet in assign['team'] if pet.get('is_borrowed', False)])
        total_pets = sum([len(assign['team']) for assign in current_assignments])

        # 检查是否所有任务都达到特级
        all_special = all([assign['score'] > 37 for assign in current_assignments])

        # 如果找到所有任务都达到特级的方案，标记并保存
        if all_special:
            all_special_found[0] = True
            best_score['total'] = total
            best_score['borrowed'] = borrowed
            best_score['total_pets'] = total_pets
            best_assignments.clear()
            best_assignments.append([a.copy() for a in current_assignments])
        return

    # 处理当前任务
    current_task = task_list[0]

    # 剪枝：如果当前任务的最大可能得分都无法达到特级，直接返回
    if task_max_scores[current_task['id']] <= 37:
        return

    # 生成可用宠物列表
    available = []
    for pet in available_pets:
        if pet.get('is_borrowed', False):
            # 农场的宠物都可用
            available.append(pet)
        else:
            # 自己的宠物未被使用才可用（使用位运算检查）
            if not (used_pet_mask & (1 << (pet['id'] - 1))):
                available.append(pet)

    # 计算当前任务的最大可能得分（使用可用宠物）
    current_task_max = 0
    pet_scores = []
    for pet in available:
        pet_scores.append(pet_task_scores[pet['id']][current_task['id']])
    pet_scores.sort(reverse=True)
    if pet_scores:
        current_task_max = sum(pet_scores[:min(3, len(pet_scores))])

    # 剪枝：如果当前任务的最大可能得分都无法达到特级，直接返回
    if current_task_max <= 37:
        return

    # 先计算1-3只宠物的组合，优先尝试能达到特级的组合
    # 先生成所有可能的组合，并按得分从高到低排序
    valid_combos = []

    # 优先尝试1只宠物的组合（优先自有宠物）
    for pet in available:
        score = pet_task_scores[pet['id']][current_task['id']]
        if score > 37:
            borrowed = 1 if pet.get('is_borrowed', False) else 0
            valid_combos.append(([pet], score, 1, borrowed))

    # 尝试2只宠物的组合
    if len(valid_combos) == 0 or current_task_max > max([c[1] for c in valid_combos], default=0):
        if len(available) >=2:
            for combo in itertools.combinations(available, 2):
                score = calculate_team_score(combo, current_task, pet_task_scores)
                if score > 37:
                    borrowed = sum(1 for pet in combo if pet.get('is_borrowed', False))
                    valid_combos.append((list(combo), score, 2, borrowed))

    # 尝试3只宠物的组合
    if len(valid_combos) == 0 or current_task_max > max([c[1] for c in valid_combos], default=0):
        if len(available) >=3:
            for combo in itertools.combinations(available, 3):
                score = calculate_team_score(combo, current_task, pet_task_scores)
                if score > 37:
                    borrowed = sum(1 for pet in combo if pet.get('is_borrowed', False))
                    valid_combos.append((list(combo), score, 3, borrowed))

    # 如果没有能达到特级的组合，返回
    if not valid_combos:
        return

    # 按得分从高到低排序，优先尝试得分高的组合，其次是借用宠物少的组合
    valid_combos.sort(key=lambda x: (-x[1], x[3], x[2]))

    # 检查每个任务最多借1只农场宠物
    # 检查总共借用的农场宠物不超过3只
    current_borrowed_total = sum(1 for assign in current_assignments for pet in assign['team'] if pet.get('is_borrowed', False))

    for combo, score, combo_size, combo_borrowed in valid_combos:
        # 检查每个任务最多借1只农场宠物
        if combo_borrowed > 1:
            continue

        # 检查总共借用的农场宠物不超过3只
        if current_borrowed_total + combo_borrowed > 3:
            continue

        # 检查任务中没有相同的宠物
        pet_names = [pet['name'] for pet in combo]
        if len(set(pet_names)) != len(pet_names):
            continue

        # 检查自有宠物是否已经被使用（使用位运算）
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

        # 记录分配
        new_assignments = current_assignments + [
            {
                'task': current_task,
                'team': combo,
                'score': score
            }
        ]

        # 递归处理下一个任务
        assign_with_borrow(task_list[1:], new_used_mask, new_assignments,
                           available_pets, pet_task_scores, task_max_scores,
                           best_score, best_assignments, all_special_found)

        # 如果已经找到全特级方案，直接返回
        if all_special_found[0]:
            return

def assign_normal(task_list: List[Dict], used_pet_mask: int, current_assignments: List[Dict],
                  available_pets: List[Dict], pet_task_scores: Dict[int, Dict[int, int]],
                  best_score: Dict, best_assignments: List[List[Dict]]):
    """普通最优方案寻找"""
    if not task_list:
        # 所有任务分配完毕，计算总得分
        total = sum([assign['score'] for assign in current_assignments])
        borrowed = sum([1 for assign in current_assignments for pet in assign['team'] if pet.get('is_borrowed', False)])
        total_pets = sum([len(assign['team']) for assign in current_assignments])

        # 比较是否更优
        if total > best_score['total']:
            best_score['total'] = total
            best_score['borrowed'] = borrowed
            best_score['total_pets'] = total_pets
            best_assignments.clear()
            best_assignments.append([a.copy() for a in current_assignments])
        elif total == best_score['total']:
            if borrowed < best_score['borrowed']:
                best_score['borrowed'] = borrowed
                best_score['total_pets'] = total_pets
                best_assignments.clear()
                best_assignments.append([a.copy() for a in current_assignments])
            elif borrowed == best_score['borrowed']:
                if total_pets < best_score['total_pets']:
                    best_score['total_pets'] = total_pets
                    best_assignments.clear()
                    best_assignments.append([a.copy() for a in current_assignments])
                elif total_pets == best_score['total_pets']:
                    best_assignments.append([a.copy() for a in current_assignments])
        # 处理完成后返回
        return

    # 剪枝：计算当前总得分加上剩余任务的最大可能得分，如果小于已有的最佳得分，提前终止
    current_total = sum([assign['score'] for assign in current_assignments])

    # 生成可用宠物列表
    available = []
    for pet in available_pets:
        if pet.get('is_borrowed', False):
            # 农场的宠物都可用
            available.append(pet)
        else:
            # 自己的宠物未被使用才可用（使用位运算检查）
            if not (used_pet_mask & (1 << (pet['id'] - 1))):
                available.append(pet)

    # 计算剩余任务的最大可能得分
    remaining_max = 0
    for task in task_list:
        # 计算单个任务的最大可能得分：3只最高得分宠物的得分之和
        pet_scores = []
        for pet in available:
            pet_scores.append(pet_task_scores[pet['id']][task['id']])
        pet_scores.sort(reverse=True)
        remaining_max += sum(pet_scores[:3]) if pet_scores else 0

    # 如果当前总得分加上剩余最大得分小于等于已有最佳得分，提前终止
    if best_score['total'] != -1 and current_total + remaining_max <= best_score['total']:
        return

    # 处理当前任务
    current_task = task_list[0]

    # 先计算2只宠物的最大得分，判断是否需要尝试3只宠物
    max_two_score = 0
    # 先检查是否有至少2只可用宠物
    if len(available) >=2:
        for combo in itertools.combinations(available, 2):
            score = calculate_team_score(combo, current_task, pet_task_scores)
            if score > max_two_score:
                max_two_score = score

    # 生成1-3只宠物的组合，当2只宠物的最大得分已经达到特级，就不需要尝试3只
    for i in range(1,4):
        # 如果是3只宠物，且2只的最大得分已经达到特级，就跳过
        if i == 3 and max_two_score > 37:
            continue
        # 如果可用宠物数量不足i只，跳过
        if len(available) < i:
            continue

        for combo in itertools.combinations(available, i):
            # 检查每个任务最多借1只农场宠物
            combo_borrowed = sum(1 for pet in combo if pet.get('is_borrowed', False))
            if combo_borrowed > 1:
                continue

            # 检查任务中没有相同的宠物
            pet_names = [pet['name'] for pet in combo]
            if len(set(pet_names)) != len(pet_names):
                continue

            # 检查总共借用的农场宠物不超过3只
            current_borrowed = sum(1 for assign in current_assignments for pet in assign['team'] if pet.get('is_borrowed', False))
            if current_borrowed + combo_borrowed > 3:
                continue

            # 检查自有宠物是否已经被使用（使用位运算）
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

            # 计算该组合的得分
            score = calculate_team_score(combo, current_task, pet_task_scores)

            # 记录分配
            new_assignments = current_assignments + [
                {
                    'task': current_task,
                    'team': list(combo),
                    'score': score
                }
            ]

            # 递归处理下一个任务
            assign_normal(task_list[1:], new_used_mask, new_assignments,
                          available_pets, pet_task_scores, best_score, best_assignments)

def calculate_best_assignment(task_combination: Tuple[Dict], available_pets: List[Dict], pet_task_scores: Dict[int, Dict[int, int]]) -> Tuple[Dict, List[List[Dict]], bool]:
    """计算给定任务组合的最佳宠物分配"""
    best_score = {'total': -1, 'borrowed': float('inf'), 'total_pets': float('inf')}
    best_assignments = []
    all_special_found = [False]  # 用列表包装，方便修改

    # 获取自有宠物的最大ID，用于位运算
    owned_pets = [pet for pet in available_pets if not pet.get('is_borrowed', False)]
    max_owned_pet_id = max([pet['id'] for pet in owned_pets], default=0)

    # 预计算每个任务的最大可能得分（使用3只最高得分宠物）
    def calculate_task_max_score(task, use_borrowed=True):
        pet_scores = []
        for pet in available_pets:
            if use_borrowed or not pet.get('is_borrowed', False):
                pet_scores.append(pet_task_scores[pet['id']][task['id']])
        pet_scores.sort(reverse=True)
        return sum(pet_scores[:3]) if pet_scores else 0

    # 预计算每个任务的最大可能得分
    task_max_scores = {}
    task_max_scores_no_borrow = {}
    for task in task_combination:
        task_max_scores[task['id']] = calculate_task_max_score(task)
        task_max_scores_no_borrow[task['id']] = calculate_task_max_score(task, use_borrowed=False)

    # 开始分阶段计算
    # 第一阶段：尝试不使用借用宠物的全特级方案
    assign_no_borrow(list(task_combination), 0, [],
                     available_pets, pet_task_scores, task_max_scores_no_borrow,
                     best_score, best_assignments, all_special_found)

    # 第二阶段：如果第一阶段没有找到，尝试使用借用宠物的全特级方案
    if not all_special_found[0]:
        assign_with_borrow(list(task_combination), 0, [],
                           available_pets, pet_task_scores, task_max_scores,
                           best_score, best_assignments, all_special_found)

    # 第三阶段：如果前两个阶段都没有找到，执行原来的逻辑寻找最优方案
    if not all_special_found[0]:
        assign_normal(list(task_combination), 0, [],
                      available_pets, pet_task_scores, best_score, best_assignments)

    return best_score, best_assignments, all_special_found[0]

def get_reward_level(score: int) -> str:
    """根据总得分获取奖励等级"""
    if score > 37:
        return "特阶"
    elif 25 < score <= 37:
        return "一阶"
    elif 13 < score <= 25:
        return "二阶"
    elif 5 < score <= 13:
        return "三阶"
    elif 1 < score <= 5:
        return "四阶"
    else:
        return "无奖励"

def main():
    # 处理打包后的多进程支持
    multiprocessing.freeze_support()
    # 设置启动方式为spawn，兼容Windows打包
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        # 如果已经设置过启动方式，忽略错误
        pass

    # 检查依赖
    check_dependencies()

    # 读取数据
    pets = read_pet_list()
    regions = read_regions()

    # 用户交互
    selected_region = show_regions(regions)
    tasks = regions[selected_region]
    show_pets(pets)
    owned_pets = select_owned_pets(pets)
    farm_pets = select_farm_pets(pets)
    task_count = select_task_count()

    # 预计算宠物-任务得分矩阵
    print("正在预计算宠物得分...")
    available_pets = owned_pets + farm_pets
    pet_task_scores = precompute_pet_task_scores(available_pets, tasks)

    # 计算最优方案
    print("正在生成任务组合...")
    task_combinations = generate_task_combinations(tasks, task_count)
    if not task_combinations:
        print("无法生成指定数量的任务组合，请重新运行程序并选择较小的任务数量。")
        # 不再直接return，继续执行到末尾的等待代码
    else:
        # 初始化全局最佳
        overall_best = {
            'total': -1,
            'borrowed': float('inf'),
            'total_pets': float('inf'),
            'assignments': []
        }

        # 记录开始时间
        start_time = time.time()

        # 使用并行计算
        print(f"正在使用{multiprocessing.cpu_count()}个CPU核心并行计算最优派遣方案...")

        # 创建进程池
        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            # 提交所有任务组合的计算
            futures = []
            future_to_task = {}  # 映射future到task_combo
            for task_combo in task_combinations:
                valid_tasks = [task for task in task_combo if task['task']]
                if valid_tasks:
                    future = executor.submit(
                        calculate_best_assignment,
                        valid_tasks,
                        available_pets,
                        pet_task_scores
                    )
                    futures.append(future)
                    future_to_task[future] = task_combo

            # 处理完成的任务，使用tqdm显示进度
            all_special_found = False
            processed_count = 0

            with tqdm(total=len(futures), desc="正在计算任务组合") as pbar:
                for future in as_completed(futures):
                    task_combo = future_to_task[future]
                    processed_count += 1
                    pbar.update(1)

                    try:
                        best_score, best_assignments, combo_all_special = future.result()
                    except Exception as e:
                        print(f"\n计算任务组合时出错：{e}")
                        continue

                    # 如果找到全特级方案，立即停止所有计算并输出结果
                    if combo_all_special:
                        # 取消所有未完成的任务
                        for f in futures:
                            if not f.done():
                                f.cancel()

                        # 记录为全局最佳方案
                        overall_best['total'] = best_score['total']
                        overall_best['borrowed'] = best_score['borrowed']
                        overall_best['total_pets'] = best_score['total_pets']
                        overall_best['assignments'] = best_assignments

                        # 跳出循环，准备输出结果
                        all_special_found = True
                        break

                    # 更新全局最佳
                    if best_score['total'] > overall_best['total']:
                        overall_best['total'] = best_score['total']
                        overall_best['borrowed'] = best_score['borrowed']
                        overall_best['total_pets'] = best_score['total_pets']
                        overall_best['assignments'] = best_assignments
                    elif best_score['total'] == overall_best['total']:
                        if best_score['borrowed'] < overall_best['borrowed']:
                            overall_best['borrowed'] = best_score['borrowed']
                            overall_best['total_pets'] = best_score['total_pets']
                            overall_best['assignments'] = best_assignments
                        elif best_score['borrowed'] == overall_best['borrowed']:
                            if best_score['total_pets'] < overall_best['total_pets']:
                                overall_best['total_pets'] = best_score['total_pets']
                                overall_best['assignments'] = best_assignments
                            elif best_score['total_pets'] == overall_best['total_pets']:
                                overall_best['assignments'].extend(best_assignments)

        # 计算总耗时
        end_time = time.time()
        total_calc_time = end_time - start_time

        # 输出结果
        print("\n===== 最优派遣方案结果 =====")
        print(f"✅ 计算完成！方案计算总耗时：{total_calc_time:.2f} 秒")
        print(f"派遣区域：{selected_region}")
        if not overall_best['assignments']:
            print("没有找到有效的派遣方案。")
        else:
            # 取第一个最佳方案
            best_assignment = overall_best['assignments'][0]
            print(f"执行任务数量：{len(best_assignment)}")
            print(f"总得分：{overall_best['total']}")
            print(f"借用宠物数量：{overall_best['borrowed']}")
            print(f"总使用宠物数量：{overall_best['total_pets']}")

            # 输出每个任务
            for i, assign in enumerate(best_assignment, 1):
                task = assign['task']
                team = assign['team']
                score = assign['score']
                reward_level = get_reward_level(score)
                print(f"\n--- 任务{i} ---")
                print(f"任务名称：{task['task']}")
                print(f"任务区域：{task['area']}")
                print(f"加成特性：{', '.join(task['bonus_skills'])}")
                # 处理宠物名称，农场宠物加（借）
                pet_names = []
                for pet in team:
                    if pet.get('is_borrowed', False):
                        pet_names.append(f"{pet['name']}（借）")
                    else:
                        pet_names.append(pet['name'])
                print(f"推荐派遣宠物：{', '.join(pet_names)}")
                print(f"任务得分：{score}")
                print(f"预计奖励等级：{reward_level}")

            # 如果有多个同优先方案，提示用户
            if len(overall_best['assignments']) > 1:
                print(f"\n注：共有{len(overall_best['assignments'])}种同优先的最优方案，以上为其中一种。")

    # 等待用户按键退出
    print("\n按任意键退出程序...")
    try:
        import sys
        if sys.platform == 'win32':
            # Windows系统，使用msvcrt读取任意键
            import msvcrt
            msvcrt.getch()
        else:
            # Linux/macOS系统，使用termios读取任意键
            import termios
            import tty
            fd = sys.stdin.fileno()
            old_terminal_settings = termios.tcgetattr(fd)
            try:
                # 设置为原始模式，读取单个字符
                tty.setraw(fd)
                sys.stdin.read(1)
            finally:
                # 恢复终端设置
                termios.tcsetattr(fd, termios.TCSADRAIN, old_terminal_settings)
    except ImportError:
        # 如果缺少依赖模块，用input()替代
        input()

if __name__ == "__main__":
    main()