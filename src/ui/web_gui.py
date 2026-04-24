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
from src.core.scoring import precompute_pet_task_scores, get_reward_level, get_carrot_reward, format_reward_range
from src.core.assignment import calculate_best_assignment
from src.core.i18n import t

# --- CACHED DATA LOADING ---
@st.cache_data
def get_cached_pets(server):
    return load_pets(server=server)

@st.cache_data
def get_cached_tasks(file_path):
    return load_tasks(file_path)

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Trickcal Pet Dispatcher",
    page_icon="assets/icon.png",
    layout="wide"
)

# --- SESSION STATE INITIALIZATION ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'cn'
if 'server' not in st.session_state:
    st.session_state.server = 'cn'
if 'p_limit' not in st.session_state:
    st.session_state.p_limit = 5
if 'msg_success' not in st.session_state:
    st.session_state.msg_success = False
if 'msg_error' not in st.session_state:
    st.session_state.msg_error = None

def clear_results():
    """Clears the cached calculation result when any input parameter changes."""
    st.session_state.calc_result = None

# --- CONFIG UPLOAD CALLBACK (The Streamlit-Native Fix for Reversal Bug) ---
def on_config_upload():
    """Processes config file only when a new file is uploaded."""
    uploaded_file = st.session_state.config_uploader
    if uploaded_file is not None:
        try:
            config = json.load(uploaded_file)
            
            # Reset existing pet selections to prevent "merging" configs
            for key in list(st.session_state.keys()):
                if key.startswith("chk_"):
                    st.session_state[key] = False
                elif key.startswith("num_"):
                    st.session_state[key] = 0

            # Safe to update these because the widgets haven't rendered yet in this run
            st.session_state.server = config.get('server', st.session_state.server)
            st.session_state.p_limit = config.get('max_job_number', st.session_state.p_limit)
            st.session_state.lang = config.get('ui_language', st.session_state.lang)
            
            for pet_name in config.get('owned_pets', []):
                st.session_state[f"chk_{pet_name}"] = True
            for pet_name, count in config.get('aux_pets_counts', {}).items():
                st.session_state[f"num_{pet_name}"] = count
            st.session_state.msg_success = True
            clear_results()
        except Exception as e:
            st.session_state.msg_error = str(e)

# --- HELPER: GET CURRENT CONFIG ---
def get_current_config():
    owned = [k.replace("chk_", "") for k, v in st.session_state.items() if k.startswith("chk_") and v]
    aux = {k.replace("num_", ""): v for k, v in st.session_state.items() if k.startswith("num_") and v > 0}
    return {
        "server": st.session_state.server,
        "max_job_number": st.session_state.p_limit,
        "owned_pets": owned,
        "aux_pets_counts": aux,
        "ui_language": st.session_state.lang
    }

