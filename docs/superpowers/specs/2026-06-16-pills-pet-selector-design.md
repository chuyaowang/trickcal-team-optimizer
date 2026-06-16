# Pills-based Pet Selector — Design

Date: 2026-06-16
Status: Approved

## Goal

Replace the pet input UI in the Streamlit web app with a compact `st.pills`
selector. Owned and borrowed pets are chosen from a single box of pet pills
(each pill shows the pet icon + name); a mode toggle switches the box between
"Owned" (green) and "Borrow" (orange). Selected owned pets and borrowed pets are
summarized in two compact, icon-only boxes below, where clicking an icon removes
it (borrow: removes one copy).

The rest of the app — sidebar, task preview, run button, results, and the
config save/load **JSON format** — must behave exactly as before.

## Scope

In scope: the pet-selection block of `src/ui/web_gui.py` (currently the two
`st.columns` with checkboxes for owned pets and `number_input`s for borrowed
pets, ~lines 224–256), plus the three call sites that read pet state:
`on_config_upload`, `get_current_config`, and the `run_calc` block.

Out of scope: optimizer logic, scoring, i18n strings (reuse existing keys),
CLI/Tkinter UIs, data loading other than adding a thumbnail path.

## Layout

```
Mode:  ( [Owned] | Borrow )            <- st.segmented_control
[ search pets...                    ]  <- st.text_input (filters palette pills)
+-------------------------------------------------+
|  PALETTE (green in Owned / orange in Borrow)    |  <- st.pills, scoped CSS tint
|  (icon Sato) (icon Inky) (icon Azure Dragon)... |     icon + name, click to add
+-------------------------------------------------+

GREEN — Owned              ORANGE — Borrow            <- two columns, same row
+------------------+       +---------------------------+
| (S)(A)(I)(R)     |       | (P)(P)(P)(I)(D)           |  <- compact icon-only
+------------------+       +---------------------------+     click = remove (1 copy)
```

Boxes are compact wrapped grids of icons only (no names, no rows). Borrow copies
appear as repeated icons (3 copies = 3 identical icons). Hovering an icon shows
the pet name (image title attribute).

## State model

Single source of truth in session state; replaces the per-pet `chk_<name>`
(bool) and `num_<name>` (int) session keys.

- `st.session_state.owned_set: list[str]` — owned pet names (deduped, insertion
  order). NOT bound directly to a widget.
- `st.session_state.borrow_counts: dict[str, int]` — borrowed name → copies.
- `st.session_state.pet_mode: "owned" | "borrow"` — segmented control value
  (widget key `pet_mode`), default `"owned"`.

Initialized in the session-state init block alongside the existing keys.

### Stateless pills pattern

Every pills widget (palette + both boxes) is a **stateless click emitter**:
`selection_mode="single"`, and its `on_change` callback reads the clicked value,
mutates the master state above, then sets the widget's own session_state value
back to `None`. Resetting to `None` means clicking the same option again
re-registers as a change and re-fires (needed to stack borrow copies), and means
the widgets never carry a persistent selection that could drift from the master
state or raise on a default-not-in-options. Each widget calls `clear_results()`.

## Interaction

### Mode toggle
`st.segmented_control` labeled by `t('MY_PETS')` / `t('BORROW_PETS')`, default
Owned. Sets `pet_mode`; the palette is rendered once and tinted per mode.

### Search
`st.text_input` above the palette filters the palette's option list by substring
(case-insensitive) on the display name. The boxes are unaffected by the search.

### Palette (click to add)
`st.pills(options=filtered_names, selection_mode="single", key="palette",
format_func=icon_and_name, on_change=on_palette_click)`, tinted green in Owned
mode / orange in Borrow mode.
- `on_palette_click`: `clicked = st.session_state.palette`; if `clicked`:
  - Owned mode → add `clicked` to `owned_set` if absent.
  - Borrow mode → `borrow_counts[clicked] = min(borrow_counts.get(clicked,0)+1,
    MAX_COPIES)`.
  - reset `st.session_state.palette = None`; `clear_results()`.

`MAX_COPIES = 20` (matches the previous `number_input` max).

### Green box (Owned) — click to remove
`st.pills(options=owned_set, selection_mode="single", key="owned_box",
format_func=icon_only, on_change=on_owned_box_click)`.
- `on_owned_box_click`: remove the clicked name from `owned_set`; reset
  `owned_box = None`; `clear_results()`.

