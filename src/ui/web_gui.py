import streamlit as st
import pandas as pd
import time
import os
import sys
import json
from typing import List, Dict

# Ensure the project root is in the python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data_loader.csv_loader import load_pets, load_tasks, get_available_job_files
from src.core.scoring import precompute_pet_task_scores, get_reward_level
from src.core.assignment import calculate_best_assignment

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="宠物派遣计算器",
    page_icon="🐾",
    layout="wide"
)

st.title("🐾 宠物派遣最优方案计算器 (MILP)")

# --- SESSION STATE INITIALIZATION ---
if 'server' not in st.session_state:
    st.session_state.server = 'cn'
if 'p_limit' not in st.session_state:
    st.session_state.p_limit = 5
if 'owned_pets_list' not in st.session_state:
    st.session_state.owned_pets_list = []
if 'aux_pets_dict' not in st.session_state:
    st.session_state.aux_pets_dict = {}

# --- SIDEBAR: CONFIG LOAD/SAVE ---
with st.sidebar:
    st.header("💾 配置管理")
    
    # 1. Read Config
    uploaded_file = st.file_uploader("读取配置文件 (.json)", type=["json"])
    if uploaded_file is not None:
        try:
            config = json.load(uploaded_file)
            st.session_state.server = config.get('server', 'cn')
            st.session_state.p_limit = config.get('max_job_number', 5)
            st.session_state.owned_pets_list = config.get('owned_pets', [])
            st.session_state.aux_pets_dict = config.get('aux_pets_counts', {})
            st.success("配置已从文件加载！")
        except Exception as e:
            st.error(f"读取失败: {e}")

    st.divider()
    
    # 2. Server Selection
    server_options = {"cn": "中国服 (CN)", "gl": "国际服 (GL)", "kr": "韩服 (KR)"}
    server_list = list(server_options.keys())
    server_idx = server_list.index(st.session_state.server)
    server_key = st.radio(
        "选择服务器", 
        options=server_list, 
        format_func=lambda x: server_options[x],
        index=server_idx
    )
    st.session_state.server = server_key
    
    # 3. Job File Selection
    job_files = get_available_job_files(server=server_key)
    if job_files:
        job_file_path = st.selectbox(
            "选择任务文件", 
            options=job_files, 
            format_func=lambda x: os.path.basename(x)
        )
    else:
        st.error(f"未找到 data/{server_key} 任务文件")
        st.stop()
        
    # 4. Max Jobs (P)
    p_limit = st.number_input(
        "最大并行任务数量 (P)", 
        min_value=2, 
        max_value=5, 
        value=st.session_state.p_limit,
        step=1
    )
    st.session_state.p_limit = p_limit

    st.divider()
    
    # 5. Save Config (Download)
    config_to_save = {
        "server": st.session_state.server,
        "max_job_number": st.session_state.p_limit,
        "owned_pets": st.session_state.owned_pets_list,
        "aux_pets_counts": st.session_state.aux_pets_dict
    }
    st.download_button(
        label="📥 下载当前配置",
        data=json.dumps(config_to_save, indent=4, ensure_ascii=False),
        file_name=f"dispatch_config_{server_key}.json",
        mime="application/json"
    )

# --- DATA LOADING ---
all_pets = load_pets(server=st.session_state.server)
tasks = load_tasks(job_file_path)

# --- MAIN AREA: PET SELECTION ---
col_owned, col_aux = st.columns(2)

with col_owned:
    st.subheader("📋 我拥有的宠物")
    owned_search = st.text_input("搜索拥有宠物...", key="owned_search")
    
    # Scrollable container using expander
    with st.expander("选择拥有的宠物 (勾选)", expanded=True):
        new_owned_selection = []
        
        # Filter pets based on search or current selection
        filtered_owned = [
            p for p in all_pets 
            if owned_search.lower() in p['name'].lower() or p['name'] in st.session_state.owned_pets_list
        ]
        
        # Display in a grid of 2 columns
        o_cols = st.columns(2)
        for i, pet in enumerate(filtered_owned):
            name = pet['name']
            is_selected = name in st.session_state.owned_pets_list
            with o_cols[i % 2]:
                if st.checkbox(f"{name}", value=is_selected, key=f"chk_{name}"):
                    new_owned_selection.append(name)
        
        st.session_state.owned_pets_list = sorted(list(set(new_owned_selection)))

with col_aux:
    st.subheader("🤝 借用宠物数量")
    aux_search = st.text_input("搜索借用宠物...", key="aux_search")
    
    with st.expander("设置可借用副本数", expanded=True):
        new_aux_dict = {}
        # Filter pets based on search or non-zero count
        filtered_pets = [
            p for p in all_pets 
            if aux_search.lower() in p['name'].lower() or st.session_state.aux_pets_dict.get(p['name'], 0) > 0
        ]
        
        # Display in a grid of 3 columns
        cols = st.columns(3)
        for i, pet in enumerate(filtered_pets):
            name = pet['name']
            current_count = st.session_state.aux_pets_dict.get(name, 0)
            
            # Distribute into columns
            with cols[i % 3]:
                count = st.number_input(
                    f"{name}", 
                    min_value=0, 
                    max_value=20, 
                    value=int(current_count), 
                    key=f"num_{name}",
                    label_visibility="visible"
                )
                if count > 0:
                    new_aux_dict[name] = count
        st.session_state.aux_pets_dict = new_aux_dict

# --- CALCULATION & RESULTS ---
st.divider()
run_calc = st.button("🚀 开始计算最优派遣方案", use_container_width=True, type="primary")

if run_calc:
    if not st.session_state.owned_pets_list:
        st.warning("请至少选择一个拥有的宠物。")
    else:
        st.header("📊 计算结果")
        owned_pet_objs = [p for p in all_pets if p['name'] in st.session_state.owned_pets_list]
        
        with st.spinner("正在运行 MILP 求解器..."):
            pet_task_scores = precompute_pet_task_scores(all_pets, tasks)
            start_time = time.time()
            result = calculate_best_assignment(
                my_pets=owned_pet_objs,
                aux_pets_counts=st.session_state.aux_pets_dict,
                tasks=tasks,
                pet_task_scores=pet_task_scores,
                max_active_jobs=st.session_state.p_limit
            )
            calc_time = time.time() - start_time
            
            if result.get('status') != 'Optimal':
                st.error(f"未找到最优解。状态: {result.get('status')}")
            else:
                st.balloons()
                m1, m2, m3 = st.columns(3)
                m1.metric("总计层级奖励分", result['total'])
                m2.metric("借用宠物总数", result['borrowed'])
                m3.metric("计算耗时 (秒)", f"{calc_time:.3f}")
                
                for i, assign in enumerate(result['assignments'], 1):
                    task = assign['task']
                    team = assign['team']
                    score = assign['score']
                    reward_level = get_reward_level(score, st.session_state.server)
                    
                    with st.expander(f"任务 {i}: {task['task']} ({reward_level})", expanded=True):
                        c1, c2 = st.columns([2, 1])
                        with c1:
                            st.markdown("**派遣队伍:**")
                            pet_list = [f"{p['name']} {' (借)' if p['is_borrowed'] else ''}" for p in team]
                            st.write(", ".join(pet_list))
                        with c2:
                            st.write(f"**原始得分:** {score}")
                            st.write(f"**加成特性:** {', '.join(task['bonus_skills'])}")
