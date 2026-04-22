# Software Architecture Overview

The `trickcal-team-optimizer` project is designed with a modular architecture to separate data handling, core logic, and user interfaces. This structure allows for easy maintenance and expansion to different game servers (CN, GL, KR).

## Directory Structure
```text
trickcal-team-optimizer/
├── main.py              # CLI Entry Point
├── data/                # Server-specific CSV data (cn, gl, kr)
├── docs/wiki/           # Documentation and Wiki files
└── src/
    ├── core/            # Mathematical models and constants
    │   ├── assignment.py # MILP Solver implementation (PuLP)
    │   ├── scoring.py    # Pet-task score precomputation
    │   └── constants.py  # Server-specific reward levels and rules
    ├── data_loader/     # CSV ingestion logic
    └── ui/              # User Interfaces
        ├── cli.py       # Command Line logic
        ├── gui.py       # Basic Desktop GUI (Tkinter)
        └── web_gui.py   # Modern Web Interface (Streamlit)
```

## Key Components

### 1. Data Layer (`src/data_loader/`)
Handles loading pet traits and job requirements from server-specific subdirectories. It ensures that pet names and tasks are correctly identified for the solver.

### 2. Core Logic (`src/core/`)
- **Scoring**: Precomputes a reward matrix mapping pets to potential jobs based on traits and rarity.
- **Assignment**: The "brain" of the application. It builds a mathematical model using **Mixed Integer Linear Programming (MILP)** to maximize the total quantity of rewards (carrots) and solves it for the global optimum using the `PuLP` library.

### 3. UI Layer (`src/ui/`)
- **Web GUI (`web_gui.py`)**: The primary interface. Built with Streamlit, it provides the most robust rendering for Chinese characters and features configuration save/load support.
- **CLI (`main.py` / `cli.py`)**: A lightweight interface for quick calculations or automated runs using saved config files.
- **Tkinter GUI (`gui.py`)**: A basic desktop fallback for environments without a web browser or Streamlit support.

## Server-Specific Logic
The application dynamically switches its context based on the selected server (CN, GL, or KR). This affects:
- The data paths (e.g., `data/gl/`).
- The character encoding (Simplified vs. Traditional Chinese).
- The reward tier labels and label-threshold mappings used in result reporting and optimization.