# --- SIDEBAR START ---
with st.sidebar:
    st.header(t('LANGUAGE', st.session_state.lang))
    st.radio(
        t('LANGUAGE', st.session_state.lang), 
        label_visibility="collapsed",
        options=["cn", "en"], 
        format_func=lambda x: "简体中文" if x == "cn" else "English",
        key='lang',
        horizontal=True
    )
    st.divider()
    
    # 1. Server Selection
    st.header(t('SERVER_SETTINGS', st.session_state.lang))
    server_names = t('SERVER_NAMES', st.session_state.lang)
    server_list = list(server_names.keys())
    
    st.radio(
        t('SELECT_SERVER', st.session_state.lang), 
        options=server_list, 
        format_func=lambda x: server_names[x],
        key='server',
        on_change=clear_results
    )
    
    # 2. Job File Selection
    job_files = get_available_job_files(server=st.session_state.server)
    if job_files:
        job_file_path = st.selectbox(
            t('SELECT_JOB_FILE', st.session_state.lang), 
            options=job_files, 
            format_func=lambda x: os.path.basename(x),
            index=len(job_files) - 1,
            key=f"job_select_{st.session_state.server}",
            on_change=clear_results
        )
    else:
        st.error(t('TASK_FILE_NOT_FOUND', st.session_state.lang).format(st.session_state.server))
        st.stop()
        
    # 3. Max Jobs (P)
    st.number_input(
        t('MAX_JOBS', st.session_state.lang), 
        min_value=2, 
        max_value=5, 
        step=1,
        key='p_limit',
        on_change=clear_results
    )
    
    st.divider()
    
    # 4. Configuration Management
    st.header(t('CONFIG_MGMT', st.session_state.lang))
    if st.session_state.lang == 'cn':
        st.info("💡 可跳过：上传之前保存的 .json 配置文件（按键在底部），可快速恢复设置。")
    else:
        st.info("💡 Optional: Upload a previously saved (button below) .json config to instantly restore settings.")

    # Load Config (Using callback to fix reversal bug)
    st.file_uploader(
        t('LOAD_CONFIG', st.session_state.lang), 
        type=["json"], 
        key='config_uploader', 
        on_change=on_config_upload
    )
    
    if st.session_state.msg_success:
        st.success(t('LOAD_SUCCESS', st.session_state.lang))
        st.session_state.msg_success = False
    if st.session_state.msg_error:
        st.error(t('LOAD_FAIL', st.session_state.lang).format(st.session_state.msg_error))
        st.session_state.msg_error = None

    # Save Config
    current_cfg = get_current_config()
    st.download_button(
        label=t('SAVE_CONFIG', st.session_state.lang),
        data=json.dumps(current_cfg, indent=4, ensure_ascii=False),
        file_name=f"dispatch_config_{st.session_state.server}.json",
        mime="application/json"
    )
    
    st.divider()
    
    github_url = "https://github.com/chuyaowang/trickcal-team-optimizer"
    st.markdown(f"""
        <div style="margin-top: -10px; margin-bottom: 20px;">
            <a href="{github_url}" target="_blank" style="text-decoration: none; color: inherit;">
                <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" width="20" style="vertical-align: middle; margin-right: 5px;">
                <span style="vertical-align: middle; font-size: 14px;">{t('VIEW_ON_GITHUB', st.session_state.lang)}</span>
            </a>
        </div>
    """, unsafe_allow_html=True)

# --- MAIN AREA ---
st.title(t('APP_TITLE', st.session_state.lang))

all_pets = get_cached_pets(st.session_state.server)
tasks = get_cached_tasks(job_file_path)

# Task Preview
with st.expander(t('TASK_PREVIEW', st.session_state.lang), expanded=True):
    preview_tasks = [t_obj for t_obj in tasks if t_obj['task']]
    if preview_tasks:
        preview_df = pd.DataFrame([
            {
                t('TASK_NAME', st.session_state.lang): task['task'],
                t('BONUS_TRAITS', st.session_state.lang): ", ".join(task['bonus_skills'])
            }
            for task in preview_tasks
        ])
        st.table(preview_df)
    else:
        st.write("No active tasks found in this file.")

# Rank Colors
RANK_COLORS = {
    "特阶": "#FFD700", "一阶": "#FFEC8B", "二阶": "#C0C0C0", 
    "三阶": "#CD7F32", "四阶": "#A0522D", "无奖励": "#F0F2F6",
    "S": "#FFD700", "A": "#FFEC8B", "B": "#C0C0C0", 
    "C": "#CD7F32", "D": "#A0522D", "N/A": "#F0F2F6"
}

col_owned, col_aux = st.columns(2)

with col_owned:
    st.subheader(t('MY_PETS', st.session_state.lang))
    owned_search = st.text_input(t('SEARCH_PETS', st.session_state.lang), key="owned_search")
    
    with st.expander(t('EXPAND_PET_LIST', st.session_state.lang), expanded=True):
        filtered_owned = [
            p for p in all_pets 
            if owned_search.lower() in p['name'].lower() or st.session_state.get(f"chk_{p['name']}", False)
        ]
        
        o_cols = st.columns(2)
        for i, pet in enumerate(filtered_owned):
            name = pet['name']
            with o_cols[i % 2]:
                st.checkbox(f"{name}", key=f"chk_{name}", on_change=clear_results)

