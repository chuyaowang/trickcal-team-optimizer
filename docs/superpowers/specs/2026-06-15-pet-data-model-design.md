# Pet Data Model Redesign — Canonical Master + Translations

**Date:** 2026-06-15
**Status:** Approved (design)
**Goal:** Restructure pet data so each pet, its translations, traits, ranks, and
icon are linked through a single canonical record — enabling pet icons in the web
UI and a single source of truth across servers.

## Problem

Today each server has its own `data/<server>/pets.csv` keyed by a localized pet
name, with localized traits and ranks. The rosters differ (cn 33, gl-cn 36,
gl-en 36, kr 24) and row order is not aligned, so there is no way to link the
same pet across servers or to attach a language-independent icon.

Icons exist as `data/pet_images/{id}.png`, named by a numeric game id — the
natural canonical key — but nothing currently maps a pet to its id.

## Goals

- One canonical record per pet, keyed by the numeric image id.
- Language-neutral traits/ranks/rarity stored once; names translated per language.
- Pet icons resolvable from the canonical id.
- Minimal disruption to the jobs (task) pipeline and the contributor workflow.

## Non-Goals

- Changing the MILP algorithm or scoring formulas.
- Converting `jobs_*.csv` to trait keys (jobs stay localized; see Traits).
- Building the UI itself, including rendering icons next to names (this spec is
  the data layer that precedes the UI work).

## Decisions (from brainstorming)

- **Canonical master + translations** model (full normalization).
- **Approach 1** file layout: lean master CSV + separate translation tables,
  staying CSV / UTF-8 BOM / Excel-friendly.
- **Trait keys + translate jobs at load**: master and pets use language-neutral
  trait keys; jobs files stay localized and are reverse-mapped to keys at load.
- **Names stored in `pets.csv`** (not a separate file).
- **Availability = name presence**: server↔language is 1:1, so a pet is available
  on a server iff it has a non-empty name in that server's language. No `on_*`
  columns.
- **Missing data allowed**: blank name → pet absent on that server; missing icon
  or unassigned id → name shown without icon. Migration may be incremental.

## Data Model

All CSVs saved as **UTF-8 with BOM**.

### `data/pets.csv` (canonical master)

| column        | meaning                                                |
|---------------|--------------------------------------------------------|
| `id`          | stable pet id == icon filename stem (e.g. `148590`)    |
| `rarity_key`  | `NORMAL` \| `RARE` \| `UNIQUE` \| `LEGENDARY`          |
| `trait_1`     | trait key (e.g. `KIND`); may be blank                  |
| `rank_1`      | `C` \| `B` \| `A` \| `S`; blank if no `trait_1`        |
| `trait_2`     | trait key; may be blank                                |
| `rank_2`      | rank; blank if no `trait_2`                            |
| `name_en`     | English name; blank if unknown / not on that server    |
| `name_zh_hans`| Simplified Chinese name (cn)                           |
| `name_zh_hant`| Traditional Chinese name (gl-cn)                       |
| `name_ko`     | Korean name (kr)                                       |

Example:

```csv
id,rarity_key,trait_1,rank_1,trait_2,rank_2,name_en,name_zh_hans,name_zh_hant,name_ko
148590,NORMAL,KIND,C,DULL,C,Sato,莎兔,蘋果兔,
```

### `data/i18n/traits.csv`

`key, en, zh_hans, zh_hant, ko` — one row per trait. Keys are stable ASCII
tokens seeded from the English names.

```csv
key,en,zh_hans,zh_hant,ko
KIND,Kind,体贴,體貼,
DULL,Dull,迟钝,遲鈍,
```

### `data/i18n/rarity.csv`

`key, en, zh_hans, zh_hant, ko` — display names for the four rarity keys.
(Base scores live in `constants.py`, keyed by `rarity_key`.)

### Concrete vocabulary (seeded from current data)

These are the closed sets derived from the existing CN/EN files. The `ko` column
is blank until real Korean data arrives.

Traits (`traits.csv`):

| key       | en    | zh_hans | zh_hant |
|-----------|-------|---------|---------|
| `KIND`    | Kind  | 体贴    | 體貼    |
| `DULL`    | Dull  | 迟钝    | 遲鈍    |
| `BRISK`   | Brisk | 活泼    | 活潑    |
| `BOLD`    | Bold  | 自信    | 自信    |
| `KEEN`    | Keen  | 敏锐    | 敏銳    |
| `BOND`    | Bond  | 亲密    | 親密    |