### Orange box (Borrow) — click to remove one copy
Options are expanded per copy: for each `name` with count `n`, emit values
`f"{name}\x00{i}"` for `i in range(n)`; `format_func` strips the `\x00<i>` suffix
to render the same icon for every copy.
`st.pills(options=expanded, selection_mode="single", key="borrow_box",
format_func=icon_only_copy, on_change=on_borrow_box_click)`.
- `on_borrow_box_click`: parse the name from the clicked value; decrement
  `borrow_counts[name]` and delete the key if it reaches 0; reset
  `borrow_box = None`; `clear_results()`.

### Pill labels (icons)
- Palette `format_func(name)`: Markdown with an inline image (the pet's 96px
  thumbnail as a `data:image/webp;base64,...` URI, with the name as the image
  title) followed by the display name.
- Box `format_func`: the inline image only (name in the image title for hover),
  no text — keeps the boxes compact.
- Pets without a thumbnail fall back to name-only.

`load_pets` (in `src/data_loader/csv_loader.py`) gains a `thumb` field:
`data/pet_images/thumbnails/<id>.png` when it exists, else `None`. The existing
`icon` (master) field is unchanged.

### Box tint
The palette is wrapped in `st.container(key="palette_box")`, which emits a
`.st-key-palette_box` CSS class. A small scoped `st.markdown(<style>)` block
tints that container (and its pills) green or orange based on `pet_mode`. The
green/orange summary boxes are likewise wrapped in keyed containers for their
border/background color.

## Config compatibility

The saved/loaded JSON schema is unchanged:
`{server, max_job_number, owned_pets: [...], aux_pets_counts: {...}, ui_language}`.

- `on_config_upload`: reset `owned_set = []` and `borrow_counts = {}`, then set
  `owned_set = list(config["owned_pets"])` and
  `borrow_counts = dict(config["aux_pets_counts"])` (drop the old `chk_`/`num_`
  reset loop).
- `get_current_config`: `owned_pets = st.session_state.owned_set`,
  `aux_pets_counts = {k: v for k, v in borrow_counts.items() if v > 0}`.
- `run_calc`: `owned_pet_names = owned_set`;
  `aux_pets_counts = {k: v for k, v in borrow_counts.items() if v > 0}`.

## Code structure

In `src/ui/web_gui.py`:
- `render_pet_selector(all_pets, data_lang)` — renders the toggle, search,
  palette, and the two summary boxes; reads/writes the state model above.
- Callbacks: `on_palette_click`, `on_owned_box_click`, `on_borrow_box_click`.

Pure, testable helpers (module-level functions, no Streamlit calls):
- `pet_icon_uri(thumb_path: str | None) -> str | None` — base64 data URI for a
  thumbnail, cached; `None` when the path is missing.
- `expand_borrow(borrow_counts) -> list[str]` — copy-expanded option values
  (`name\x00i`); and `copy_value_name(value) -> str` to parse a name back out.
- `state_to_config(owned, borrow_counts, server, p_limit, lang) -> dict`.
- `config_to_state(config) -> tuple[list, dict]` — returns
  `(owned_set, borrow_counts)` from a config dict.

`get_current_config` and `on_config_upload` are thin wrappers over the two pure
config functions so the mapping logic is unit-tested independent of Streamlit.

## Testing

- `tests/test_web_config.py`: round-trip and edge cases for `state_to_config` /
  `config_to_state` (empty selections, borrow counts, dropping zero counts,
  missing keys defaulting safely); `expand_borrow` / `copy_value_name`
  (counts → N values, parse round-trip, names containing odd characters); and
  `pet_icon_uri` (returns `None` for a missing path; returns a
  `data:image/webp;base64,` string for a real thumbnail).
- Streamlit interactions (palette add, box remove, mode toggle, tint, copy
  stacking, config upload) are verified by running the app manually.

## Edge cases

- Palette options are the search-filtered names; boxes show full state
  regardless of the search.
- Borrow copies capped at `MAX_COPIES = 20`; further clicks are no-ops.
- Stateless widgets reset to `None` each click, so duplicate/absent options
  never raise.
- Any state change calls `clear_results()` to invalidate a stale result.
- A pet with no thumbnail renders as name-only (no broken image).