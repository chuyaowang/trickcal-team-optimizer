# GEMINI.md - trickcal-team-optimizer

## Project Overview
**trickcal-team-optimizer** (Trickcal: Chibi Go - Farm Pet Dispatch Calculation) is a specialized tool for calculating optimal pet assignments for farm dispatch tasks. It leverages Mixed Integer Linear Programming (MILP) to find global optimal solutions across multiple tasks simultaneously, maximizing total reward tiers while respecting all game constraints.

### Core Logic
- **Algorithm:** Mixed Integer Linear Programming (MILP) implemented via the `PuLP` library.
- **Optimization Goal:** Maximize the total number of reward (carrots) (each tier S, A, B, etc. corresponds to a different carrot reward amount) across up to 5 concurrent tasks, with a tiny penalty per assigned pet to encourage minimal team sizes in case of ties.
- **Constraints:**
  - 1-3 pets per task.
  - Max 1 borrowed pet per task.
  - Max 3 borrowed pets total across all active tasks.
  - No duplicate pets (clones) allowed within the same team (even if one is owned and one is borrowed).
  - Respects server-specific reward labels (GL, KR).
- **Localization:** Full multi-language support (English/Chinese) for UI and results via `src/core/i18n.py`.
- **Server Support:** Servers `gl-cn`, `gl-en`, `kr` share one canonical `data/pets.csv` and one `data/missions/missions_YYMMDD.csv` per game update (language-neutral keys); only the display language differs. The CN server is retired (configs naming it load as `gl-cn`).

### Technologies
- **Language:** Python 3.10+
- **Solver:** `PuLP`
- **Web UI:** `streamlit`
- **Data Manipulation:** `pandas`
- **Architecture:** Modular structure (Data Loader, Core Logic, UI, Localization).

## Project Structure
- `src/core/`: 
    - `assignment.py`: MILP model and solver logic.
    - `scoring.py`: Pet-task score precomputation.
    - `constants.py`: Server-specific reward levels and game rules.
    - `i18n.py`: Internationalization strings and translation helper.
- `src/data_loader/`: Handles server-aware CSV ingestion.
- `src/ui/`: 
    - `web_gui.py`: Primary Streamlit interface with config save/load.
    - `cli.py` / `main.py`: Command Line interface with config support.
    - `gui.py`: Basic fallback Tkinter GUI.
- `data/`: `pets.csv`, `missions/missions_YYMMDD.csv`, translation tables in `i18n/` (`traits.csv`, `rarity.csv`, `locations.csv`), and `pet_images/`.

## Development Conventions
- **Data Integrity:** All CSV files **MUST** be saved with **UTF-8 with BOM** encoding for Excel compatibility.
- **Language Consistency:** Data files use language-neutral keys; display text comes from `data/i18n/`. Server languages: `gl-cn`→Traditional Chinese, `gl-en`→English, `kr`→Korean (not supported yet).
- **UI Decoupling:** The UI language (`en`/`cn`) is decoupled from the server data selection.
- **UI State Management (Streamlit):** To ensure stable widget behavior and prevent "reverting value" bugs, **ALWAYS** use the `key` parameter in Streamlit widgets (e.g., `st.number_input(..., key='p_limit')`) to link them directly to `st.session_state`. Avoid manual state assignments immediately after widget rendering.

## Building and Running
### Prerequisites
```bash
pip install pandas pulp streamlit
```

### Key Commands
- **Web GUI:** `streamlit run src/ui/web_gui.py`
- **CLI (Interactive):** `python main.py`
- **CLI (Config-based):** `python main.py --config config.json --lang en`

## Documentation
Refer to `docs/wiki/` for User, Installation, and Contribution guides in both English and Chinese. Keep the docs updated after feature changes are pushed to the main branch.
