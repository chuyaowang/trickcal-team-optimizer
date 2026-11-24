# Central Missions Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace per-server `data/<server>/jobs_*.csv` with one key-based missions file per game update plus a location translation table, and retire the CN server.

**Architecture:** `data/i18n/locations.csv` maps a location key to its region and its localized location/task text. `data/missions/missions_YYMMDD.csv` lists `location,trait_1,trait_2` keys. A new loader turns a missions file into the existing task dict shape (`{'task': "<location> - <task>", 'bonus_skills': [trait keys]}`), so scoring and the solver are untouched.

**Tech Stack:** Python 3.10+, pandas, pytest, Streamlit (AppTest in tests).

**Spec:** `docs/superpowers/specs/2026-11-24-central-missions-design.md`

## Global Constraints

- All CSV files are UTF-8 with BOM (`encoding="utf-8-sig"` when writing); `scripts/enforce_bom.py` runs in pre-commit.
- Languages in `locations.csv`: `en`, `zh_hant`, `ko` only. Blank cell = no translation → fall back to `en`.
- Keys are UPPER_SNAKE; loaders `.strip()` cells; unknown location or trait keys raise `ValueError`.
- Remaining servers: `gl-cn` (zh_hant), `gl-en` (en), `kr` (ko, "not supported yet"). UI language `cn` (Simplified Chinese UI) is unrelated and stays.
- Commits: conventional commits, one logical change each, no `Co-authored-by` line (user rule).

## Review Focus

- A saved config with `"server": "cn"` → loads as `gl-cn` in both the web uploader and `main.py --config` (tests in Task 4).
- `trait_2` blank → `bonus_skills` has one key, never `""` or `nan` (test in Task 2).
- `kr` server (all `ko` cells blank) → task text falls back to English, no crash (test in Task 2).
- Cells with stray whitespace (` KEEN `) → still resolve (test in Task 2).
- Switching server in the web UI keeps the selected missions file (the selectbox key is no longer per-server) (test in Task 3).

---

### Task 1: Spec, plan, and migrated data

**Files:**
- Create: `data/i18n/locations.csv`, `data/missions/missions_<YYMMDD>.csv` × 18 (same dates as `data/gl-en/jobs_*.csv`)
- Commit also: the spec and this plan
- One-off migration script lives in the scratchpad, **not** the repo.

Location keys and regions (region = rotation order, starting at the Kyarot region):

| Region | Keys |
|---|---|
| 1 | KYAROT_GREENHOUSE, CHLOE_TAILOR_SHOP, FOUNTAIN, ASHUR_BAKERY, SHOUPAN_MAILROOM |
| 2 | DIANA_HOUSE, KOMMY_HOUSE, BUTTER_HOUSE, TIG_HOUSE, MAGO_HOUSE |
| 3 | FRICLE_FLOWER_BED, UFC, WITCH_KINGDOM_LIBRARY, VELVET_TRAINING_GROUND, POSHER_SHOP |
| 4 | VENUE, LAB, CITY_HALL_SQUARE, HOSPITAL, ARCADE |
| 5 | GARDEN, MELUN_STAGE, LAKE, POND, STONE_PILLAR |
| 6 | RIM_HOUSE, PHOTO_STUDIO, TAROT_SHOP, DOLL_HOUSE, PUMPKIN_FARM |

- [ ] **Step 1:** Commit the spec and plan: `docs: add central missions design and plan`.
- [ ] **Step 2:** Write the scratchpad script: pair rows of `gl-en/jobs_D.csv` and `gl-cn/jobs_D.csv` by position (same row order per date), key each row by its English location, take `location_*`/`task_*` text from the **latest** file for each key, convert traits to keys via `vocab_loader.trait_key_from_localized(text, "en")`, and assert the gl-cn traits give the same keys.
- [ ] **Step 3:** Write `locations.csv` columns `key,region,location_en,task_en,location_zh_hant,task_zh_hant,location_ko,task_ko` (ko blank) and the 18 missions files with header `location,trait_1,trait_2`, row order kept.
- [ ] **Step 4:** Verify the conversion both ways: for each date, rebuild `"<loc> - <task>"` + localized traits from the new files and compare to the old gl-en and gl-cn files. Expected: identical. Report any name that differs across dates (an old translation that was later fixed); the latest wording wins.
- [ ] **Step 5:** `python scripts/enforce_bom.py` → no missing BOM.
- [ ] **Step 6:** Commit: `feat(data): add location translations and central mission files`.