with col_aux:
    st.subheader(t('BORROW_PETS', st.session_state.lang))
    aux_search = st.text_input(t('SEARCH_PETS', st.session_state.lang) + " ", key="aux_search")
    
    with st.expander(t('SET_BORROW_COPIES', st.session_state.lang), expanded=True):
        filtered_aux = [
            p for p in all_pets 
            if aux_search.lower() in p['name'].lower() or st.session_state.get(f"num_{p['name']}", 0) > 0
        ]
        
        cols = st.columns(3)
        for i, pet in enumerate(filtered_aux):
            name = pet['name']
            with cols[i % 3]:
                st.number_input(f"{name}", min_value=0, max_value=20, step=1, key=f"num_{name}", on_change=clear_results)

st.divider()
run_calc = st.button(t('RUN_OPTIMIZER', st.session_state.lang), use_container_width=True, type="primary")

if run_calc:
    owned_pet_names = [k.replace("chk_", "") for k, v in st.session_state.items() if k.startswith("chk_") and v]
    aux_pets_counts = {k.replace("num_", ""): v for k, v in st.session_state.items() if k.startswith("num_") and v > 0}
    
    if not owned_pet_names:
        st.warning(t('SELECT_OWNED_WARNING', st.session_state.lang))
        st.session_state.calc_result = None
    else:
        owned_pet_objs = [p for p in all_pets if p['name'] in owned_pet_names]
        
        with st.spinner(t('STATUS', st.session_state.lang) + "..."):
            pet_task_scores = precompute_pet_task_scores(all_pets, tasks)
            start_time = time.time()
            result = calculate_best_assignment(
                my_pets=owned_pet_objs,
                aux_pets_counts=aux_pets_counts,
                tasks=tasks,
                pet_task_scores=pet_task_scores,
                max_active_jobs=st.session_state.p_limit
            )
            calc_time = time.time() - start_time
            st.session_state.calc_result = result
            st.session_state.calc_time = calc_time
            
            if result.get('status') == 'Optimal':
                st.balloons()

if st.session_state.get('calc_result'):
    result = st.session_state.calc_result
    calc_time = st.session_state.calc_time
    
    st.header(t('RESULTS', st.session_state.lang))
    if result.get('status') != 'Optimal':
        st.error(t('NO_OPTIMAL', st.session_state.lang).format(result.get('status')))
    else:
        m1, m2, m3 = st.columns(3)
        
        total_display = format_reward_range(result['min_total'], result['max_total'])
        
        m1.metric(t('TOTAL_REWARD', st.session_state.lang), f"{total_display}🥕")
        m2.metric(t('TOTAL_BORROWED', st.session_state.lang), result['borrowed'])
        m3.metric(t('CALC_TIME', st.session_state.lang), f"{calc_time:.3f}s")
        
        for i, assign in enumerate(result['assignments'], 1):
            task = assign['task']
            team = assign['team']
            score = assign['score']
            reward_level = get_reward_level(score, st.session_state.server)
            carrot_reward = get_carrot_reward(score)
            
            bg_color = RANK_COLORS.get(reward_level, "#F0F2F6")
            borrow_tag = " (借)" if st.session_state.lang == 'cn' else " (Borrow)"
            pet_list_str = ", ".join([f"{p['name']}{borrow_tag if p['is_borrowed'] else ''}" for p in team])
            
            st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 8px 12px; border-radius: 8px; border: 1px solid #ddd; color: black; margin-bottom: 10px;">
                    <div style="font-size: 1.0em; font-weight: bold; color: #333;">{t('STATUS', st.session_state.lang)} {i}: {task['task']}</div>
                    <div style="font-size: 1.1em; font-weight: bold; margin: 4px 0;">{reward_level} ({score} pts) -> {carrot_reward} 🥕</div>
                    <hr style="margin: 6px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
                    <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 0.95em;">
                        <div><strong>{t('DISPATCH_TEAM', st.session_state.lang)}:</strong> {pet_list_str}</div>
                        <div><strong>{t('BONUS_TRAITS', st.session_state.lang)}:</strong> {', '.join(task['bonus_skills'])}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
elif not run_calc:
    st.info(t('INFO_TEXT', st.session_state.lang))
