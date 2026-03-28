from typing import List, Dict
import os
from src.core.scoring import get_reward_level

def select_job_file(job_files: List[str]) -> str:
    """让用户选择一个任务CSV文件"""
    print("\n===== 可选任务文件 =====")
    for i, file_path in enumerate(job_files, 1):
        print(f"{i}. {os.path.basename(file_path)}")
    
    while True:
        try:
            choice = input("请选择任务文件（输入序号）：")
            selected_idx = int(choice) - 1
            if 0 <= selected_idx < len(job_files):
                return job_files[selected_idx]
            else:
                print(f"请输入1到{len(job_files)}之间的序号。")
        except ValueError:
            print("请输入有效的数字序号。")

def show_pets(pets: List[Dict], skill_scores: Dict[str, int]):
    """显示所有宠物列表"""
    print("\n===== 所有宠物列表 =====")
    score_to_level = {v: k for k, v in skill_scores.items()}
    for i, pet in enumerate(pets, 1):
        skill_str = ', '.join([f"{k}({score_to_level.get(v, v)})" for k, v in pet['skill_score'].items()])
        print(f"{i}. {pet['name']} - {pet['rarity']} - 特性：{skill_str}")

def select_owned_pets(pets: List[Dict]) -> List[Dict]:
    """让用户选择自己拥有的宠物"""
    print("\n===== 选择自己拥有的宠物 =====")
    while True:
        try:
            choice = input("请选择自己拥有的宠物（输入序号，用空格分隔）：")
            selected_indices = [int(x) - 1 for x in choice.split()]
            selected_indices = list(set(selected_indices))
            
            invalid_indices = [idx + 1 for idx in selected_indices if not (0 <= idx < len(pets))]
            if invalid_indices:
                print(f"以下序号无效：{', '.join(map(str, invalid_indices))}，请重新输入。")
                continue
            
            return [pets[idx].copy() for idx in selected_indices]
        except ValueError:
            print("请输入有效的数字序号，用空格分隔。")

def select_farm_pets(pets: List[Dict]) -> List[Dict]:
    """让用户选择农场拥有的宠物"""
    print("\n===== 选择农场拥有的宠物 =====")
    while True:
        try:
            choice = input("请选择农场拥有的宠物（输入序号，用空格分隔）：")
            if not choice.strip():
                return []
            selected_indices = [int(x) - 1 for x in choice.split()]
            
            invalid_indices = [idx + 1 for idx in selected_indices if not (0 <= idx < len(pets))]
            if invalid_indices:
                print(f"以下序号无效：{', '.join(map(str, invalid_indices))}，请重新输入。")
                continue
            
            farm_pets = []
            for idx in selected_indices:
                new_pet = pets[idx].copy()
                new_pet['is_borrowed'] = True
                farm_pets.append(new_pet)
            return farm_pets
        except ValueError:
            print("请输入有效的数字序号，用空格分隔。")

def select_task_count() -> int:
    """让用户选择可执行任务数量"""
    print("\n===== 选择任务数量 =====")
    while True:
        try:
            choice = input("请选择可执行任务数量（1-5）：")
            count = int(choice)
            if 1 <= count <= 5:
                return count
            else:
                print("请输入1到5之间的数字。")
        except ValueError:
            print("请输入有效的数字。")

def display_results(overall_best: Dict, selected_region: str, calc_time: float):
    """输出最优派遣方案结果"""
    print("\n" + "="*30)
    print("===== 最优派遣方案结果 =====")
    print(f"✅ 计算完成！方案计算总耗时：{calc_time:.2f} 秒")
    print(f"派遣区域：{selected_region}")
    
    if not overall_best['assignments']:
        print("没有找到有效的派遣方案。")
        return

    best_assignment = overall_best['assignments'][0]
    print(f"执行任务数量：{len(best_assignment)}")
    print(f"总得分：{overall_best['total']}")
    print(f"借用宠物数量：{overall_best['borrowed']}")
    print(f"总使用宠物数量：{overall_best['total_pets']}")

    for i, assign in enumerate(best_assignment, 1):
        task = assign['task']
        team = assign['team']
        score = assign['score']
        reward_level = get_reward_level(score)
        print(f"\n--- 任务{i} ---")
        print(f"任务名称：{task['task']}")
        print(f"加成特性：{', '.join(task['bonus_skills'])}")
        
        pet_names = [f"{pet['name']}{'（借）' if pet.get('is_borrowed', False) else ''}" for pet in team]
        print(f"推荐派遣宠物：{', '.join(pet_names)}")
        print(f"任务得分：{score}")
        print(f"预计奖励等级：{reward_level}")

    if len(overall_best['assignments']) > 1:
        print(f"\n注：共有{len(overall_best['assignments'])}种同优先的最优方案，以上为其中一种。")
