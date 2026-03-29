import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import time
import os
from typing import List, Dict

from src.data_loader.csv_loader import load_pets, load_tasks, get_available_job_files
from src.core.constants import SKILL_SCORE_MAP
from src.core.scoring import precompute_pet_task_scores, get_reward_level
from src.core.assignment import calculate_best_assignment

class DispatchCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("宠物派遣计算器 (Basic)")
        self.root.geometry("900x900")
        
        self.all_pets = []
        self.current_tasks = []
        self.owned_pets = []
        self.aux_pets_counts = {} # {pet_name: count}
        self.job_files = []
        self.server = 'cn'
        
        self.create_widgets()
        self.load_server_data()
    
    def create_widgets(self):
        # 标题
        title_label = ttk.Label(self.root, text="宠物派遣计算器", font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        
        # 服务器选择
        server_frame = ttk.LabelFrame(self.root, text="1. 选择服务器")
        server_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.server_var = tk.StringVar(value="cn")
        servers = [("中国服 (CN)", "cn"), ("国际服 (GL-CN)", "gl-cn"), ("国际服 (GL-EN)", "gl-en"), ("韩服 (KR)", "kr")]
        for text, mode in servers:
            ttk.Radiobutton(server_frame, text=text, variable=self.server_var, value=mode, command=self.on_server_change).pack(side=tk.LEFT, padx=15, pady=5)

        # 任务文件选择
        job_file_frame = ttk.LabelFrame(self.root, text="2. 选择任务文件")
        job_file_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.job_file_var = tk.StringVar()
        self.job_file_combobox = ttk.Combobox(job_file_frame, textvariable=self.job_file_var, state="readonly")
        self.job_file_combobox.pack(padx=10, pady=5, fill=tk.X)
        self.job_file_combobox.bind("<<ComboboxSelected>>", self.on_job_file_selected)

        # 宠物选择区域 (左右分栏)
        pet_selection_frame = ttk.Frame(self.root)
        pet_selection_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # 左侧：拥有宠物
        owned_frame = ttk.LabelFrame(pet_selection_frame, text="3. 选择自己拥有的宠物 (可多选)")
        owned_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        self.owned_listbox = tk.Listbox(owned_frame, selectmode=tk.MULTIPLE, exportselection=0)
        self.owned_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        owned_scroll = ttk.Scrollbar(owned_frame, orient=tk.VERTICAL, command=self.owned_listbox.yview)
        owned_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.owned_listbox.configure(yscrollcommand=owned_scroll.set)
        
        # 右侧：借用宠物
        farm_frame = ttk.LabelFrame(pet_selection_frame, text="4. 选择并设置借用宠物数量")
        farm_frame.pack(side=tk.RIGHT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        self.farm_tree = ttk.Treeview(farm_frame, columns=("name", "count"), show="headings", height=10)
        self.farm_tree.heading("name", text="宠物名称")
        self.farm_tree.heading("count", text="数量 (双击修改)")
        self.farm_tree.column("count", width=100, anchor=tk.CENTER)
        self.farm_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        farm_scroll = ttk.Scrollbar(farm_frame, orient=tk.VERTICAL, command=self.farm_tree.yview)
        farm_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.farm_tree.configure(yscrollcommand=farm_scroll.set)
        self.farm_tree.bind("<Double-1>", self.on_farm_pet_double_click)

        # 任务数量选择
        task_count_frame = ttk.Frame(self.root)
        task_count_frame.pack(padx=10, pady=5, fill=tk.X)
        
        ttk.Label(task_count_frame, text="同时执行任务数量 (P):").pack(side=tk.LEFT, padx=5)
        self.task_count_var = tk.StringVar(value="5")
        self.task_count_combobox = ttk.Combobox(task_count_frame, textvariable=self.task_count_var, values=["2", "3", "4", "5"], width=5, state="readonly")
        self.task_count_combobox.pack(side=tk.LEFT, padx=5)
        
        # 计算按钮
        self.calc_button = ttk.Button(self.root, text="开始计算最优派遣方案", command=self.calculate)
        self.calc_button.pack(padx=10, pady=10)
        
        # 结果显示
        result_frame = ttk.LabelFrame(self.root, text="计算结果")
        result_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=("Arial", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.result_text.config(state=tk.DISABLED)

    def on_server_change(self):
        self.server = self.server_var.get()
        self.load_server_data()

    def load_server_data(self):
        try:
            # 加载宠物
            self.all_pets = load_pets(server=self.server)
            
            # 更新列表
            self.owned_listbox.delete(0, tk.END)
            for item in self.farm_tree.get_children():
                self.farm_tree.delete(item)
            
            score_to_level = {v: k for k, v in SKILL_SCORE_MAP.items()}
            for pet in self.all_pets:
                skill_str = ', '.join([f"{k}({score_to_level.get(v, v)})" for k, v in pet['skill_score'].items()])
                info = f"{pet['name']} ({pet['rarity']}) - {skill_str}"
                self.owned_listbox.insert(tk.END, info)
                self.farm_tree.insert("", tk.END, values=(pet['name'], 0))
            
            # 加载任务文件
            self.job_files = get_available_job_files(server=self.server)
            if self.job_files:
                self.job_file_combobox["values"] = [os.path.basename(f) for f in self.job_files]
                self.job_file_combobox.current(0)
                self.on_job_file_selected(None)
            else:
                self.job_file_combobox["values"] = []
                self.job_file_var.set("未找到任务文件")
                
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {e}")

    def on_job_file_selected(self, event):
        idx = self.job_file_combobox.current()
        if 0 <= idx < len(self.job_files):
            self.current_tasks = load_tasks(self.job_files[idx])

    def on_farm_pet_double_click(self, event):
        item_id = self.farm_tree.identify_row(event.y)
        if not item_id:
            return
        
        current_values = self.farm_tree.item(item_id, "values")
        pet_name = current_values[0]
        current_count = current_values[1]
        
        new_count = simpledialog.askinteger("修改数量", f"请输入可借用的 {pet_name} 数量:", initialvalue=int(current_count), minvalue=0, maxvalue=20)
        if new_count is not None:
            self.farm_tree.item(item_id, values=(pet_name, new_count))

    def calculate(self):
        if not self.current_tasks:
            messagebox.showwarning("警告", "请先选择有效的任务文件")
            return
        
        # 获取拥有的宠物
        selected_owned_indices = self.owned_listbox.curselection()
        if not selected_owned_indices:
            messagebox.showwarning("警告", "请选择至少一只拥有的宠物")
            return
        owned_pets = [self.all_pets[i] for i in selected_owned_indices]
        
        # 获取借用的宠物数量
        aux_pets_counts = {}
        for item in self.farm_tree.get_children():
            name, count = self.farm_tree.item(item, "values")
            count = int(count)
            if count > 0:
                aux_pets_counts[name] = count
        
        try:
            p_limit = int(self.task_count_var.get())
        except ValueError:
            p_limit = 5
        
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"正在计算 [{self.server.upper()}] 服务器的最优方案 (MILP solver)...\n")
        self.result_text.update()
        
        start_time = time.time()
        
        try:
            # 1. 预计算得分
            pet_task_scores = precompute_pet_task_scores(self.all_pets, self.current_tasks)
            
            # 2. 调用 MILP 计算
            result = calculate_best_assignment(
                my_pets=owned_pets,
                aux_pets_counts=aux_pets_counts,
                tasks=self.current_tasks,
                pet_task_scores=pet_task_scores,
                max_active_jobs=p_limit
            )
            
            calc_time = time.time() - start_time
            self.display_result(result, calc_time)
            
        except Exception as e:
            self.result_text.insert(tk.END, f"\n❌ 计算发生错误：\n{str(e)}\n")
            import traceback
            print(traceback.format_exc())
        
        self.result_text.config(state=tk.DISABLED)

    def display_result(self, result: Dict, calc_time: float):
        if result.get('status') != 'Optimal':
            self.result_text.insert(tk.END, f"\n未找到最优解。状态: {result.get('status')}\n")
            return

        self.result_text.insert(tk.END, f"\n✅ 计算完成！总耗时：{calc_time:.2f} 秒\n")
        self.result_text.insert(tk.END, f"总计奖励分：{result['total']}\n")
        self.result_text.insert(tk.END, f"借用宠物总数：{result['borrowed']} | 使用宠物总数：{result['total_pets']}\n")
        self.result_text.insert(tk.END, "-"*50 + "\n")

        for i, assign in enumerate(result['assignments'], 1):
            task = assign['task']
            team = assign['team']
            score = assign['score']
            reward_level = get_reward_level(score, self.server)
            
            self.result_text.insert(tk.END, f"任务 {i}: {task['task']}\n")
            self.result_text.insert(tk.END, f"  加成特性: {', '.join(task['bonus_skills'])}\n")
            
            pet_names = [f"{p['name']}{' (借)' if p.get('is_borrowed', False) else ''}" for p in team]
            self.result_text.insert(tk.END, f"  派遣宠物: {', '.join(pet_names)}\n")
            self.result_text.insert(tk.END, f"  得分: {score} -> 奖励等级: {reward_level}\n\n")

def run_gui():
    root = tk.Tk()
    app = DispatchCalculatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
