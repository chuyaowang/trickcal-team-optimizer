# 🐾 ddl-PetDispatch

[English](#english) | [中文](#中文)

---
## Please Note: Help Needed!

⚠️ **Help is needed to update the pets and dispatch missions data for the calculator!**
⚠️ **宠物和任务信息需要帮助更新！**

📢 Current Status:

- \[GL-CN\]: 国际服（中文）宠物，任务数据已更新 (游戏更新 20260326)
- \[GL-EN\]: Global server (English) pet and missions data updated (Game update 20260326)
- \[CN\]: 中国服的宠物和任务信息可能需要更新。如果你可以更新数据，请先参考[Contribution / 贡献指南](docs/wiki/Contribution-Guide-CN.md)!
- \[KR\]: 需要更新。目前的韩服数据和国际服相同，仅做测试用。Currently the KR server uses the same data as the global server for testing only. If you are willing to update, please refer to [Contribution / 贡献指南](docs/wiki/Contribution-Guide.md) first!

## English

**ddl-PetDispatch** is a globally optimal pet assignment calculator for farm dispatch tasks. It uses Mixed Integer Linear Programming (MILP) to find the best possible pet teams to maximize your reward tiers.

### 🚀 Quick Start (One-Liner)
If you have **Miniconda** or **Anaconda** installed, run this in your terminal inside the project folder:
```bash
conda create -n petdispatch python=3.9 -y && conda activate petdispatch && pip install -r requirements.txt
```

### 💻 How to Use

#### 1. Web Interface (Recommended)
Run the modern web-based UI with **Multi-language support**:
```bash
streamlit run src/ui/web_gui.py
```
*   **UI Language**: Toggle between English and Chinese in the sidebar.
*   **Save/Load Configs**: Download your setup as a `.json` file and reload it instantly later.
*   **Results**: View optimized teams directly on the same page.

#### 2. Command Line (CLI)
Run directly using a saved config file:
```bash
python main.py --config your_config.json --lang en
```

### 📖 Documentation
- [User Guide](docs/wiki/User-Guide.md)
- [Installation Guide](docs/wiki/Installation-Guide.md)
- [Contribution Guide](docs/wiki/Contribution-Guide.md)
- [Algorithm Explanation](docs/wiki/Algorithm-Explanation.md)
- [Software Architecture](docs/wiki/Software-Architecture.md)

---

## 中文

**ddl-PetDispatch** 是一款针对农场派遣任务的全局最优宠物分配计算器。它利用混合整数线性规划 (MILP) 算法，自动寻找能够最大化奖励等级的宠物组合方案。

### 🚀 快速安装 (一键指令)
如果您已安装 **Miniconda** 或 **Anaconda**，请在项目文件夹内运行：
```bash
conda create -n petdispatch python=3.9 -y && conda activate petdispatch && pip install -r requirements.txt
```

### 💻 使用说明

#### 1. 网页界面 (推荐)
启动支持**多语言切换**的现代网页版 UI：
```bash
streamlit run src/ui/web_gui.py
```
*   **UI语言切换**: 在侧边栏可自由切换中英文界面。
*   **保存与读取**: 在侧边栏可以将您当前的宠物配置下载为 `.json` 文件，下次使用时直接上传。
*   **彩色面板**: 方案计算结果以不同颜色的卡片显示在输入区域下方。

#### 2. 命令行界面 (CLI)
使用已保存的配置文件直接运行：
```bash
python main.py --config 你的配置文件.json --lang cn
```

### 📖 相关文档
- [用户指南](docs/wiki/User-Guide-CN.md)
- [安装指南](docs/wiki/Installation-Guide-CN.md)
- [贡献指南](docs/wiki/Contribution-Guide-CN.md)
- [算法说明 (英文)](docs/wiki/Algorithm-Explanation.md)
- [软件架构 (英文)](docs/wiki/Software-Architecture.md)
