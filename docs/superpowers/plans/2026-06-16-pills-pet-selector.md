# Pills-based Pet Selector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the checkbox/number-input pet picker in the Streamlit web app with a compact `st.pills` selector: a mode toggle recolors one palette green (owned) / orange (borrow); compact icon-only boxes below show selections and remove on click.

**Architecture:** Pure, Streamlit-free logic lives in a new `src/ui/pet_selector.py` (unit-tested). `web_gui.py` imports it for rendering and for thin `on_change` callbacks. Every pills widget is a stateless click-emitter: its callback mutates a single source-of-truth state (`owned_set` list, `borrow_counts` dict), then resets the widget to `None` so repeat clicks re-fire. Confirmed working via Streamlit `AppTest`.

**Tech Stack:** Python 3.8+, Streamlit 1.55 (`st.pills`, `st.segmented_control`, `st.container(key=...)`), pytest, `streamlit.testing.v1.AppTest`.

**Environment:** Run tests with the `speaki` conda env: `/opt/miniconda3/envs/speaki/bin/python`. It has streamlit, pulp, pandas, pytest. (microsam lacks pulp/streamlit.)

---

### Task 1: Add `thumb` (thumbnail path) to loaded pets

**Files:**
- Modify: `src/data_loader/csv_loader.py` (the `load_pets` per-row dict, ~lines 42-53)
- Test: `tests/test_load_pets.py`

- [ ] **Step 1: Add a failing test for the `thumb` field**

Append to `tests/test_load_pets.py`:

```python
def test_load_pets_sets_thumb_when_present(tmp_path, monkeypatch):
    data_dir = _write_master(tmp_path)
    monkeypatch.setattr(vocab_loader, "_I18N_DIR", os.path.join(data_dir, "i18n"))
    vocab_loader._load_table.cache_clear()
    vocab_loader._reverse_table.cache_clear()

    # No thumbnail file yet -> thumb is None
    pets = csv_loader.load_pets(server="gl-en", data_dir=data_dir)
    assert pets[0]["thumb"] is None

    # Create the thumbnail -> thumb resolves to it
    thumb_dir = os.path.join(data_dir, "pet_images", "thumbnails")
    os.makedirs(thumb_dir, exist_ok=True)
    thumb_path = os.path.join(thumb_dir, "148590.png")
    with open(thumb_path, "wb") as f:
        f.write(b"RIFF0000WEBP")  # any bytes; load_pets only checks existence
    pets = csv_loader.load_pets(server="gl-en", data_dir=data_dir)
    assert pets[0]["thumb"] == thumb_path
```

- [ ] **Step 2: Run the test, verify it fails**

Run: `/opt/miniconda3/envs/speaki/bin/python -m pytest tests/test_load_pets.py::test_load_pets_sets_thumb_when_present -v`
Expected: FAIL with `KeyError: 'thumb'`.

- [ ] **Step 3: Add the `thumb` field in `load_pets`**

In `src/data_loader/csv_loader.py`, inside the row loop where `icon` is computed, add the thumbnail path and include it in the appended dict:

```python
        rarity_key = row["rarity_key"].strip()
        pet_id = row["id"].strip()
        icon = os.path.join(data_dir, "pet_images", f"{pet_id}.png")
        thumb = os.path.join(data_dir, "pet_images", "thumbnails", f"{pet_id}.png")
        pets.append({
            'name': name,
            'id': pet_id or None,
            'icon': icon if pet_id and os.path.exists(icon) else None,
            'thumb': thumb if pet_id and os.path.exists(thumb) else None,
            'rarity_key': rarity_key,
            'rarity': vocab_loader.rarity_name(rarity_key, lang),
            'rarity_score': RARITY_BASE_SCORE.get(rarity_key, 2),
            'skill_score': skill_score,
            'is_borrowed': False,
        })
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `/opt/miniconda3/envs/speaki/bin/python -m pytest tests/test_load_pets.py -v`
Expected: PASS (both old and new tests).

- [ ] **Step 5: Commit**

```bash
git add src/data_loader/csv_loader.py tests/test_load_pets.py
git commit -m "feat(data): expose thumbnail path on loaded pets"
```

---

### Task 2: Pure selector logic module

**Files:**
- Create: `src/ui/pet_selector.py`
- Test: `tests/test_pet_selector.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_pet_selector.py`:

```python
import os
from src.ui import pet_selector as ps


