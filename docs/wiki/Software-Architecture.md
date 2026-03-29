# Software Architecture Overview

The `ddl-PetDispatch` project is designed with a modular architecture to separate data handling, core logic, and user interfaces. This structure allows for easy maintenance and expansion to different game servers (CN, GL, KR).

## Directory Structure
```text
ddl-PetDispatch/
├── main.py              # CLI Entry Point
├── data/                # Server-specific CSV data (cn, gl, kr)
├── docs/wiki/           # Documentation and Wiki files
└── src/
    ├── core/            # Mathematical models and constants
    │   ├── assignment.py # MILP Solver implementation
    │   ├── scoring.py    # Pet-task score precomputation
    │   └── constants.py  # Server-specific reward levels and rules
    ├── data_loader/     # CSV ingestion logic
    └── ui/              # User Interfaces (CLI and GUI)
```

## Key Components

### 1. Data Layer (`src/data_loader/`)
Handles loading pet traits and job requirements from server-specific subdirectories. It ensures that the unique identities of pets and tasks are maintained for the solver.

### 2. Core Logic (`src/core/`)
- **Scoring**: Precomputes a reward matrix mapping every available pet to every potential job based on traits and rarity.
- **Assignment**: The "brain" of the application. It uses `PuLP` to build a mathematical model of the dispatch problem and solve it for the global optimum.

### 3. UI Layer (`src/ui/`)
- **CLI**: A lightweight command-line interface for quick calculations.
- **GUI**: A `tkinter`-based desktop application providing a visual way to select pets, set borrow counts, and view recommended teams.

## Server-Specific Logic
The application dynamically switches its context based on the selected server (CN, GL, or KR). This affects:
- The path used to load `pets.csv` and `jobs_*.csv`.
- The reward tier names and thresholds used in result reporting.
