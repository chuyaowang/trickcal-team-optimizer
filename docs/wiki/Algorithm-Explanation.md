# MILP Solver Algorithm Explanation

This project uses **Mixed Integer Linear Programming (MILP)** to solve the pet dispatch assignment problem. Unlike traditional recursive search, MILP can find the global optimal solution across multiple tasks simultaneously while respecting complex constraints.

## Core Objective

The goal is to maximize the **Total Rewards** (carrots) across all selected jobs. 

$$ \text{Maximize } \sum_{j \in Jobs} \sum_{t \in Tiers} R(t) \cdot v_{j,t} $$

where $v_{j,t}$ is a binary variable that is 1 if job $j$ achieves reward tier $t$, and $R(t)$ is the actual carrot reward for that tier. This ensures the solver prioritizes hitting higher reward thresholds that yield more carrots over simply maximizing raw points that might not reach a new threshold.

## Decision Variables
- $x_{w,j}$: Binary variable (1 if worker $w$ is assigned to job $j$, 0 otherwise).
- $y_j$: Binary variable (1 if job $j$ is selected to be run).
- $v_{j,t}$: Binary variable (1 if job $j$ reaches score tier $t$).

## Constraints
1.  **Worker Uniqueness**: Each pet (owned or borrowed) can only be assigned to one job at a time.
2.  **Global Borrow Limit**: The total number of borrowed pets across all jobs cannot exceed a global limit (default: 3).
3.  **Active Job Limit**: Only a specific number of jobs (defined by user $P$) can be run simultaneously.
4.  **Team Size**: Each job can have between 1 and 3 pets.
5.  **Single Borrow per Job**: Each job can have at most one borrowed pet.
6.  **Duplicate/Clone Prevention**: If a user owns a pet and also borrows a copy of the same pet, they cannot both be in the same team.
7.  **Tier Validation**: A tier $t$ can only be claimed for job $j$ if the sum of raw pet scores in that team meets or exceeds the threshold $t$.

## Solver Implementation
The logic is implemented using the `PuLP` library in Python, which interfaces with the CBC solver to find the optimal assignment in a fraction of a second.
