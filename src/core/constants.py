# 技能分值映射
SKILL_SCORE_MAP = {
    'C': 7,
    'B': 12,
    'A': 17,
    'S': 22
}

# 稀有度基础分映射
RARITY_BASE_MAP = {
    '普通宠物': 2,
    '高级宠物': 2,
    '稀有宠物': 3,
    '传说宠物': 5
}

RARITY_BASE_MAP_EN = {
    'Normal': 2,
    'Rare': 2,
    'Unique': 3,
    'Legendary': 5
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
    'gl': [
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