def test_add_owned_dedupes_and_preserves_order():
    assert ps.add_owned([], "Inky") == ["Inky"]
    assert ps.add_owned(["Inky"], "Sato") == ["Inky", "Sato"]
    assert ps.add_owned(["Inky"], "Inky") == ["Inky"]  # no duplicate


def test_remove_owned():
    assert ps.remove_owned(["Inky", "Sato"], "Inky") == ["Sato"]
    assert ps.remove_owned(["Sato"], "Inky") == ["Sato"]  # absent -> unchanged


def test_inc_borrow_caps_at_max():
    assert ps.inc_borrow({}, "Inky") == {"Inky": 1}
    assert ps.inc_borrow({"Inky": 1}, "Inky") == {"Inky": 2}
    assert ps.inc_borrow({"Inky": 20}, "Inky", max_copies=20) == {"Inky": 20}


def test_dec_borrow_removes_at_zero():
    assert ps.dec_borrow({"Inky": 2}, "Inky") == {"Inky": 1}
    assert ps.dec_borrow({"Inky": 1}, "Inky") == {}
    assert ps.dec_borrow({}, "Inky") == {}


def test_expand_borrow_and_parse_roundtrip():
    counts = {"Inky": 3, "Sato": 1}
    values = ps.expand_borrow(counts)
    assert len(values) == 4
    assert sum(1 for v in values if ps.copy_value_name(v) == "Inky") == 3
    # names with odd characters survive the round-trip
    assert ps.copy_value_name(ps.expand_borrow({"A B#1": 1})[0]) == "A B#1"


def test_state_config_roundtrip_drops_zero_counts():
    cfg = ps.state_to_config(["Inky"], {"Sato": 2, "Z": 0}, "cn", 5, "en")
    assert cfg["owned_pets"] == ["Inky"]
    assert cfg["aux_pets_counts"] == {"Sato": 2}
    assert cfg["server"] == "cn" and cfg["max_job_number"] == 5 and cfg["ui_language"] == "en"
    owned, counts = ps.config_to_state(cfg)
    assert owned == ["Inky"] and counts == {"Sato": 2}


def test_config_to_state_defaults_when_keys_missing():
    assert ps.config_to_state({}) == ([], {})


def test_pet_icon_uri(tmp_path):
    assert ps.pet_icon_uri(None) is None
    assert ps.pet_icon_uri(str(tmp_path / "missing.png")) is None
    p = tmp_path / "t.png"
    p.write_bytes(b"RIFF0000WEBP")
    uri = ps.pet_icon_uri(str(p))
    assert uri.startswith("data:image/webp;base64,")
```

- [ ] **Step 2: Run the tests, verify they fail**

Run: `/opt/miniconda3/envs/speaki/bin/python -m pytest tests/test_pet_selector.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.ui.pet_selector'`.

- [ ] **Step 3: Implement the module**

Create `src/ui/pet_selector.py`:

```python
"""Pure (Streamlit-free) logic for the web pet selector.

Kept separate from web_gui.py so it can be unit-tested without importing
Streamlit (which runs page setup at import time). web_gui.py imports these
helpers for rendering and for its on_change callbacks.
"""
import base64
import os
from typing import Dict, List, Optional, Tuple

MAX_COPIES = 20
_COPY_SEP = "\x00"


def pet_icon_uri(thumb_path: Optional[str]) -> Optional[str]:
    """Base64 ``data:`` URI for a thumbnail, or None if missing/unset."""
    if not thumb_path or not os.path.exists(thumb_path):
        return None
    with open(thumb_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/webp;base64,{data}"


def add_owned(owned: List[str], name: str) -> List[str]:
    """Owned list with ``name`` appended if absent (deduped, order kept)."""
    return list(owned) if name in owned else list(owned) + [name]


def remove_owned(owned: List[str], name: str) -> List[str]:
    return [n for n in owned if n != name]


def inc_borrow(counts: Dict[str, int], name: str,
               max_copies: int = MAX_COPIES) -> Dict[str, int]:
    out = dict(counts)
    out[name] = min(out.get(name, 0) + 1, max_copies)
    return out


def dec_borrow(counts: Dict[str, int], name: str) -> Dict[str, int]:
    out = dict(counts)
    if name in out:
        if out[name] <= 1:
            del out[name]
        else:
            out[name] -= 1
    return out


def expand_borrow(counts: Dict[str, int]) -> List[str]:
    """One option value per copy: ``"<name>\\x00<i>"`` for each copy i."""
    values: List[str] = []
    for name, n in counts.items():
        values.extend(f"{name}{_COPY_SEP}{i}" for i in range(n))
    return values


def copy_value_name(value: str) -> str:
    """Parse the pet name back out of an expanded copy value."""
    return value.split(_COPY_SEP, 1)[0]


def state_to_config(owned: List[str], borrow_counts: Dict[str, int],
                    server: str, max_job_number: int, lang: str) -> dict:
    return {
        "server": server,
        "max_job_number": max_job_number,
        "owned_pets": list(owned),
        "aux_pets_counts": {k: v for k, v in borrow_counts.items() if v > 0},
        "ui_language": lang,
    }


def config_to_state(config: dict) -> Tuple[List[str], Dict[str, int]]:
    owned = list(config.get("owned_pets", []))
    counts = {k: int(v) for k, v in config.get("aux_pets_counts", {}).items()
              if int(v) > 0}
    return owned, counts
```

