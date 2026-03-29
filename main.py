import time
from src.data_loader.csv_loader import load_pets, load_tasks, get_available_job_files
from src.core.scoring import precompute_pet_task_scores
from src.core.assignment import calculate_best_assignment
from src.core.constants import SKILL_SCORE_MAP
from src.ui.cli import (
    select_server, select_job_file, show_pets, 
    select_owned_pets, select_farm_pets, select_task_count, 
    display_results
)

def main():
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
    # 注意：我们需要所有宠物（包括可能的借用宠物）对所有任务的得分
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
