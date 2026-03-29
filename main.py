import time
import argparse
import json
import os
from src.data_loader.csv_loader import load_pets, load_tasks, get_available_job_files
from src.core.scoring import precompute_pet_task_scores, get_reward_level
from src.core.assignment import calculate_best_assignment
from src.core.constants import SKILL_SCORE_MAP
from src.ui.cli import (
    select_server, select_job_file, show_pets, 
    select_owned_pets, select_farm_pets, select_task_count, 
    display_results
)

def run_config(config_path):
    """根据配置文件直接运行计算"""
    if not os.path.exists(config_path):
        print(f"错误: 配置文件 {config_path} 不存在。")
        return

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"错误: 无法读取配置文件。{e}")
        return

    server = config.get('server', 'cn')
    max_active_jobs = config.get('max_job_number', 5)
    owned_pets_list = config.get('owned_pets', [])
    aux_pets_counts = config.get('aux_pets_counts', {})

    # 加载数据
    try:
        all_pets = load_pets(server=server)
    except Exception as e:
        print(f"错误: 无法加载服务器 {server} 的数据。{e}")
        return

    # 找到最新的任务文件 (如果没有指定)
    job_files = get_available_job_files(server=server)
    if not job_files:
        print(f"错误: 未找到任务文件。")
        return
    selected_job_file = job_files[-1] # 默认选最新的
    tasks = load_tasks(selected_job_file)

    # 准备宠物对象
    my_pets = [p for p in all_pets if p['name'] in owned_pets_list]
    
    print(f"正在从配置运行 [{server.upper()}] 服务器计算...")
    print(f"任务文件: {os.path.basename(selected_job_file)}")
    
    start_time = time.time()
    pet_task_scores = precompute_pet_task_scores(all_pets, tasks)
    result = calculate_best_assignment(
        my_pets=my_pets,
        aux_pets_counts=aux_pets_counts,
        tasks=tasks,
        pet_task_scores=pet_task_scores,
        max_active_jobs=max_active_jobs
    )
    calc_time = time.time() - start_time
    display_results(result, server, calc_time)

def main():
    parser = argparse.ArgumentParser(description="宠物派遣最优方案计算器 (MILP)")
    parser.add_argument("--config", type=str, help="配置文件 (.json) 的路径，用于直接运行计算")
    args = parser.parse_args()

    if args.config:
        run_config(args.config)
        return

    # --- 交互式 CLI 逻辑 ---
    # 1. 选择服务器
    server = select_server()
    
    # 2. 加载该服务器的宠物数据
    try:
        all_pets = load_pets(server=server)
    except Exception as e:
        print(f"错误: 无法加载服务器 {server} 的宠物数据。{e}")
        return

    # 3. 选择任务文件并加载
    job_files = get_available_job_files(server=server)
    if not job_files:
        print(f"错误: 在 data/{server} 目录下未找到任务文件。")
        return
    
    selected_job_file = select_job_file(job_files)
    tasks = load_tasks(selected_job_file)

    # 4. 显示宠物并选择
    show_pets(all_pets, SKILL_SCORE_MAP)
    my_pets = select_owned_pets(all_pets)
    aux_pets_counts = select_farm_pets(all_pets)
    
    # 5. 选择任务数量
    max_active_jobs = select_task_count()

    print("\n正在计算最优方案，请稍候...")
    start_time = time.time()

    # 6. 预计算得分
    pet_task_scores = precompute_pet_task_scores(all_pets, tasks)

    # 7. 执行 MILP 计算
    result = calculate_best_assignment(
        my_pets=my_pets,
        aux_pets_counts=aux_pets_counts,
        tasks=tasks,
        pet_task_scores=pet_task_scores,
        max_active_jobs=max_active_jobs
    )

    calc_time = time.time() - start_time

    # 8. 显示结果
    display_results(result, server, calc_time)

if __name__ == "__main__":
    main()