- [ ] **Step 4: Run the tests, verify they pass**

Run: `/opt/miniconda3/envs/speaki/bin/python -m pytest tests/test_pet_selector.py -v`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add src/ui/pet_selector.py tests/test_pet_selector.py
git commit -m "feat(ui): add pure pet-selector logic (state, copies, config mapping)"
```

---

### Task 3: Wire the new state model and config into web_gui.py

**Files:**
- Modify: `src/ui/web_gui.py` (imports; session init ~lines 41-51; `on_config_upload` ~58-84; `get_current_config` ~87-96; `run_calc` reads ~262-263)

This task changes the state plumbing only; the old checkbox/number UI (lines ~224-256) is replaced in Tasks 4-5. After this task the app still runs (selector temporarily empty is fine — it's replaced next).

- [ ] **Step 1: Add the import**

In `src/ui/web_gui.py`, after `from src.data_loader.vocab_loader import trait_name` add:

```python
from src.ui import pet_selector
```

- [ ] **Step 2: Add session-state keys**

In the session-state init block (after `st.session_state.p_limit = 5`), add:

```python
if 'owned_set' not in st.session_state:
    st.session_state.owned_set = []
if 'borrow_counts' not in st.session_state:
    st.session_state.borrow_counts = {}
if 'pet_mode' not in st.session_state:
    st.session_state.pet_mode = 'owned'
```

- [ ] **Step 3: Replace `on_config_upload` body**

Replace the whole `on_config_upload` function with:

```python
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
```

- [ ] **Step 4: Replace `get_current_config`**

Replace the whole `get_current_config` function with:

```python
def get_current_config():
    return pet_selector.state_to_config(
        st.session_state.owned_set,
        st.session_state.borrow_counts,
        st.session_state.server,
        st.session_state.p_limit,
        st.session_state.lang,
    )
```

- [ ] **Step 5: Update the `run_calc` reads**

In the `if run_calc:` block, replace the first two lines:

```python
    owned_pet_names = [k.replace("chk_", "") for k, v in st.session_state.items() if k.startswith("chk_") and v]
    aux_pets_counts = {k.replace("num_", ""): v for k, v in st.session_state.items() if k.startswith("num_") and v > 0}
```

with:

```python
    owned_pet_names = list(st.session_state.owned_set)
    aux_pets_counts = {k: v for k, v in st.session_state.borrow_counts.items() if v > 0}
```

- [ ] **Step 6: Verify the app still imports and runs**

Run:

```bash
/opt/miniconda3/envs/speaki/bin/python -c "from streamlit.testing.v1 import AppTest; at = AppTest.from_file('src/ui/web_gui.py'); at.run(timeout=30); print('run ok, no exception:', not at.exception)"
```

Expected: `run ok, no exception: True`.

- [ ] **Step 7: Commit**

```bash
git add src/ui/web_gui.py
git commit -m "refactor(ui): drive pet state from owned_set/borrow_counts + pure config mapping"
```

---

### Task 4: Render the palette (toggle + search + add-on-click pills)

**Files:**
- Modify: `src/ui/web_gui.py` (the pet-selection block, currently `col_owned, col_aux = st.columns(2)` through the borrow `number_input` loop, ~lines 224-256)

- [ ] **Step 1: Add the palette callback and helpers near the other callbacks**

In `src/ui/web_gui.py`, after the `clear_results` function, add:

```python
def _pet_label(pet, with_name):
    """Markdown label for a pill: thumbnail image (+ optional name)."""
    uri = pet_selector.pet_icon_uri(pet.get('thumb'))
    title = pet['name'].replace('"', '')
    img = f'![]({uri} "{title}")' if uri else ''
    if with_name:
        return f"{img} {pet['name']}".strip()
    return img if img else pet['name']

