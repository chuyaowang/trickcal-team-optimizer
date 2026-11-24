# Contribution Guide

Help keep the **trickcal-team-optimizer** data up to date! This guide explains how to update pet and task information for different game servers.

## Data Structure
Pets and missions are shared by all servers; only the display language differs.
- `data/pets.csv`: the canonical master — one row per pet, shared across servers.
- `data/missions/missions_YYMMDD.csv`: the missions of one game update, shared
  across servers, written with language-neutral keys.
- `data/i18n/traits.csv`, `data/i18n/rarity.csv`, `data/i18n/locations.csv`:
  translation tables mapping language-neutral keys to localized names.
- `data/pet_images/<id>.png`: pet icons, named by the pet's `id`.

Each server maps to one language: `gl-cn`→Traditional Chinese, `gl-en`→English,
`kr`→Korean (not supported yet). A pet is considered available on a server when
it has a non-empty name in that server's language column.

## 1. Updating Pets (`data/pets.csv`)
Add or edit one row per pet in the canonical master.

**Columns:**
- `id`: the pet's numeric id; must match its icon `data/pet_images/<id>.png`.
  May be left blank (the pet then shows without an icon).
- `rarity_key`: one of `NORMAL`, `RARE`, `UNIQUE`, `LEGENDARY`.
- `trait_1`, `rank_1`, `trait_2`, `rank_2`: trait **keys** (e.g. `KIND`,
  `BOLD`) and ranks (`C`, `B`, `A`, `S`). Leave the trait blank if absent.
- `name_en`, `name_ja`, `name_zh_hant`, `name_ko`: the pet's name per
  language. Leave a name blank if the pet is not on that server (or unknown).

**Adding a new trait or rarity:** add a row to `data/i18n/traits.csv` (or
`rarity.csv`) with the new key and its translation in each language. The keys you
use in `pets.csv` and in the missions files must exist in these tables.

**Before submitting:** run `python -m scripts.validate_pet_data` — it checks that
every trait/rarity/location key resolves and that each missions file is
consistent.

## 2. Updating Missions (`data/missions/missions_YYMMDD.csv`)
Missions rotate through **6 regions** in a fixed loop. Each region has the same 5
locations and tasks every time; only the required traits change. One file covers
all servers. When a new batch of missions is released:
1.  **Copy the previous file of the same region** (6 updates earlier) and
    **Save As** `missions_YYMMDD.csv` (e.g. `missions_261203.csv` for a
    December 3, 2026 update).
    - *Reason: our CSV files are saved as **UTF-8 with BOM** so Excel reads them
      correctly; copying keeps that encoding.*
2.  Change only the trait keys.

**Columns:**
- `location`: a location key from `data/i18n/locations.csv` (e.g.
  `KYAROT_GREENHOUSE`). The location and task names shown to users come from
  that table.
- `trait_1`, `trait_2`: the required trait keys (e.g. `KEEN`, `BOND`). Leave
  `trait_2` blank if the mission needs only one trait.

A file must list each location at most once, and all its locations must belong
to the same region; the validator checks both.

**New locations or translations:** add or edit a row in
`data/i18n/locations.csv` (`key`, `region`, then `location_<lang>` and
`task_<lang>` for `en`, `zh_hant`, `ko`). A blank translation falls back to
English.

**Automated Check:**
We have an automated system to ensure all CSV files have the correct **UTF-8 with BOM** encoding. This check runs both locally (if configured) and on every Pull Request.

## Development Environment & Pre-commit
To make contributions easier and avoid CI failures, we use `pre-commit` to automatically fix encoding issues before you even push your changes.

### Setting up pre-commit
1. Install dependencies: `pip install -r requirements.txt`
2. Install the git hook: `pre-commit install`

### What happens if a commit fails?
If `pre-commit` finds a CSV file without a BOM, it will:
1.  **Block the commit.**
2.  **Automatically add the BOM** to the file for you.
3.  **Instruction:** You just need to `git add` the modified file again and run your commit command once more.

## Submitting Changes
- Ensure your CSV files are saved with **UTF-8 with BOM** encoding.
- Submit a Pull Request with the new or updated files.
- GitHub Actions will verify the encoding. If the check fails, the build will turn red.
