# User Guide

Welcome to the **ddl-PetDispatch** calculator! This tool helps you find the most efficient way to assign your pets to farm dispatch tasks to maximize your rewards.

## Choosing an Interface

The application offers three ways to interact with the solver:
1.  **Web UI (Recommended)**: Best experience, full multi-language and config support.
2.  **Basic GUI**: A lightweight desktop window using Tkinter.
3.  **Command Line (CLI)**: For advanced users or automated scripts.

---

## 1. Web Interface (Streamlit) 🌐

Run via: `streamlit run src/ui/web_gui.py`

### Getting Started
1.  **Language**: Toggle between **English** and **Chinese** at the top of the sidebar.
2.  **Select Your Server**: Choose between CN, GL-CN, GL-EN, or KR.
    - *Note: GL-EN uses English names for pets and tasks.*
3.  **Choose a Job Batch**: Select the current active job list from the dropdown.
4.  **Identify Your Pets**:
    -   **Owned Pets**: Check the boxes for pets you have. Organized in a 2-column grid.
    -   **Borrowed Pets**: Set the number of copies available from friends using the number inputs (3-column grid).
5.  **Set Task Limit (P)**: Choose how many missions to run simultaneously (2-5).

### Managing Your Configuration 💾
You can save your setup to avoid re-entering it:
-   **Saving**: Click **"📥 Download Current Config"** in the sidebar.
-   **Loading**: Use the file uploader in the sidebar to restore your pets and settings.

---

## 2. Basic Desktop GUI (Tkinter) 🖥️

Run via: `python -m src.ui.gui`

This is a simple version of the tool that runs as a standard window on your computer.

### How to Use
1.  **Server & Job**: Select the server and the job file at the top.
2.  **Selection**: 
    -   Highlight pets in the "Owned" list.
    -   In the "Farm" table, **double-click** the "Count" column to enter borrowable copies.
3.  **Calculate**: Click the button to see results below.

---

## Understanding Results

Regardless of the UI, the results show:
-   **Summary Metrics**: Total tier reward points and borrow counts.
-   **Task Details**: Each recommended team, their raw score, and the predicted reward level (e.g., S, A, or Special).

## Tips
-   The solver prioritizes hitting higher reward tiers (e.g., reaching 37 points) over maximizing raw points.
-   Total borrowing is capped at 3 pets across all active tasks.
