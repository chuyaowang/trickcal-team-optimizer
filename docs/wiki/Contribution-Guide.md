# Contribution Guide

Help keep the **trickcal-team-optimizer** data up to date! This guide explains how to update pet and task information for different game servers.

## Data Structure
Pets now live in a single canonical file; only the per-server **jobs** files are
split by server:
- `data/pets.csv`: the canonical master — one row per pet, shared across servers.
- `data/i18n/traits.csv`, `data/i18n/rarity.csv`: translation tables mapping
  language-neutral keys to localized names.
- `data/pet_images/<id>.png`: pet icons, named by the pet's `id`.
- `data/<server>/jobs_*.csv`: dispatch tasks per server (`cn`, `gl-cn`,
  `gl-en`, `kr`). `kr` is **TESTING DATA ONLY**.

Each server maps to one language: `cn`→Simplified, `gl-cn`→Traditional,
`gl-en`→English, `kr`→Korean. A pet is considered available on a server when it
has a non-empty name in that server's language column.

## 1. Updating Pets (`data/pets.csv`)
Add or edit one row per pet in the canonical master.

**Columns:**
- `id`: the pet's numeric id; must match its icon `data/pet_images/<id>.png`.
  May be left blank (the pet then shows without an icon).
- `rarity_key`: one of `NORMAL`, `RARE`, `UNIQUE`, `LEGENDARY`.
- `trait_1`, `rank_1`, `trait_2`, `rank_2`: trait **keys** (e.g. `KIND`,
  `BOLD`) and ranks (`C`, `B`, `A`, `S`). Leave the trait blank if absent.
- `name_en`, `name_zh_hans`, `name_zh_hant`, `name_ko`: the pet's name per
  language. Leave a name blank if the pet is not on that server (or unknown).

**Adding a new trait or rarity:** add a row to `data/i18n/traits.csv` (or
`rarity.csv`) with the new key and its translation in each language. The keys you
use in `pets.csv` and in the jobs files must exist in these tables.

**Before submitting:** run `python -m scripts.validate_pet_data` — it checks that
every trait/rarity key resolves and that jobs traits map to keys.

## 2. Updating Jobs (`jobs_*.csv`)
Dispatch tasks rotate periodically. When a new batch of tasks is released:
1.  **Do not create a new CSV from scratch.** 
2.  **Open an existing `jobs_*.csv`** file in the server's folder.
3.  Edit the values and **Save As** a new file.
    - *Reason: Our CSV files are pre-formatted with **UTF-8 with BOM**. This ensures that Excel correctly identifies the Chinese characters. If you create a new file without BOM, Excel may display the characters as unreadable junk.*
4.  Use the naming convention `jobs_YYMMDD.csv` (e.g., `jobs_260326.csv` for a March 26, 2026 update).

**Automated Check:**
We have an automated system to ensure all CSV files have the correct **UTF-8 with BOM** encoding. This check runs both locally (if configured) and on every Pull Request.

**Columns:**
- `Location`: The name of the map/area.
- `Task`: The specific name of the dispatch task.
- `Trait 1`, `Trait 2`: The required traits for score bonuses, written in the
  server's language. Each must match a translation in `data/i18n/traits.csv` so
  it can be mapped to a trait key (the validator flags any that don't).

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
- Submit a Pull Request with the new or updated files in the correct server directory.
- GitHub Actions will verify the encoding. If the check fails, the build will turn red.
