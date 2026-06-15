# 贡献指南

感谢您帮助保持 **trickcal-team-optimizer** 数据的准确与及时！本指南将说明如何为不同服务器更新宠物和任务信息。

## 数据结构
宠物数据现已合并到一个统一的文件中；只有各服务器的**任务**文件仍按服务器拆分：
- `data/pets.csv`: 统一的宠物主表 —— 每只宠物一行，所有服务器共享。
- `data/i18n/traits.csv`、`data/i18n/rarity.csv`: 翻译表，将语言无关的“键”映射为各语言名称。
- `data/pet_images/<id>.png`: 宠物图标，按宠物的 `id` 命名。
- `data/<server>/jobs_*.csv`: 各服务器的派遣任务（`cn`、`gl-cn`、`gl-en`、`kr`）。`kr` **目前是测试数据**。

每个服务器对应一种语言：`cn`→简体、`gl-cn`→繁体、`gl-en`→英文、`kr`→韩文。
当某只宠物在该服务器对应语言的名称列非空时，即视为该宠物在此服务器可用。

## 1. 更新宠物数据 (`data/pets.csv`)
在主表中为每只宠物添加或编辑一行。

**列说明:**
- `id`: 宠物的数字 id，必须与其图标 `data/pet_images/<id>.png` 对应。可留空（此时该宠物不显示图标）。
- `rarity_key`: 取值为 `NORMAL`、`RARE`、`UNIQUE`、`LEGENDARY` 之一。
- `trait_1`, `rank_1`, `trait_2`, `rank_2`: 特性**键**（如 `KIND`、`BOLD`）及其等级（`C`, `B`, `A`, `S`）。无特性时留空。
- `name_en`, `name_zh_hans`, `name_zh_hant`, `name_ko`: 各语言下的宠物名称。若该宠物不在某服务器（或名称未知），留空即可。

**新增特性或稀有度:** 在 `data/i18n/traits.csv`（或 `rarity.csv`）中添加一行，填写新的键及其各语言翻译。
您在 `pets.csv` 和任务文件中使用的键，必须在这些翻译表中存在。

**提交前:** 请运行 `python -m scripts.validate_pet_data` —— 它会检查所有特性/稀有度键是否有效、任务特性是否能映射到键。

## 2. 更新任务数据 (`jobs_*.csv`)
游戏中的派遣任务会定期轮换。当新一轮任务开启时：
1.  **不要从零开始创建新的 CSV 文件。**
2.  **打开该服务器目录下现有的 `jobs_*.csv` 文件。**
3.  修改其中的内容，然后**另存为**一个新文件。
    - *原因：我们的 CSV 文件预设为 **带 BOM 的 UTF-8** 编码。这能确保 Excel 正确识别中文字符。如果您直接创建新文件，Excel 可能会将其识别为乱码。*
4.  命名规则为 `jobs_YYMMDD.csv`（例如：2026 年 3 月 26 日的更新应命名为 `jobs_260326.csv`）。

**自动化检查:**
我们拥有一套自动化系统，用于确保所有 CSV 文件都具有正确的 **带 BOM 的 UTF-8** 编码。此检查会在本地（如果已配置）以及每次 Pull Request 时运行。

**列说明:**
- `Location`: 地图或区域名称。
- `Task`: 具体派遣任务名称。
- `Trait 1`, `Trait 2`: 该任务要求的加成特性，使用该服务器对应语言填写。每个特性都必须能在 `data/i18n/traits.csv` 中找到对应翻译，以便映射为特性键（校验脚本会标记无法匹配的特性）。

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
- 提交 Pull Request，将新增或修改的文件放入正确的服务器文件夹中。
- GitHub Actions 将验证编码。如果检查未通过，构建将显示失败。
