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
from src.core.i18n import t

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="🐾 ddl-PetDispatch",
    layout="wide"
)

# --- SESSION STATE INITIALIZATION ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'cn'
if 'server' not in st.session_state:
    st.session_state.server = 'cn'
if 'p_limit' not in st.session_state:
    st.session_state.p_limit = 5

# --- HELPER: GET CURRENT CONFIG ---
def get_current_config():
    """Extracts the current state directly from widget keys to ensure it's up-to-date."""
    owned = [k.replace("chk_", "") for k, v in st.session_state.items() if k.startswith("chk_") and v]
    aux = {k.replace("num_", ""): v for k, v in st.session_state.items() if k.startswith("num_") and v > 0}
    return {
        "server": st.session_state.server,
        "max_job_number": st.session_state.p_limit,
        "owned_pets": owned,
        "aux_pets_counts": aux,
        "ui_language": st.session_state.lang
    }

# --- SIDEBAR: CONFIG & LANGUAGE ---
with st.sidebar:
    st.header(t('LANGUAGE', st.session_state.lang))
    lang_options = {"cn": "简体中文", "en": "English"}
    st.session_state.lang = st.radio(
        "Select Language", 
        options=list(lang_options.keys()), 
        format_func=lambda x: lang_options[x],
        index=0 if st.session_state.lang == 'cn' else 1,
        horizontal=True
    )
    st.divider()
    st.header(t('CONFIG_MGMT', st.session_state.lang))
    
    # Brief explanation
    if st.session_state.lang == 'cn':
        st.info("💡 可跳过：上传之前保存的 .json 配置文件（按键在底部），可快速恢复您的宠物勾选和数量设置。")
    else:
        st.info("💡 Optional: Upload a previously saved (button below) .json config to instantly restore your pets and counts.")

    # 1. Read Config
    uploaded_file = st.file_uploader(t('LOAD_CONFIG', st.session_state.lang), type=["json"])
    if uploaded_file is not None:
        try:
            config = json.load(uploaded_file)
            st.session_state.server = config.get('server', 'cn')
            st.session_state.p_limit = config.get('max_job_number', 5)
            st.session_state.lang = config.get('ui_language', st.session_state.lang)
            
            # Pre-populate widget keys so they are ready when rendered
            for pet_name in config.get('owned_pets', []):
                st.session_state[f"chk_{pet_name}"] = True
            for pet_name, count in config.get('aux_pets_counts', {}).items():
                st.session_state[f"num_{pet_name}"] = count
                
            st.success(t('LOAD_SUCCESS', st.session_state.lang))
        except Exception as e:
            st.error(t('LOAD_FAIL', st.session_state.lang).format(e))

    st.divider()
    
    # 2. Server Selection
    st.header(t('SERVER_SETTINGS', st.session_state.lang))
    server_names = t('SERVER_NAMES', st.session_state.lang)
    server_list = list(server_names.keys())
    
    if st.session_state.server not in server_list: 
        st.session_state.server = 'cn'
    
    server_idx = server_list.index(st.session_state.server)
    server_key = st.radio(
        t('SELECT_SERVER', st.session_state.lang), 
        options=server_list, 
        format_func=lambda x: server_names[x],
        index=server_idx
    )
    st.session_state.server = server_key
    
    # 3. Job File Selection
    job_files = get_available_job_files(server=server_key)
    if job_files:
        job_file_path = st.selectbox(
            t('SELECT_JOB_FILE', st.session_state.lang), 
            options=job_files, 
            format_func=lambda x: os.path.basename(x)
        )
    else:
        st.error(t('TASK_FILE_NOT_FOUND', st.session_state.lang).format(server_key))
        st.stop()
        
    # 4. Max Jobs (P)
    p_limit = st.number_input(
        t('MAX_JOBS', st.session_state.lang), 
        min_value=2, 
        max_value=5, 
        value=st.session_state.p_limit,
        step=1
    )
    st.session_state.p_limit = p_limit

    st.divider()
    
    # 5. Save Config (Download)
    # Note: This is now reactive to the current session state keys
    current_cfg = get_current_config()
    st.download_button(
        label=t('SAVE_CONFIG', st.session_state.lang),
        data=json.dumps(current_cfg, indent=4, ensure_ascii=False),
        file_name=f"dispatch_config_{server_key}.json",
        mime="application/json"
    )
    
    st.divider()
    
    # GitHub Link
    github_url = "https://github.com/chuyaowang/ddl-PetDispatch/tree/modularize-and-refactor"
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

# --- DATA LOADING ---
all_pets = load_pets(server=st.session_state.server)
tasks = load_tasks(job_file_path)