def on_palette_click():
    clicked = st.session_state.palette
    if clicked:
        if st.session_state.pet_mode == 'owned':
            st.session_state.owned_set = pet_selector.add_owned(st.session_state.owned_set, clicked)
        else:
            st.session_state.borrow_counts = pet_selector.inc_borrow(st.session_state.borrow_counts, clicked)
    st.session_state.palette = None
    clear_results()
```

- [ ] **Step 2: Replace the old two-column selection block with the palette**

Replace everything from `col_owned, col_aux = st.columns(2)` through the end of the `with col_aux:` block (the borrow `number_input` loop) with:

```python
# Pet selector: mode toggle + search + palette pills (boxes added in Task 5)
pets_by_name = {p['name']: p for p in all_pets}

st.segmented_control(
    t('MY_PETS', st.session_state.lang) + " / " + t('BORROW_PETS', st.session_state.lang),
    options=['owned', 'borrow'],
    format_func=lambda m: t('MY_PETS', st.session_state.lang) if m == 'owned'
        else t('BORROW_PETS', st.session_state.lang),
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
        format_func=lambda n: _pet_label(pets_by_name[n], with_name=True),
        key="palette",
        on_change=on_palette_click,
        label_visibility="collapsed",
    )
```

- [ ] **Step 3: Verify palette add works via AppTest**

Run:

```bash
/opt/miniconda3/envs/speaki/bin/python - <<'PY'
from streamlit.testing.v1 import AppTest
at = AppTest.from_file('src/ui/web_gui.py').run(timeout=30)
assert not at.exception, at.exception
# palette is the button_group with key 'palette'
pal = [b for b in at.button_group if b.key == 'palette'][0]
first = pal.options[0]
pal.set_value(first).run(timeout=30)
print("owned_set after one palette click:", at.session_state['owned_set'])
assert at.session_state['owned_set'] == [first]
print("OK")
PY
```

Expected: prints the clicked pet name in `owned_set` and `OK`.

- [ ] **Step 4: Commit**

```bash
git add src/ui/web_gui.py
git commit -m "feat(ui): add pills palette with mode toggle, search, and click-to-add"
```

---

### Task 5: Compact icon-only summary boxes (click to remove)

**Files:**
- Modify: `src/ui/web_gui.py` (add the box callbacks near `on_palette_click`; render the two boxes right after the palette `st.container` block from Task 4)

- [ ] **Step 1: Add the box callbacks**

After `on_palette_click`, add:

```python
def on_owned_box_click():
    clicked = st.session_state.owned_box
    if clicked:
        st.session_state.owned_set = pet_selector.remove_owned(st.session_state.owned_set, clicked)
    st.session_state.owned_box = None
    clear_results()

def on_borrow_box_click():
    clicked = st.session_state.borrow_box
    if clicked:
        name = pet_selector.copy_value_name(clicked)
        st.session_state.borrow_counts = pet_selector.dec_borrow(st.session_state.borrow_counts, name)
    st.session_state.borrow_box = None
    clear_results()
```

- [ ] **Step 2: Render the two boxes after the palette block**

Immediately after the `with st.container(key="palette_box"):` block, add:

```python
# Compact icon-only summary boxes (green = owned, orange = borrow)
st.markdown(
    "<style>"
    ".st-key-owned_box [data-baseweb='tag']{background-color:#2e7d3233;border-color:#2e7d32;}"
    ".st-key-borrow_box [data-baseweb='tag']{background-color:#ef6c0033;border-color:#ef6c00;}"
    "</style>",
    unsafe_allow_html=True,
)
box_owned, box_borrow = st.columns(2)

with box_owned:
    st.caption(t('MY_PETS', st.session_state.lang))
    with st.container(key="owned_box"):
        st.pills(
            "owned_box",
            options=list(st.session_state.owned_set),
            selection_mode="single",
            format_func=lambda n: _pet_label(pets_by_name[n], with_name=False),
            key="owned_box",
            on_change=on_owned_box_click,
            label_visibility="collapsed",
        )