### Task 2: Location table + missions loader + validator

**Files:**
- Modify: `src/data_loader/vocab_loader.py`, `src/data_loader/csv_loader.py`, `scripts/validate_pet_data.py`
- Test: `tests/test_load_missions.py` (replaces `tests/test_load_tasks.py`), `tests/test_validate_pet_data.py`

**Interfaces:**
- Produces (`vocab_loader`): `location_regions() -> Dict[str, int]`; `location_text(key: str, lang: str) -> Tuple[str, str]` returning `(location, task)` with `en` fallback per cell; raises `KeyError` for an unknown key. Cached; reads `_I18N_DIR/locations.csv` (tests monkeypatch `_I18N_DIR` as today).
- Produces (`csv_loader`): `get_available_mission_files(data_dir: str = './data') -> List[str]` (sorted `data_dir/missions/missions_*.csv`); `load_missions(file_path: str, lang: str) -> List[Dict]` → `[{'task': f"{location} - {task}", 'bonus_skills': [keys]}]`. Raises `ValueError` naming the file and the bad key. `load_tasks` and `get_available_job_files` are removed in Task 3, once nothing calls them.
- Produces (validator): `find_mission_file_errors(path: str, regions: Dict[str, int], trait_keys: Set[str]) -> List[str]`.

- [ ] **Step 1: Write failing tests** in `tests/test_load_missions.py`, using tmp `traits.csv` (KIND, KEEN) and `locations.csv` with `LAKE` (region 5, en "Lake"/"Playing in Water", zh_hant "湖"/"玩水", ko blank):
  - `test_load_missions_translates_location_and_traits`: row `LAKE,KEEN,KIND`, lang `zh_hant` → `[{'task': '湖 - 玩水', 'bonus_skills': ['KEEN', 'KIND']}]`
  - `test_blank_trait_2_is_omitted`: row `LAKE,KEEN,` → `bonus_skills == ['KEEN']`
  - `test_missing_translation_falls_back_to_english`: lang `ko` → `task == 'Lake - Playing in Water'`
  - `test_whitespace_is_stripped`: row ` LAKE , KEEN ,` → resolves
  - `test_unknown_location_raises` / `test_unknown_trait_raises`: `pytest.raises(ValueError, match="NOPE")`
  - `test_get_available_mission_files_sorted`: two files in `tmp/missions` → sorted paths
  - in `tests/test_validate_pet_data.py`: `find_mission_file_errors` returns `[]` for a good file, and one error each for an unknown location, an unknown trait, a duplicated location, and locations from two regions.
- [ ] **Step 2:** `pytest tests/test_load_missions.py tests/test_validate_pet_data.py -v` → new tests FAIL (missing functions).
- [ ] **Step 3:** Implement the interfaces above. In `validate_pet_data.main`, add the missions check over `data/missions/*.csv`; leave the old jobs check in place until Task 3.
- [ ] **Step 4:** `pytest tests/ -v` → all PASS; `python -m scripts.validate_pet_data` → OK.
- [ ] **Step 5:** Commit: `feat(loader): load missions from central key-based files`.

### Task 3: Switch the UIs to central missions; delete per-server jobs

**Files:**
- Modify: `src/ui/web_gui.py` (imports, `get_cached_tasks`, job selectbox ~221-233, `data_lang` usage), `main.py` (both paths), `src/ui/gui.py` (`load_server_data`), `src/core/i18n.py` (`TASK_FILE_NOT_FOUND` → mention `data/missions`, no `{}` placeholder), `src/data_loader/csv_loader.py` (remove `load_tasks`, `get_available_job_files`), `scripts/validate_pet_data.py` (remove jobs check)
- Delete: `data/cn/`, `data/gl-cn/`, `data/gl-en/`, `data/kr/`, `tests/test_load_tasks.py`
- Test: `tests/test_web_selector.py`

**Interfaces:**
- Consumes: `get_available_mission_files()`, `load_missions(path, SERVER_LANG[server])` from Task 2.

