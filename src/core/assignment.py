import pulp
from collections import defaultdict
from typing import List, Dict, Tuple
from src.core.constants import CONSTRAINTS, TIER_REWARD_MAP
from src.core.scoring import get_reward_range

def calculate_best_assignment(
    my_pets: List[Dict],
    aux_pets_counts: Dict[str, int],
    tasks: List[Dict],
    pet_task_scores: Dict[Tuple[str, str], int],
    max_active_jobs: int
) -> Dict:
    """
    MILP-based assignment logic using PuLP.
    Optimizes job selection and pet assignment to maximize tier-based rewards.
    """
    jobs = [t['task'] for t in tasks]
    reg_workers = [f"{p['name']}_REG" for p in my_pets]

    # Generate unique IDs for duplicate borrows.
    aux_workers = [
        f"{name}_{i+1}_AUX" if aux_pets_counts.get(name, 0) > 1 else f"{name}_AUX"
        for name, count in aux_pets_counts.items()
        for i in range(count)
    ]

    all_workers = reg_workers + aux_workers

    def get_base_name(worker_string):
        # Strips the tags to find the base character (e.g., "John_1_AUX" -> "John")
        if '_REG' in worker_string:
            return worker_string.replace('_REG', '')
        if '_AUX' in worker_string:
            parts = worker_string.replace('_AUX', '').split('_')
            # If it's like "Name_1_AUX", parts is ["Name", "1"]
            if parts[-1].isdigit():
                return "_".join(parts[:-1])
            return parts[0]
        return worker_string

    # Dictionary mapping every unique ID to its base name
    npc_identity = {w: get_base_name(w) for w in all_workers}

    # Dictionary grouping all unique IDs by their base name for the exclusivity constraint
    workers_by_name = defaultdict(list)
    for w in all_workers:
        workers_by_name[npc_identity[w]].append(w)

    # Generate the solver-ready reward matrix
    rewards = {}
    for w in all_workers:
        base_name = npc_identity[w]
        for j in jobs:
            # Look up score in precomputed scores (precomputed uses base names)
            rewards[(w, j)] = pet_task_scores.get((base_name, j), 0)

    # --- PARAMETERS ---
    m = CONSTRAINTS['M']      # Max capacity per job
    a = CONSTRAINTS['A']      # Global borrow limit
    p = max_active_jobs       # Job limit (user input)
    tiers = CONSTRAINTS['TIERS']
    tier_reward_map = TIER_REWARD_MAP

    # --- INITIALIZE MILP ---
    prob = pulp.LpProblem("Max_Reward_Job_Selection", pulp.LpMaximize)

    # --- DECISION VARIABLES ---
    x = pulp.LpVariable.dicts("assign", ((w, j) for w in all_workers for j in jobs), cat='Binary')
    y = pulp.LpVariable.dicts("select_job", jobs, cat='Binary')
    v = pulp.LpVariable.dicts("tier", ((j, t) for j in jobs for t in tiers), cat='Binary')

    # --- OBJECTIVE FUNCTION ---
    # Maximize reward, with a tiny penalty for each pet to encourage minimal teams on ties.
    # Higher penalty for borrowed pets (AUX) to prioritize owned pets (REG).
    prob += pulp.lpSum(tier_reward_map[t] * v[j, t] for j in jobs for t in tiers) - \
            0.0001 * pulp.lpSum(x[w, j] for w in reg_workers for j in jobs) - \
            0.00011 * pulp.lpSum(x[w, j] for w in aux_workers for j in jobs)
            
    # --- CONSTRAINTS ---

    # Constraint A: Physical Reality
    for w in all_workers:
        prob += pulp.lpSum(x[w, j] for j in jobs) <= 1

    # Constraint B: Global Borrow Limit
    prob += pulp.lpSum(x[w, j] for w in aux_workers for j in jobs) <= a

    # Constraint C: Maximum Active Jobs
    prob += pulp.lpSum(y[j] for j in jobs) <= p

    # Constraint D: The Linking & Max Capacity Constraint
    for j in jobs:
        prob += pulp.lpSum(x[w, j] for w in all_workers) <= m * y[j]

    # Constraint E: Max 1 Friend per Team
    for j in jobs:
        prob += pulp.lpSum(x[w, j] for w in aux_workers) <= 1

    # Constraint F: Mutual Exclusivity (No Clones on a Team)
    for j in jobs:
        for name, name_group in workers_by_name.items():
            if len(name_group) > 1:
                prob += pulp.lpSum(x[w, j] for w in name_group) <= 1

    # Constraint G: Tier Validation
    for j in jobs:
        # G1: "Claim One Prize"
        prob += pulp.lpSum(v[j, t] for t in tiers) == y[j]
        # G2: "Earn Your Prize"
        raw_score = pulp.lpSum(rewards[w, j] * x[w, j] for w in all_workers)
        chosen_tier_value = pulp.lpSum(t * v[j, t] for t in tiers)
        prob += raw_score >= chosen_tier_value

    # --- SOLVE ---
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    if pulp.LpStatus[prob.status] != 'Optimal':
        return {'total': 0, 'min_total': 0, 'max_total': 0, 'assignments': [], 'status': pulp.LpStatus[prob.status]}

    # --- PARSE RESULTS ---
    assignments = []
    min_total = 0
    max_total = 0
    for j in jobs:
        if pulp.value(y[j]) == 1:
            team = []
            job_score = 0
            for w in all_workers:
                if pulp.value(x[w, j]) == 1:
                    base_name = npc_identity[w]
                    team.append({
                        'name': base_name,
                        'is_borrowed': '_AUX' in w
                    })
                    job_score += rewards[(w, j)]
            
            l, h = get_reward_range(job_score)
            min_total += l
            max_total += h
            
            task_obj = next(t for t in tasks if t['task'] == j)
            assignments.append({
                'task': task_obj,
                'team': team,
                'score': job_score
            })

    return {
        'total': float(pulp.value(prob.objective)),
        'min_total': min_total,
        'max_total': max_total,
        'borrowed': int(sum(pulp.value(x[w, j]) for w in aux_workers for j in jobs)),
        'total_pets': int(sum(pulp.value(x[w, j]) for w in all_workers for j in jobs)),
        'assignments': assignments,
        'status': 'Optimal'
    }
