# 🐾 ddl-PetDispatch

[English](#english) | [中文](#中文)

---
## Please Note

⚠️ The pets and dispatch missions data may need to be updated for the CN server and definitely needs to be updated for the KR server. Currently the KR server uses the same data as the global server for testing only. If you are willing to update, please refer to [Contribution / 贡献指南](docs/wiki/Contribution-Guide.md) first!

⚠️ 中国服的宠物和任务信息可能需要更新。韩服的信息一定需要更新。目前的韩服数据和国际服相同，仅做测试用。如果你可以更新数据，请先参考[Contribution / 贡献指南](docs/wiki/Contribution-Guide-CN.md)


## English

**ddl-PetDispatch** is a globally optimal pet assignment calculator for farm dispatch tasks. It uses Mixed Integer Linear Programming (MILP) to find the best possible pet teams to maximize your reward tiers.

### 🚀 Quick Start (One-Liner)
If you have **Miniconda** or **Anaconda** installed, run this in your terminal inside the project folder:
```bash
conda create -n petdispatch python=3.9 -y && conda activate petdispatch && pip install -r requirements.txt
```

### 💻 How to Use

#### 1. Web Interface (Recommended)
Run the modern web-based UI:
```bash
streamlit run src/ui/web_gui.py
```
*   **Save/Load**: Use the sidebar to download your setup as a `.json` file and reload it later.
*   **Results**: View optimized teams directly on the same page.

#### 2. Command Line (CLI)
Run directly using a saved config file:
```bash
python main.py --config your_config.json
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
启动现代化的网页版 UI：
```bash
streamlit run src/ui/web_gui.py
```
*   **保存与读取**: 在侧边栏可以将您当前的宠物配置下载为 `.json` 文件，下次使用时直接上传即可。
*   **实时结果**: 方案计算结果将直接显示在输入区域下方。

#### 2. 命令行界面 (CLI)
使用已保存的配置文件直接运行：
```bash
python main.py --config 你的配置文件.json
```

### 📖 相关文档
- [用户指南](docs/wiki/User-Guide-CN.md)
- [安装指南](docs/wiki/Installation-Guide-CN.md)
- [贡献指南](docs/wiki/Contribution-Guide-CN.md)
- [算法说明 (英文)](docs/wiki/Algorithm-Explanation.md)
- [软件架构 (英文)](docs/wiki/Software-Architecture.md)