# --- RANK COLORS ---
RANK_COLORS = {
    "特阶": "#FFD700", "一阶": "#FFEC8B", "二阶": "#C0C0C0", 
    "三阶": "#CD7F32", "四阶": "#A0522D", "无奖励": "#F0F2F6",
    "S": "#FFD700", "A": "#FFEC8B", "B": "#C0C0C0", 
    "C": "#CD7F32", "D": "#A0522D", "N/A": "#F0F2F6"
}

# --- MAIN AREA: PET SELECTION ---
col_owned, col_aux = st.columns(2)

with col_owned:
    st.subheader(t('MY_PETS', st.session_state.lang))
    owned_search = st.text_input(t('SEARCH_PETS', st.session_state.lang), key="owned_search")
    
    with st.expander(t('EXPAND_PET_LIST', st.session_state.lang), expanded=True):
        new_owned_selection = []
        # Filter pets based on search or current selection in session state
        filtered_owned = [
            p for p in all_pets 
            if owned_search.lower() in p['name'].lower() or st.session_state.get(f"chk_{p['name']}", False)
        ]
        
        o_cols = st.columns(2)
        for i, pet in enumerate(filtered_owned):
            name = pet['name']
            with o_cols[i % 2]:
                if st.checkbox(f"{name}", key=f"chk_{name}"):
                    new_owned_selection.append(name)

with col_aux:
    st.subheader(t('BORROW_PETS', st.session_state.lang))
    aux_search = st.text_input(t('SEARCH_PETS', st.session_state.lang) + " ", key="aux_search")
    
    with st.expander(t('SET_BORROW_COPIES', st.session_state.lang), expanded=True):
        # Filter pets based on search or non-zero count in session state
        filtered_aux = [
            p for p in all_pets 
            if aux_search.lower() in p['name'].lower() or st.session_state.get(f"num_{p['name']}", 0) > 0
        ]
        
        cols = st.columns(3)
        for i, pet in enumerate(filtered_aux):
            name = pet['name']
            with cols[i % 3]:
                st.number_input(
                    f"{name}", 
                    min_value=0, 
                    max_value=20, 
                    step=1, 
                    key=f"num_{name}"
                )

# --- CALCULATION & RESULTS ---
st.divider()
run_calc = st.button(t('RUN_OPTIMIZER', st.session_state.lang), use_container_width=True, type="primary")

if run_calc:
    # Final check of selections
    owned_pet_names = [k.replace("chk_", "") for k, v in st.session_state.items() if k.startswith("chk_") and v]
    aux_pets_counts = {k.replace("num_", ""): v for k, v in st.session_state.items() if k.startswith("num_") and v > 0}
    
    if not owned_pet_names:
        st.warning(t('SELECT_OWNED_WARNING', st.session_state.lang))
    else:
        st.header(t('RESULTS', st.session_state.lang))
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
            
            if result.get('status') != 'Optimal':
                st.error(t('NO_OPTIMAL', st.session_state.lang).format(result.get('status')))
            else:
                st.balloons()
                m1, m2, m3 = st.columns(3)
                m1.metric(t('TOTAL_REWARD', st.session_state.lang), result['total'])
                m2.metric(t('TOTAL_BORROWED', st.session_state.lang), result['borrowed'])
                m3.metric(t('CALC_TIME', st.session_state.lang), f"{calc_time:.3f}")
                
                for i, assign in enumerate(result['assignments'], 1):
                    task = assign['task']
                    team = assign['team']
                    score = assign['score']
                    reward_level = get_reward_level(score, st.session_state.server)
                    
                    bg_color = RANK_COLORS.get(reward_level, "#F0F2F6")
                    borrow_tag = " (借)" if st.session_state.lang == 'cn' else " (Borrow)"
                    pet_list_str = ", ".join([f"{p['name']}{borrow_tag if p['is_borrowed'] else ''}" for p in team])
                    
                    st.markdown(f"""
                        <div style="background-color: {bg_color}; padding: 8px 12px; border-radius: 8px; border: 1px solid #ddd; color: black; margin-bottom: 10px;">
                            <div style="font-size: 1.0em; font-weight: bold; color: #333;">{t('STATUS', st.session_state.lang)} {i}: {task['task']}</div>
                            <div style="font-size: 1.1em; font-weight: bold; margin: 4px 0;">{reward_level} ({score} pts)</div>
                            <hr style="margin: 6px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
                            <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 0.95em;">
                                <div><strong>{t('DISPATCH_TEAM', st.session_state.lang)}:</strong> {pet_list_str}</div>
                                <div><strong>{t('BONUS_TRAITS', st.session_state.lang)}:</strong> {', '.join(task['bonus_skills'])}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
else:
    st.info(t('INFO_TEXT', st.session_state.lang))
