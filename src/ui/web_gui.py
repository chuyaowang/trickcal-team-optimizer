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
from src.core.analytics import track_visit
from src.core.constants import SERVER_LANG
from src.data_loader.vocab_loader import trait_name
from src.ui import pet_selector

# --- CACHED DATA LOADING ---
@st.cache_data
def get_cached_pets(server):
    return load_pets(server=server)

@st.cache_data
def get_cached_tasks(file_path, lang):
    return load_tasks(file_path, lang=lang)

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Trickcal Pet Dispatcher",
    page_icon="assets/icon.png",
    layout="wide"
)

# --- ANALYTICS (best-effort, once per session) ---
track_visit()

# --- SESSION STATE INITIALIZATION ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'cn'
if 'server' not in st.session_state:
    st.session_state.server = 'cn'
if 'p_limit' not in st.session_state:
    st.session_state.p_limit = 5
if 'owned_set' not in st.session_state:
    st.session_state.owned_set = []
if 'borrow_counts' not in st.session_state:
    st.session_state.borrow_counts = {}
if 'pet_mode' not in st.session_state:
    st.session_state.pet_mode = 'owned'
if 'msg_success' not in st.session_state:
    st.session_state.msg_success = False
if 'msg_error' not in st.session_state:
    st.session_state.msg_error = None

def clear_results():
    """Clears the cached calculation result when any input parameter changes."""
    st.session_state.calc_result = None

def on_palette_click():
    clicked = st.session_state.palette
    if clicked:
        if st.session_state.pet_mode == 'owned':
            st.session_state.owned_set = pet_selector.add_owned(st.session_state.owned_set, clicked)
        else:
            st.session_state.borrow_counts = pet_selector.inc_borrow(st.session_state.borrow_counts, clicked)
        clear_results()
    st.session_state.palette = None

def on_owned_box_click():
    clicked = st.session_state.owned_box
    if clicked:
        st.session_state.owned_set = pet_selector.remove_owned(st.session_state.owned_set, clicked)
        clear_results()
    st.session_state.owned_box = None

def on_borrow_box_click():
    clicked = st.session_state.borrow_box
    if clicked:
        name = pet_selector.copy_value_name(clicked)
        st.session_state.borrow_counts = pet_selector.dec_borrow(st.session_state.borrow_counts, name)
        clear_results()
    st.session_state.borrow_box = None

def on_server_change():
    """Pet selections are server-language-specific, so reset them on switch."""
    st.session_state.owned_set = []
    st.session_state.borrow_counts = {}
    clear_results()

# --- CONFIG UPLOAD CALLBACK (The Streamlit-Native Fix for Reversal Bug) ---
def on_config_upload():
    """Processes config file only when a new file is uploaded."""
    uploaded_file = st.session_state.config_uploader
    if uploaded_file is not None:
        try:
            config = json.load(uploaded_file)
            owned, counts = pet_selector.config_to_state(config)
            st.session_state.owned_set = owned
            st.session_state.borrow_counts = counts
            st.session_state.server = config.get('server', st.session_state.server)
            st.session_state.p_limit = config.get('max_job_number', st.session_state.p_limit)
            st.session_state.lang = config.get('ui_language', st.session_state.lang)
            st.session_state.msg_success = True
            clear_results()
        except Exception as e:
            st.session_state.msg_error = str(e)

# --- HELPER: GET CURRENT CONFIG ---
def get_current_config():
    return pet_selector.state_to_config(
        st.session_state.owned_set,
        st.session_state.borrow_counts,
        st.session_state.server,
        st.session_state.p_limit,
        st.session_state.lang,
    )

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
        on_change=on_server_change
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
data_lang = SERVER_LANG[st.session_state.server]
tasks = get_cached_tasks(job_file_path, data_lang)

