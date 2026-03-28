import time
import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

from src.data_loader.csv_loader import load_pets, load_tasks, get_available_job_files
from src.core.constants import SKILL_SCORE_MAP
from src.core.scoring import precompute_pet_task_scores
from src.core.assignment import generate_task_combinations, calculate_best_assignment
from src.ui.cli import show_pets, select_owned_pets, select_farm_pets, select_task_count, display_results, select_job_file

def main():
    multiprocessing.freeze_support()
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass

    # 1. 加载数据
    print("正在加载数据...")
    job_files = get_available_job_files()
    if not job_files:
        print("错误：未在data目录下找到任何 jobs_*.csv 文件。")
        return

    selected_job_file = select_job_file(job_files)
    selected_region = os.path.basename(selected_job_file)
    
    pets = load_pets()
    tasks = load_tasks(selected_job_file)

    # 2. 用户交互
    show_pets(pets, SKILL_SCORE_MAP)
    owned_pets = select_owned_pets(pets)
    farm_pets = select_farm_pets(pets)
    task_count = select_task_count()

    # 3. 预计算
    print("\n正在预计算宠物得分...")
    available_pets = owned_pets + farm_pets
    pet_task_scores = precompute_pet_task_scores(available_pets, tasks)

    # 4. 生成任务组合
    print("正在生成任务组合...")
    task_combinations = generate_task_combinations(tasks, task_count)
    
    if not task_combinations:
        print("无法生成指定数量的任务组合。")
        return

    # 5. 并行计算最优方案
    overall_best = {
        'total': -1,
        'borrowed': float('inf'),
        'total_pets': float('inf'),
        'assignments': []
    }

    start_time = time.time()
    cpu_count = multiprocessing.cpu_count()
    print(f"正在使用 {cpu_count} 个CPU核心并行计算...")

    with ProcessPoolExecutor(max_workers=cpu_count) as executor:
        futures = {executor.submit(calculate_best_assignment, combo, available_pets, pet_task_scores): combo for combo in task_combinations}
        
        with tqdm(total=len(futures), desc="计算进度") as pbar:
            for future in as_completed(futures):
                pbar.update(1)
                try:
                    best_score, best_assignments, is_special = future.result()
                    
                    if is_special:
                        # 找到全特级方案，立即停止
                        for f in futures:
                            if not f.done():
                                f.cancel()
                        overall_best.update({
                            'total': best_score['total'],
                            'borrowed': best_score['borrowed'],
                            'total_pets': best_score['total_pets'],
                            'assignments': best_assignments
                        })
                        break

                    # 更新全局最优
                    if best_score['total'] > overall_best['total']:
                        overall_best.update(best_score)
                        overall_best['assignments'] = best_assignments
                    elif best_score['total'] == overall_best['total']:
                        if best_score['borrowed'] < overall_best['borrowed']:
                            overall_best.update(best_score)
                            overall_best['assignments'] = best_assignments
                        elif best_score['borrowed'] == overall_best['borrowed']:
                            if best_score['total_pets'] < overall_best['total_pets']:
                                overall_best.update(best_score)
                                overall_best['assignments'] = best_assignments
                            elif best_score['total_pets'] == overall_best['total_pets']:
                                overall_best['assignments'].extend(best_assignments)
                except Exception as e:
                    print(f"\n计算出错: {e}")

    end_time = time.time()
    
    # 6. 显示结果
    display_results(overall_best, selected_region, end_time - start_time)

    input("\n按回车键退出程序...")

if __name__ == "__main__":
    main()
