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

# 奖励等级阈值
REWARD_LEVELS = [
    (37, "特阶"),
    (25, "一阶"),
    (13, "二阶"),
    (5, "三阶"),
    (1, "四阶"),
    (0, "无奖励")
]

# 约束条件
CONSTRAINTS = {
    'MAX_PETS_PER_TASK': 3,
    'MAX_BORROWED_PER_TASK': 1,
    'MAX_BORROWED_TOTAL': 3,
    'SPECIAL_SCORE_THRESHOLD': 37
}
