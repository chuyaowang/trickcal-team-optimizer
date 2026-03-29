# User Guide

Welcome to the **ddl-PetDispatch** calculator! This tool helps you find the most efficient way to assign your pets to farm dispatch tasks to maximize your rewards.

## Choosing an Interface

The application offers three ways to interact with the solver:
1.  **Web UI (Recommended)**: Best for most users, handles fonts perfectly.
2.  **Basic GUI**: A lightweight desktop window using Tkinter.
3.  **Command Line (CLI)**: For advanced users or automated scripts.

---

## 1. Web Interface (Streamlit) 🌐

Run via: `streamlit run src/ui/web_gui.py`

### Getting Started
1.  **Select Your Server**: Choose between CN, GL, or KR in the sidebar.
2.  **Choose a Job Batch**: Select the current active job list from the dropdown.
3.  **Identify Your Pets**:
    -   **Owned Pets**: Check the boxes for pets you have. Use the search box to filter.
    -   **Borrowed Pets**: Set the number of copies available from friends using the number inputs.
4.  **Set Task Limit (P)**: Choose how many dispatch missions to run simultaneously (2-5).

### Managing Your Configuration 💾
You can save your setup to avoid re-entering it:
-   **Saving**: Click **"📥 Download Current Config"** in the sidebar to save a `.json` file.
-   **Loading**: Use the file uploader in the sidebar to restore your settings from a `.json` file.

---

## 2. Basic Desktop GUI (Tkinter) 🖥️

Run via: `python -m src.ui.gui`

This is a simple version of the tool that runs as a standard window on your computer.

### How to Use
1.  **Server & Job**: Select the server and the job file at the top.
2.  **Selection**: 
    -   Highlight pets in the "Owned" list (hold Ctrl or Shift for multiple).
    -   In the "Farm" table, **double-click** the "Count" column for a pet to enter the number of borrowable copies.
3.  **Calculate**: Click the button to see results in the text area below.

---

## Understanding Results

Regardless of the UI, the results show:
-   **Summary Metrics**: Total tier reward points and borrow counts.
-   **Task Details**: Each recommended team, their raw score, and the predicted reward level (e.g., S, A, or Special).

## Tips
-   The solver prioritizes hitting higher reward tiers (e.g., reaching 37 points) over maximizing raw points.
-   Total borrowing is capped at 3 pets across all active tasks.