with box_borrow:
    st.caption(t('BORROW_PETS', st.session_state.lang))
    borrow_values = pet_selector.expand_borrow(st.session_state.borrow_counts)
    with st.container(key="borrow_box"):
        st.pills(
            "borrow_box",
            options=borrow_values,
            selection_mode="single",
            format_func=lambda v: _pet_label(pets_by_name[pet_selector.copy_value_name(v)], with_name=False),
            key="borrow_box",
            on_change=on_borrow_box_click,
            label_visibility="collapsed",
        )
```

- [ ] **Step 3: Verify remove + borrow stacking via AppTest**

Run:

```bash
/opt/miniconda3/envs/speaki/bin/python - <<'PY'
from streamlit.testing.v1 import AppTest
at = AppTest.from_file('src/ui/web_gui.py').run(timeout=30)
assert not at.exception, at.exception

def bg(key): return [b for b in at.button_group if b.key == key][0]

# Owned: add then remove
pal = bg('palette'); name = pal.options[0]
pal.set_value(name).run(timeout=30)
assert at.session_state['owned_set'] == [name]
bg('owned_box').set_value(name).run(timeout=30)
assert at.session_state['owned_set'] == [], at.session_state['owned_set']

# Switch to borrow mode, click same pet 3x -> 3 copies, remove one -> 2
mode = [s for s in at.segmented_control if s.key == 'pet_mode'][0]
mode.set_value('borrow').run(timeout=30)
for _ in range(3):
    bg('palette').set_value(name).run(timeout=30)
assert at.session_state['borrow_counts'] == {name: 3}, at.session_state['borrow_counts']
bb = bg('borrow_box')
bb.set_value(bb.options[0]).run(timeout=30)
assert at.session_state['borrow_counts'] == {name: 2}, at.session_state['borrow_counts']
print("OK")
PY
```

Expected: prints `OK` (owned add/remove and borrow stack/decrement all assert true).

- [ ] **Step 4: Run the full test suite**

Run: `/opt/miniconda3/envs/speaki/bin/python -m pytest -q`
Expected: all tests pass (existing 19 + new load_pets + 8 pet_selector).

- [ ] **Step 5: Commit**

```bash
git add src/ui/web_gui.py
git commit -m "feat(ui): add compact icon-only owned/borrow boxes with click-to-remove"
```

---

### Task 6: Manual verification and visual check

**Files:** none (verification only)

- [ ] **Step 1: Launch the app**

Run: `/opt/miniconda3/envs/speaki/bin/python -m streamlit run src/ui/web_gui.py`
Open the local URL.

- [ ] **Step 2: Exercise the flows and confirm each**

- Owned mode: palette box is green; clicking a pill shows its icon in the green box; clicking the icon in the green box removes it.
- Borrow mode: palette box is orange; clicking a pill 3× shows three identical icons in the orange box; clicking an icon removes one copy.
- Pills show the pet icon + name (palette) / icon only (boxes); hovering a box icon shows the name.
- Search filters the palette; selections in the boxes are unaffected.
- Save config → reload the page → upload it: owned + borrow selections restore. Run optimizer: results match the selections.

- [ ] **Step 3: Confirm icons render**

If any pill shows a broken image instead of the pet icon, the base64 data-URI Markdown image is not rendering — check `_pet_label` output and that `pet['thumb']` resolves (Task 1). Pets with no thumbnail are expected to show name-only.

---

## Self-Review Notes

- **Spec coverage:** toggle (T4), search (T4), palette add/copy (T4), green/orange compact boxes + remove/decrement (T5), copies as repeated icons via `expand_borrow` (T2/T5), icons via base64 (T1/T2/T4/T5), CSS tint (T4/T5), config JSON unchanged (T2/T3), thumb field (T1), tests (T1/T2 + AppTest smoke in T4/T5). All covered.
- **Naming consistency:** widget keys `pet_mode`, `palette`, `owned_box`, `borrow_box`, `pet_search`; state keys `owned_set`, `borrow_counts`; helpers `add_owned/remove_owned/inc_borrow/dec_borrow/expand_borrow/copy_value_name/pet_icon_uri/state_to_config/config_to_state` — used identically across tasks.
- **Risk:** the `[data-baseweb='tag']` / `pillsActive` CSS selectors are best-effort cosmetic tinting and may need adjustment against the running DOM (Task 6 visual check); they do not affect behavior or tests.