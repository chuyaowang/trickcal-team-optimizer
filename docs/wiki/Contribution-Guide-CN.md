# 贡献指南

感谢您帮助保持 **trickcal-team-optimizer** 数据的准确与及时！本指南将说明如何为不同服务器更新宠物和任务信息。

## 数据结构
宠物和任务数据由所有服务器共享，只有显示语言不同：
- `data/pets.csv`: 统一的宠物主表 —— 每只宠物一行，所有服务器共享。
- `data/missions/missions_YYMMDD.csv`: 每次游戏更新的任务，所有服务器共享，使用语言无关的“键”填写。
- `data/i18n/traits.csv`、`data/i18n/rarity.csv`、`data/i18n/locations.csv`: 翻译表，将语言无关的“键”映射为各语言名称。
- `data/pet_images/<id>.png`: 宠物图标，按宠物的 `id` 命名。

每个服务器对应一种语言：`gl-cn`→繁体、`gl-en`→英文、`gl-jp`→日文、`kr`→韩文（暂不支持）。
当某只宠物在该服务器对应语言的名称列非空时，即视为该宠物在此服务器可用。

## 1. 更新宠物数据 (`data/pets.csv`)
在主表中为每只宠物添加或编辑一行。

**列说明:**
- `id`: 宠物的数字 id，必须与其图标 `data/pet_images/<id>.png` 对应。可留空（此时该宠物不显示图标）。
- `rarity_key`: 取值为 `NORMAL`、`RARE`、`UNIQUE`、`LEGENDARY` 之一。
- `trait_1`, `rank_1`, `trait_2`, `rank_2`: 特性**键**（如 `KIND`、`BOLD`）及其等级（`C`, `B`, `A`, `S`）。无特性时留空。
- `name_en`, `name_ja`, `name_zh_hant`, `name_ko`: 各语言下的宠物名称。若该宠物不在某服务器（或名称未知），留空即可。

**新增特性或稀有度:** 在 `data/i18n/traits.csv`（或 `rarity.csv`）中添加一行，填写新的键及其各语言翻译。
您在 `pets.csv` 和任务文件中使用的键，必须在这些翻译表中存在。

**提交前:** 请运行 `python -m scripts.validate_pet_data` —— 它会检查所有特性/稀有度/地点键是否有效，以及每个任务文件是否一致。

## 2. 更新任务数据 (`data/missions/missions_YYMMDD.csv`)
派遣任务按固定顺序在 **6 个区域**之间轮换。每个区域每次都是相同的 5 个地点和任务，只有要求的特性会变化。一个文件适用于所有服务器。当新一轮任务开启时：
1.  **复制同一区域的上一个文件**（即 6 次更新之前的文件），并**另存为** `missions_YYMMDD.csv`（例如：2026 年 12 月 3 日的更新应命名为 `missions_261203.csv`）。
    - *原因：我们的 CSV 文件预设为 **带 BOM 的 UTF-8** 编码，以便 Excel 正确识别；复制文件可保留该编码。*
2.  只修改特性键。

**列说明:**
- `location`: `data/i18n/locations.csv` 中的地点键（如 `KYAROT_GREENHOUSE`）。显示给用户的地点和任务名称来自该翻译表。
- `trait_1`, `trait_2`: 要求的特性键（如 `KEEN`、`BOND`）。只需要一个特性时，`trait_2` 留空。

每个文件中同一地点最多出现一次，且所有地点必须属于同一区域；校验脚本会检查这两点。

**新增地点或翻译:** 在 `data/i18n/locations.csv` 中添加或修改一行（`key`、`region`，以及 `en`、`ja`、`zh_hant`、`ko` 各语言的 `location_<lang>` 和 `task_<lang>`）。翻译留空时显示英文。

**自动化检查:**
我们拥有一套自动化系统，用于确保所有 CSV 文件都具有正确的 **带 BOM 的 UTF-8** 编码。此检查会在本地（如果已配置）以及每次 Pull Request 时运行。

## 开发环境与 Pre-commit
为了让贡献过程更轻松并避免 CI 失败，我们使用 `pre-commit` 在您提交更改之前自动修复编码问题。

### 设置 pre-commit
1. 安装依赖：`pip install -r requirements.txt`
2. 安装 git 钩子 (hook)：`pre-commit install`

### 如果提交 (commit) 失败了怎么办？
如果 `pre-commit` 发现 CSV 文件缺少 BOM，它将：
1.  **拦截此次提交。**
2.  **自动为您为该文件添加 BOM。**
3.  **操作指令:** 您只需要再次运行 `git add` 暂存被修改的文件，然后再次运行提交命令即可。

## 提交更改
- 请确保 CSV 文件以 **带 BOM 的 UTF-8** 编码保存。
- 提交包含新增或修改文件的 Pull Request。
- GitHub Actions 将验证编码。如果检查未通过，构建将显示失败。
