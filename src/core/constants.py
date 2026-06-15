# 技能分值映射
SKILL_SCORE_MAP = {
    'C': 7,
    'B': 12,
    'A': 17,
    'S': 22
}

# Server -> data language (1:1; used for names, traits, and reward labels)
SERVER_LANG = {
    "cn": "zh_hans",
    "gl-cn": "zh_hant",
    "gl-en": "en",
    "kr": "ko",
}

# Rarity base score, keyed by language-neutral rarity key
RARITY_BASE_SCORE = {
    "NORMAL": 2,
    "RARE": 2,
    "UNIQUE": 3,
    "LEGENDARY": 5,
}

# 奖励等级阈值映射 (Server -> List of (threshold, level))
SERVER_REWARD_LEVELS = {
    'cn': [
        (37, "特阶"),
        (25, "一阶"),
        (13, "二阶"),
        (5, "三阶"),
        (1, "四阶"),
        (0, "无奖励")
    ],
    'gl-cn': [
        (37, "S"),
        (25, "A"),
        (13, "B"),
        (5, "C"),
        (1, "D"),
        (0, "N/A")
    ],
    'gl-en': [
        (37, "S"),
        (25, "A"),
        (13, "B"),
        (5, "C"),
        (1, "D"),
        (0, "N/A")
    ],
    'kr': [
        (37, "S"),
        (25, "A"),
        (13, "B"),
        (5, "C"),
        (1, "D"),
        (0, "N/A")
    ]
}

# MILP 约束与参数
CONSTRAINTS = {
    'M': 3,      # 每个任务最大宠物数
    'A': 3,      # 最大总借用数
    'TIERS': [0, 1, 5, 13, 25, 37]
}

# Tier reward mapping
TIER_REWARD_MAP = {
    # Assuming max dispatch time (22 hours) and all servers share the same mapping
    # Maps Tier threshold: Reward
    0: 0,   # N/A
    1: 5,   # D
    5: 7.5, # C
    13: 9,  # B
    25: 11, # A
    37: 14  # S
}