Rarity (`rarity.csv`) — base score from `constants.py`:

| key         | en        | zh_hans  | base score |
|-------------|-----------|----------|------------|
| `NORMAL`    | Normal    | 普通宠物 | 2          |
| `RARE`      | Rare      | 高级宠物 | 2          |
| `UNIQUE`    | Unique    | 稀有宠物 | 3          |
| `LEGENDARY` | Legendary | 传说宠物 | 5          |

### Icons

`data/pet_images/{id}.png`, resolved by convention. No column. Missing file →
no icon.

## Server / Language Configuration (`constants.py`)

- `SERVER_LANG = {cn: zh_hans, gl-cn: zh_hant, gl-en: en, kr: ko}` (1:1).
- Replace `RARITY_BASE_MAP_CN` / `RARITY_BASE_MAP_EN` with a single
  `RARITY_BASE_SCORE` keyed by `rarity_key`.
- Reward tier thresholds (`SERVER_REWARD_LEVELS`) unchanged.

## Loader & Runtime Changes

### `load_pets(server)`

1. `lang = SERVER_LANG[server]`.
2. Read `pets.csv`; keep rows where `name_<lang>` is non-empty (availability).
3. For each pet build the existing dict shape, plus `id`:
   - `name` = `name_<lang>`
   - `rarity_score` = `RARITY_BASE_SCORE[rarity_key]`
   - `skill_score` keyed by **trait_key** → `SKILL_SCORE_MAP[rank]`
   - `id` = id; icon path = `pet_images/{id}.png` (or `None` if absent)

### `load_tasks(file_path, lang)`

- Jobs files stay localized. Reverse-map each localized task trait → trait key
  via `traits.csv` for `lang`. `bonus_skills` become trait keys.
- Unrecognized trait text is surfaced by the validator (see Validation).

### Scoring

- Matches trait **keys** on both sides (pet `skill_score` keys ↔ task
  `bonus_skills` keys). Logic unchanged; only the token space is now neutral.

### UI (only what this spec requires)

- Translate trait/rarity **keys → localized names** so the existing display keeps
  working after the loader switches to keys. Rendering the icon next to the pet
  name is the **follow-on UI task**, out of scope here (see Non-Goals).

## One-Time Migration

1. Hand-author `traits.csv` and `rarity.csv` once (small closed sets).
2. Migration script consolidates the four per-server `pets.csv` into one master:
   - Convert localized traits → keys via `traits.csv`.
   - Auto-link the same pet across languages by signature
     `(rarity_key, trait_1, rank_1, trait_2, rank_2)`; merge their localized
     names into one row's `name_*` columns.
   - Flag ambiguous signature collisions for manual resolution.
3. Manually assign each pet's image `id` (the inherently manual step). This may
   be done incrementally; pets without an id simply render without an icon.
4. Remove the old `data/<server>/pets.csv` files once the loader reads the master.

## Validation, Tests, Docs

- `scripts/validate_pet_data.py` (wired into CI):
  - every trait in every `jobs_*.csv` resolves to a key in `traits.csv`;
  - every `trait_*` / `rarity_key` used in `pets.csv` exists in the i18n tables;
  - warn (not fail) on pets whose `id` has no icon file;
  - warn on duplicate ids.
- Unit tests: `load_pets` server filtering + key→name resolution; jobs trait
  reverse-mapping; rarity/trait key lookups.
- Update the wiki Contribution Guide: contributors edit the master + translation
  tables; the validator catches mistakes.

## File Change Summary

- **New:** `data/pets.csv`, `data/i18n/traits.csv`, `data/i18n/rarity.csv`,
  `scripts/migrate_pet_data.py`, `scripts/validate_pet_data.py`.
- **Changed:** `src/data_loader/csv_loader.py`, `src/core/constants.py`,
  `src/core/scoring.py` (trait-key matching), `src/ui/web_gui.py` (translate
  keys → localized names to preserve current display), Contribution Guide.
- **Removed:** `data/cn/pets.csv`, `data/gl-cn/pets.csv`,
  `data/gl-en/pets.csv`, `data/kr/pets.csv`.

## Assumptions

- Server↔language is and will remain 1:1.
- The numeric image id is a stable, unique per-pet identifier.
- Trait and rarity vocabularies are small, closed sets.
- `kr` is currently placeholder test data written in Chinese, not Korean. During
  migration its `name_ko` is left blank (per "missing names allowed") rather than
  populated with the Chinese test strings; real Korean names land later.