# Task Preview
with st.expander(t('TASK_PREVIEW', st.session_state.lang), expanded=True):
    preview_tasks = [t_obj for t_obj in tasks if t_obj['task']]
    if preview_tasks:
        preview_df = pd.DataFrame([
            {
                t('TASK_NAME', st.session_state.lang): task['task'],
                t('BONUS_TRAITS', st.session_state.lang): ", ".join(trait_name(k, data_lang) for k in task['bonus_skills'])
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

# Pet selector: mode toggle + search + palette pills (boxes added in Task 5)
pets_by_name = {p['name']: p for p in all_pets}

_mode_lang = st.session_state.lang  # snapshot so the label string and format_func agree this render (and to avoid st.session_state access inside format_func, which trips AppTest widget serialization)
st.segmented_control(
    t('MY_PETS', _mode_lang) + " / " + t('BORROW_PETS', _mode_lang),
    options=['owned', 'borrow'],
    format_func=lambda m, _l=_mode_lang: t('MY_PETS', _l) if m == 'owned'
        else t('BORROW_PETS', _l),
    key='pet_mode',
    on_change=clear_results,
    label_visibility='collapsed',
)

mode = st.session_state.pet_mode
tint = "#2e7d32" if mode == 'owned' else "#ef6c00"   # green / orange
st.markdown(
    f"<style>.st-key-palette_box [data-baseweb='tag'],"
    f".st-key-palette_box button[kind='pillsActive']"
    f"{{background-color:{tint}33;border-color:{tint};}}</style>",
    unsafe_allow_html=True,
)

search = st.text_input(t('SEARCH_PETS', st.session_state.lang), key="pet_search")
filtered = [p['name'] for p in all_pets if search.lower() in p['name'].lower()]

with st.container(key="palette_box"):
    st.pills(
        "palette",
        options=filtered,
        selection_mode="single",
        format_func=lambda n: pet_selector.pet_label(pets_by_name[n], with_name=True),
        key="palette",
        on_change=on_palette_click,
        label_visibility="collapsed",
    )

# Compact icon-only summary boxes (green = owned, orange = borrow)
st.markdown(
    "<style>"
    ".st-key-owned_box_wrap [data-baseweb='tag']{background-color:#2e7d3233;border-color:#2e7d32;}"
    ".st-key-borrow_box_wrap [data-baseweb='tag']{background-color:#ef6c0033;border-color:#ef6c00;}"
    "</style>",
    unsafe_allow_html=True,
)
box_owned, box_borrow = st.columns(2)

with box_owned:
    st.caption(t('MY_PETS', st.session_state.lang))
    with st.container(key="owned_box_wrap"):
        st.pills(
            "owned_box_pills",
            # defensive: only render names the current server actually has
            options=[n for n in st.session_state.owned_set if n in pets_by_name],
            selection_mode="single",
            format_func=lambda n: pet_selector.pet_label(pets_by_name[n], with_name=False),
            key="owned_box",
            on_change=on_owned_box_click,
            label_visibility="collapsed",
        )

with box_borrow:
    st.caption(t('BORROW_PETS', st.session_state.lang))
    # defensive: only expand copies for pets the current server actually has
    _valid_borrow = {k: v for k, v in st.session_state.borrow_counts.items() if k in pets_by_name}
    borrow_values = pet_selector.expand_borrow(_valid_borrow)
    with st.container(key="borrow_box_wrap"):
        st.pills(
            "borrow_box_pills",
            options=borrow_values,
            selection_mode="single",
            format_func=lambda v: pet_selector.pet_label(pets_by_name[pet_selector.copy_value_name(v)], with_name=False),
            key="borrow_box",
            on_change=on_borrow_box_click,
            label_visibility="collapsed",
        )

st.divider()
run_calc = st.button(t('RUN_OPTIMIZER', st.session_state.lang), use_container_width=True, type="primary")

if run_calc:
    owned_pet_names = list(st.session_state.owned_set)
    aux_pets_counts = {k: v for k, v in st.session_state.borrow_counts.items() if v > 0}
    
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
            bonus_str = ", ".join(trait_name(k, data_lang) for k in task['bonus_skills'])

            st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 8px 12px; border-radius: 8px; border: 1px solid #ddd; color: black; margin-bottom: 10px;">
                    <div style="font-size: 1.0em; font-weight: bold; color: #333;">{t('STATUS', st.session_state.lang)} {i}: {task['task']}</div>
                    <div style="font-size: 1.1em; font-weight: bold; margin: 4px 0;">{reward_level} ({score} pts) -> {carrot_reward} 🥕</div>
                    <hr style="margin: 6px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
                    <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 0.95em;">
                        <div><strong>{t('DISPATCH_TEAM', st.session_state.lang)}:</strong> {pet_list_str}</div>
                        <div><strong>{t('BONUS_TRAITS', st.session_state.lang)}:</strong> {bonus_str}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
elif not run_calc:
    st.info(t('INFO_TEXT', st.session_state.lang))
