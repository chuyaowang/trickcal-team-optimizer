from typing import List, Dict
import os
from src.core.scoring import get_reward_level, get_carrot_reward, format_reward_range
from src.core.i18n import t

def select_server(lang='cn') -> str:
    """让用户选择服务器"""
    server_names = t('SERVER_NAMES', lang)
    server_list = list(server_names.keys())
    
    print(f"\n===== {t('SELECT_SERVER', lang)} =====")
    for i, s_key in enumerate(server_list, 1):
        print(f"{i}. {server_names[s_key]}")
    
    while True:
        try:
            choice = input(f"{t('SELECT_SERVER', lang)}: ")
            idx = int(choice) - 1
            if 0 <= idx < len(server_list):
                return server_list[idx]
            else:
                print(f"1-{len(server_list)}")
        except ValueError:
            print("Number only")

def select_job_file(job_files: List[str], lang='cn') -> str:
    """让用户选择一个任务CSV文件"""
    print(f"\n===== {t('SELECT_JOB_FILE', lang)} =====")
    for i, file_path in enumerate(job_files, 1):
        print(f"{i}. {os.path.basename(file_path)}")
    
    while True:
        try:
            choice = input(f"{t('SELECT_JOB_FILE', lang)}: ")
            selected_idx = int(choice) - 1
            if 0 <= selected_idx < len(job_files):
                return job_files[selected_idx]
            else:
                print(f"1-{len(job_files)}")
        except ValueError:
            print("Number only")

def show_pets(pets: List[Dict], skill_scores: Dict[str, int], lang='cn'):
    """显示所有宠物列表"""
    print(f"\n===== {t('MY_PETS', lang)} =====")
    score_to_level = {v: k for k, v in skill_scores.items()}
    for i, pet in enumerate(pets, 1):
        skill_str = ', '.join([f"{k}({score_to_level.get(v, v)})" for k, v in pet['skill_score'].items()])
        print(f"{i}. {pet['name']} - {pet['rarity']} - {skill_str}")

def select_owned_pets(pets: List[Dict], lang='cn') -> List[Dict]:
    """让用户选择自己拥有的宠物"""
    print(f"\n===== {t('MY_PETS', lang)} =====")
    while True:
        try:
            choice = input(t('CLI_PET_SELECTION', lang))
            selected_indices = [int(x) - 1 for x in choice.split()]
            selected_indices = list(set(selected_indices))
            
            invalid_indices = [idx + 1 for idx in selected_indices if not (0 <= idx < len(pets))]
            if invalid_indices:
                print(f"Invalid: {', '.join(map(str, invalid_indices))}")
                continue
            
            return [pets[idx].copy() for idx in selected_indices]
        except ValueError:
            print("Number only")

def select_farm_pets(pets: List[Dict], lang='cn') -> Dict[str, int]:
    """让用户选择农场拥有的宠物及其数量"""
    print(f"\n===== {t('BORROW_PETS', lang)} =====")
    while True:
        try:
            print(t('CLI_BORROW_EXAMPLE', lang))
            choice = input(": ")
            if not choice.strip():
                return {}
            
            aux_pets = {}
            parts = choice.split()
            valid = True
            for part in parts:
                if ':' not in part:
                    valid = False
                    break
                idx_str, count_str = part.split(':')
                idx = int(idx_str) - 1
                count = int(count_str)
                
                if not (0 <= idx < len(pets)):
                    valid = False
                    break
                
                aux_pets[pets[idx]['name']] = count
            
            if valid:
                return aux_pets
            print("Invalid format")
        except ValueError:
            print("Number only")

def select_task_count(lang='cn') -> int:
    """让用户选择可执行任务数量"""
    print(f"\n===== {t('MAX_JOBS', lang)} =====")
    while True:
        try:
            choice = input(f"{t('MAX_JOBS', lang)}: ")
            count = int(choice)
            if 2 <= count <= 5:
                return count
            else:
                print("2-5")
        except ValueError:
            print("Number only")

def display_results(result: Dict, server: str, lang='cn', calc_time: float = 0.0):
    """输出最优派遣方案结果"""
    print("\n" + "="*30)
    print(f"===== {t('RESULTS', lang)} =====")
    print(f"✅ {t('OPTIMAL_FOUND', lang)} | {t('CALC_TIME', lang)}: {calc_time:.2f} s")
    
    if result.get('status') != 'Optimal':
        print(t('NO_OPTIMAL', lang).format(result.get('status')))
        return

    total_str = format_reward_range(result['min_total'], result['max_total'])
    print(f"{t('TOTAL_REWARD', lang)}: {total_str} 🥕")
    print(f"{t('TOTAL_BORROWED', lang)}: {result['borrowed']}")

    for i, assign in enumerate(result['assignments'], 1):
        task = assign['task']
        team = assign['team']
        score = assign['score']
        reward_level = get_reward_level(score, server)
        carrot_reward = get_carrot_reward(score)
        print(f"\n--- {t('STATUS', lang)} {i} ---")
        print(f"{t('TASK_NAME', lang)}: {task['task']}")
        
        borrow_tag = " (借)" if lang == 'cn' else " (Borrow)"
        pet_names = [f"{pet['name']}{borrow_tag if pet.get('is_borrowed', False) else ''}" for pet in team]
        print(f"{t('DISPATCH_TEAM', lang)}: {', '.join(pet_names)}")
        print(f"{t('RAW_SCORE', lang)}: {score} -> {reward_level} ({carrot_reward} 🥕)")
