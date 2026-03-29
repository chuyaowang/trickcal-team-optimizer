from typing import List, Dict
import os
from src.core.scoring import get_reward_level

def select_server() -> str:
    """让用户选择服务器"""
    servers = {
        '1': ('cn', '中国服 (CN)'),
        '2': ('gl', '国际服 (GL)'),
        '3': ('kr', '韩服 (KR)')
    }
    print("\n===== 选择服务器 =====")
    for k, v in servers.items():
        print(f"{k}. {v[1]}")
    
    while True:
        choice = input("请选择服务器（输入序号）：")
        if choice in servers:
            return servers[choice][0]
        print("无效的选择，请重试。")

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

def select_farm_pets(pets: List[Dict]) -> Dict[str, int]:
    """让用户选择农场拥有的宠物及其数量 (MILP使用)"""
    print("\n===== 选择农场拥有的宠物 (借用) =====")
    print("输入格式: 序号:数量 (例如 1:1 5:3)，用空格分隔")
    while True:
        try:
            choice = input("请选择农场宠物及其数量：")
            if not choice.strip():
                return {}
            
            aux_pets = {}
            parts = choice.split()
            valid = True
            for part in parts:
                if ':' not in part:
                    print(f"格式错误: {part} (应为 序号:数量)")
                    valid = False
                    break
                idx_str, count_str = part.split(':')
                idx = int(idx_str) - 1
                count = int(count_str)
                
                if not (0 <= idx < len(pets)):
                    print(f"无效序号: {idx + 1}")
                    valid = False
                    break
                
                aux_pets[pets[idx]['name']] = count
            
            if valid:
                return aux_pets
        except ValueError:
            print("请输入有效的数字和格式。")

def select_task_count() -> int:
    """让用户选择可执行任务数量 (P参数)"""
    print("\n===== 选择任务数量 (2-5) =====")
    while True:
        try:
            choice = input("请选择可执行任务数量：")
            count = int(choice)
            if 2 <= count <= 5:
                return count
            else:
                print("请输入2到5之间的数字。")
        except ValueError:
            print("请输入有效的数字。")

def display_results(result: Dict, server: str, calc_time: float):
    """输出最优派遣方案结果 (MILP版)"""
    print("\n" + "="*30)
    print("===== 最优派遣方案结果 (MILP) =====")
    print(f"✅ 计算完成！总耗时：{calc_time:.2f} 秒")
    print(f"服务器：{server}")
    
    if result.get('status') != 'Optimal':
        print(f"未找到最优解。状态: {result.get('status')}")
        return

    print(f"总计层级奖励分：{result['total']}")
    print(f"借用宠物总数：{result['borrowed']}")
    print(f"使用宠物总数：{result['total_pets']}")

    for i, assign in enumerate(result['assignments'], 1):
        task = assign['task']
        team = assign['team']
        score = assign['score']
        reward_level = get_reward_level(score, server)
        print(f"\n--- 任务{i} ---")
        print(f"任务名称：{task['task']}")
        print(f"加成特性：{', '.join(task['bonus_skills'])}")
        
        pet_names = [f"{pet['name']}{'（借）' if pet.get('is_borrowed', False) else ''}" for pet in team]
        print(f"派遣宠物：{', '.join(pet_names)}")
        print(f"任务得分：{score}")
        print(f"奖励等级：{reward_level}")
