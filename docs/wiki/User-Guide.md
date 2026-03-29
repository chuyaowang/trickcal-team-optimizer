# User Guide

Welcome to the **ddl-PetDispatch** calculator! This tool helps you find the most efficient way to assign your pets to farm dispatch tasks to maximize your rewards.

## Getting Started

1.  **Select Your Server**: Choose between CN, GL, or KR to ensure the data matches your game version.
2.  **Choose a Job Batch**: Select the current active job list from the dropdown menu.
3.  **Identify Your Pets**:
    -   In the **Owned Pets** list, select all pets you currently have in your inventory.
    -   In the **Farm Pets** list, find pets available from your friends. Double-click the "Count" column to set how many copies of that pet you can borrow.
4.  **Set Task Limit (P)**: Choose how many dispatch missions you want to run simultaneously (usually between 2 and 5).

## Running the Calculation

Click the **"🚀 Start Calculation"** button. The solver will analyze thousands of possible combinations using Mixed Integer Linear Programming to find the global optimal solution.

## Understanding Results

-   **Total Tier Reward**: The sum of the reward levels achieved across all tasks.
-   **Task Details**: For each task, the tool will show:
    -   The recommended team.
    -   Whether a pet is borrowed (marked with "Borrow").
    -   The raw score and the predicted reward level (e.g., S, A, or Special).

## Tips
-   The solver prioritizes hitting higher reward tiers over maximizing raw points.
-   Borrowing pets is limited to a total of 3 across all tasks.