- [ ] **Step 1: Write failing test** `test_mission_file_selection_survives_server_switch` in `tests/test_web_selector.py`: run AppTest, pick the first (oldest) option of the selectbox with key `mission_file`, switch the `server` radio to `gl-en`, assert the selectbox value is unchanged.
- [ ] **Step 2:** Run it → FAIL (no `mission_file` key).
- [ ] **Step 3:** Implement: the selectbox uses `key="mission_file"` and shows the date part of the basename; every caller loads via `load_missions`. Delete the old folders and functions.
- [ ] **Step 4:** `pytest tests/ -v` → PASS; `python -m scripts.validate_pet_data` → OK; `grep -rn "jobs_\|load_tasks\|get_available_job_files" src main.py scripts tests` → no hits.
- [ ] **Step 5:** Smoke test: `python main.py --config <scratch gl-en config> --lang en` prints results for the latest missions file.
- [ ] **Step 6:** Commit: `refactor(data): read missions from central files and drop per-server jobs`.

### Task 4: Remove the CN server

**Files:**
- Modify: `src/core/constants.py` (`SERVER_LANG`, `SERVER_REWARD_LEVELS`), `src/core/i18n.py` (`SERVER_NAMES` in both languages), `src/core/scoring.py:25-27` (default/fallback `'gl-cn'`), `src/data_loader/csv_loader.py` (`load_pets` default `'gl-cn'`), `src/ui/gui.py:23,37-38` (default + server list), `src/ui/cli.py:45` (default), `src/ui/web_gui.py` (`on_config_upload`), `main.py:29`, `web_gui.py` `RANK_COLORS` (drop 特阶… labels)
- Create: `normalize_server(server: Optional[str]) -> str` in `src/core/constants.py`: returns the argument if in `SERVER_LANG`, else `'gl-cn'`.
- Test: `tests/test_constants.py`, `tests/test_scoring.py`, `tests/test_i18n.py`, `tests/test_pet_selector.py`, `tests/test_web_selector.py`

- [ ] **Step 1: Write/adjust failing tests:**
  - `test_constants.py`: `SERVER_LANG == {"gl-cn": "zh_hant", "gl-en": "en", "kr": "ko"}`; `normalize_server("cn") == "gl-cn"`, `normalize_server(None) == "gl-cn"`, `normalize_server("gl-en") == "gl-en"`.
  - `test_scoring.py`: drop the CN label asserts; add `get_reward_level(37, 'cn') == 'S'` (unknown server falls back to gl-cn labels).
  - `test_i18n.py`: `'cn' not in t('SERVER_NAMES', 'en')` and `'cn' not in t('SERVER_NAMES', 'cn')`.
  - `test_pet_selector.py`: use `"gl-cn"` instead of `"cn"`.
  - `test_web_selector.py`: the server-switch test switches to `gl-en`; new `test_cn_config_upload_loads_as_gl_cn` sets the uploader to a JSON with `"server": "cn"` → `session_state["server"] == "gl-cn"`.
- [ ] **Step 2:** `pytest tests/ -v` → new asserts FAIL.
- [ ] **Step 3:** Implement: remove the `cn` entries; route `config.get('server')` through `normalize_server` in `web_gui.on_config_upload` and `main.run_config`.
- [ ] **Step 4:** `pytest tests/ -v` → PASS; `grep -rn "'cn'" src main.py` shows only UI-language uses.
- [ ] **Step 5:** Commit: `refactor(server): remove CN server`.

### Task 5: Docs

**Files:**
- Modify: `docs/wiki/Contribution-Guide.md`, `docs/wiki/Contribution-Guide-CN.md` (section 2 rewritten: add one `data/missions/missions_YYMMDD.csv` with keys; add new locations to `data/i18n/locations.csv`), `docs/wiki/User-Guide*.md` / `Software-Architecture.md` / `README.md` / `CLAUDE.md` wherever they mention CN server or per-server jobs folders.

- [ ] **Step 1:** `grep -rln "jobs_\|data/cn\|China Server\|中国服\|特阶" docs/wiki README.md CLAUDE.md` and update each hit.
- [ ] **Step 2:** Re-run the grep → only intentional mentions remain.
- [ ] **Step 3:** Commit: `docs: document central missions data and CN server removal`.
