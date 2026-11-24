# 技能分值映射
SKILL_SCORE_MAP = {
    'C': 7,
    'B': 12,
    'A': 17,
    'S': 22
}

# Server -> data language (1:1; used for names, traits, and reward labels)
SERVER_LANG = {
    "gl-cn": "zh_hant",
    "gl-en": "en",
    "gl-jp": "ja",
    "kr": "ko",
}

DEFAULT_SERVER = "gl-cn"


def normalize_server(server):
    """Return `server` if supported, else the default (e.g. retired 'cn' -> 'gl-cn')."""
    return server if server in SERVER_LANG else DEFAULT_SERVER

# Rarity base score, keyed by language-neutral rarity key
RARITY_BASE_SCORE = {
    "NORMAL": 2,
    "RARE": 2,
    "UNIQUE": 3,
    "LEGENDARY": 5,
}

# 奖励等级阈值映射 (Server -> List of (threshold, level))
SERVER_REWARD_LEVELS = {
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
    'gl-jp': [
        (37, "Sランク"),
        (25, "Aランク"),
        (13, "Bランク"),
        (5, "Cランク"),
        (1, "Dランク"),
        (0, "報酬なし")
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