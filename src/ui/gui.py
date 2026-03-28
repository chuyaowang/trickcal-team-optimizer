import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import time
import os
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict

from src.data_loader.csv_loader import load_pets, load_tasks, get_available_job_files
from src.core.constants import SKILL_SCORE_MAP
from src.core.scoring import precompute_pet_task_scores, get_reward_level
from src.core.assignment import generate_task_combinations, calculate_best_assignment

class DispatchCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("宠物派遣计算器")
        self.root.geometry("800x800")
        
        self.pets = []
        self.regions = {}
        self.selected_region = None
        self.owned_pets = []
        self.farm_pets = []
        self.task_count = 1
        self.job_files = []
        
        self.create_widgets()
        self.load_initial_data()
    
    def create_widgets(self):
        title_label = ttk.Label(self.root, text="宠物派遣计算器", font=("Arial", 16))
        title_label.pack(pady=10)
        
        # 任务文件选择
        job_file_frame = ttk.LabelFrame(self.root, text="选择任务文件")
        job_file_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.job_file_var = tk.StringVar()
        self.job_file_combobox = ttk.Combobox(job_file_frame, textvariable=self.job_file_var, state="readonly")
        self.job_file_combobox.pack(padx=10, pady=5, fill=tk.X)
        self.job_file_combobox.bind("<<ComboboxSelected>>", self.on_job_file_selected)

        # 区域选择框架
        region_frame = ttk.LabelFrame(self.root, text="选择派遣区域")
        region_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.region_var = tk.StringVar()
        self.region_combobox = ttk.Combobox(region_frame, textvariable=self.region_var, state="readonly")
        self.region_combobox.pack(padx=10, pady=5, fill=tk.X)
        self.region_combobox.bind("<<ComboboxSelected>>", self.on_region_selected)
        
        pet_frame = ttk.LabelFrame(self.root, text="选择拥有的宠物（可多选）")
        pet_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.owned_pet_listbox = tk.Listbox(pet_frame, selectmode=tk.MULTIPLE, exportselection=0)
        self.owned_pet_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        owned_scroll = ttk.Scrollbar(pet_frame, orient=tk.VERTICAL, command=self.owned_pet_listbox.yview)
        owned_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.owned_pet_listbox.configure(yscrollcommand=owned_scroll.set)
        
        farm_frame = ttk.LabelFrame(self.root, text="选择农场宠物（可多选）")
        farm_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.farm_pet_listbox = tk.Listbox(farm_frame, selectmode=tk.MULTIPLE, exportselection=0)
        self.farm_pet_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        farm_scroll = ttk.Scrollbar(farm_frame, orient=tk.VERTICAL, command=self.farm_pet_listbox.yview)
        farm_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.farm_pet_listbox.configure(yscrollcommand=farm_scroll.set)
        
        task_frame = ttk.LabelFrame(self.root, text="选择任务数量")
        task_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.task_count_var = tk.StringVar()
        self.task_count_combobox = ttk.Combobox(task_frame, textvariable=self.task_count_var, values=["1", "2", "3", "4", "5"], state="readonly")
        self.task_count_combobox.current(0)
        self.task_count_combobox.pack(padx=10, pady=5, fill=tk.X)
        
        calc_button = ttk.Button(self.root, text="计算最优派遣方案", command=self.calculate)
        calc_button.pack(padx=10, pady=10)
        
        result_frame = ttk.LabelFrame(self.root, text="计算结果")
        result_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.result_text.config(state=tk.DISABLED)
    
    def load_initial_data(self):
        try:
            self.job_files = get_available_job_files()
            if not self.job_files:
                messagebox.showerror("错误", "未在data目录下找到任何 jobs_*.csv 文件。")
                self.root.quit()
                return
            
            self.job_file_combobox["values"] = [os.path.basename(f) for f in self.job_files]
            self.job_file_combobox.current(0)
            
            self.pets = load_pets()
            self.load_tasks_for_file(self.job_files[0])
            
            score_to_level = {v: k for k, v in SKILL_SCORE_MAP.items()}
            for pet in self.pets:
                skill_str = ', '.join([f"{k}({score_to_level.get(v, v)})" for k, v in pet['skill_score'].items()])
                info = f"{pet['name']} - {pet['rarity']} - 特性：{skill_str}"
                self.owned_pet_listbox.insert(tk.END, info)
                self.farm_pet_listbox.insert(tk.END, info)
                
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {e}")
            self.root.quit()
            return

    def load_tasks_for_file(self, file_path):
        self.regions = load_tasks(file_path)
        self.region_combobox["values"] = [t['task'] for t in self.regions]
        if self.regions:
            self.region_combobox.current(0)
            self.on_region_selected(None)
        else:
            self.region_var.set("")

    def on_job_file_selected(self, event):
        idx = self.job_file_combobox.current()
        if 0 <= idx < len(self.job_files):
            self.load_tasks_for_file(self.job_files[idx])
    
    def on_region_selected(self, event):
        self.selected_region = self.region_var.get()
    
    def calculate(self):
        if not self.selected_region:
            messagebox.showwarning("警告", "请先选择派遣区域")
            return
        
        selected_owned_indices = self.owned_pet_listbox.curselection()
        if not selected_owned_indices:
            messagebox.showwarning("警告", "请选择至少一只拥有的宠物")
            return
        self.owned_pets = [self.pets[i] for i in selected_owned_indices]
        
        selected_farm_indices = self.farm_pet_listbox.curselection()
        self.farm_pets = []
        for i in selected_farm_indices:
            pet = self.pets[i].copy()
            pet['is_borrowed'] = True
            self.farm_pets.append(pet)
        
        try:
            self.task_count = int(self.task_count_var.get())
        except ValueError:
            messagebox.showwarning("警告", "请选择有效的任务数量")
            return
        
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "正在计算，请稍候...\n")
        self.result_text.update()
        
        available_pets = self.owned_pets + self.farm_pets
        # Find the selected task object
        current_tasks = self.regions # Note: this is a list of tasks for the current file
        pet_task_scores = precompute_pet_task_scores(available_pets, current_tasks)
        
        task_combinations = generate_task_combinations(current_tasks, self.task_count)
        if not task_combinations:
            self.result_text.insert(tk.END, f"无法生成{self.task_count}个任务组合。\n")
            self.result_text.config(state=tk.DISABLED)
            return
        
        overall_best = {'total': -1, 'borrowed': float('inf'), 'total_pets': float('inf'), 'assignments': []}
        start_time = time.time()
        
        self.result_text.insert(tk.END, f"正在使用{multiprocessing.cpu_count()}个CPU核心并行计算...\n")
        self.result_text.update()
        
        try:
            with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
                futures = {executor.submit(calculate_best_assignment, combo, available_pets, pet_task_scores): combo for combo in task_combinations}
                
                for future in as_completed(futures):
                    try:
                        best_score, best_assignments, is_special = future.result()
                        
                        if is_special:
                            for f in futures:
                                if not f.done(): f.cancel()
                            overall_best.update(best_score)
                            overall_best['assignments'] = best_assignments
                            break
                        
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
                        self.result_text.insert(tk.END, f"\n计算出错：{e}\n")
            
            calc_time = time.time() - start_time
            self.result_text.insert(tk.END, f"\n✅ 计算完成！总耗时：{calc_time:.2f} 秒\n")
            
            if not overall_best['assignments']:
                self.result_text.insert(tk.END, "没有找到有效的派遣方案。\n")
            else:
                best_assignment = overall_best['assignments'][0]
                self.result_text.insert(tk.END, f"总得分：{overall_best['total']} | 借用：{overall_best['borrowed']} | 总宠物：{overall_best['total_pets']}\n")
                
                for i, assign in enumerate(best_assignment, 1):
                    task = assign['task']
                    team = assign['team']
                    reward = get_reward_level(assign['score'])
                    self.result_text.insert(tk.END, f"\n--- 任务{i}: {task['task']} ({reward}) ---\n")
                    pet_names = [f"{p['name']}{'（借）' if p.get('is_borrowed', False) else ''}" for p in team]
                    self.result_text.insert(tk.END, f"宠物：{', '.join(pet_names)}\n得分：{assign['score']}\n")
        
        except Exception as e:
            self.result_text.insert(tk.END, f"\n发生错误：{e}\n")
        
        self.result_text.config(state=tk.DISABLED)

def run_gui():
    multiprocessing.freeze_support()
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass
    
    root = tk.Tk()
    app = DispatchCalculatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
