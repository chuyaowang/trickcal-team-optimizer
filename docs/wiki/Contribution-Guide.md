# Contribution Guide

Help keep the **ddl-PetDispatch** data up to date! This guide explains how to update pet and task information for different game servers.

## Data Structure
Data is organized by server in the `data/` directory:
- `data/cn/`: China Server (Simplified Chinese)
- `data/gl-cn/`: Global Server (Traditional Chinese)
- `data/gl-en/`: Global Server (English)
- `data/kr/`: Korea Server (Traditional Chinese / English) **TESTING DATA ONLY**

## 1. Updating Pets (`pets.csv`)
Each server subdirectory has its own `pets.csv`. Use this file to add new pets as they are released in that specific server.

**Crucial Language Note:**
- **China Server (CN)**: You **must** use **Simplified Chinese** for pet names and traits.
- **Global Server (GL)**: You **must** use **Traditional Chinese** for pet names and traits.
- Failure to use the correct character set will cause the scoring logic to fail to find matches.

**Columns:**
- `Pet`: The unique name of the pet.
- `Rarity`: Rarity level (e.g., `传说宠物`, `稀有宠物`).
- `Trait_1`, `Rank_1`: The first skill and its rank (C, B, A, S).
- `Trait_2`, `Rank_2`: The second skill and its rank.

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
- `Trait 1`, `Trait 2`: The required traits for score bonuses.

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
