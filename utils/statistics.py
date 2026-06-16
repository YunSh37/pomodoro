"""统计计算工具 — 段位、果实合成、每日结算、箴言"""

from datetime import datetime, date, timedelta


# ── 果实合成 ──────────────────────────────────────────────

def calc_fruits(total_fragments: int) -> dict:
    """计算番茄果实合成结果（四级：白→绿→紫→红）

    规则：5 白 → 1 绿, 5 绿 → 1 紫, 5 紫 → 1 红（红满不再升级）

    参数:
        total_fragments: 累计成功番茄数（白碎片总数）
    返回:
        {'white': 0-4, 'green': int, 'purple': int, 'red': int}
    """
    f = max(0, total_fragments)
    levels = {}
    for name in ("white", "green", "purple"):
        levels[name] = f % 5
        f //= 5
    levels["red"] = f  # 红满不再限制升级
    return levels


# ── 心碎合成 ──────────────────────────────────────────────

def calc_broken_hearts(total_broken: int) -> dict:
    """计算心碎合成结果

    规则：3 💔 → 1 🤡, 3 🤡 → 1 🖤, 最多 5 🖤

    参数:
        total_broken: 累计中断次数
    返回:
        {'black': 0~5, 'clown': 0~2, 'broken': 0~2}
    """
    b = max(0, total_broken)
    healing = b // 3
    broken_rem = b % 3
    black = healing // 3
    healing_rem = healing % 3
    black = min(black, 5)  # 最多 5 个黑心
    return {"black": black, "clown": healing_rem, "broken": broken_rem}


# ── 段位系统 ──────────────────────────────────────────────

RANKS = [
    (0,  "青铜专注者"),
    (3,  "白银专注者"),
    (6,  "黄金专注者"),
    (11, "钻石专注者"),
    (21, "专注大师"),
    (41, "番茄神"),
]
"""段位阈值：(最低连续天数, 段位名称)"""


def get_rank(streak_days: int) -> str:
    """根据连续专注天数返回段位名称

    参数:
        streak_days: 连续专注天数
    返回:
        段位名称字符串，如 "黄金专注者"
    """
    rank = RANKS[0][1]
    for threshold, name in RANKS:
        if streak_days >= threshold:
            rank = name
    return rank


# ── 禅意箴言 ──────────────────────────────────────────────

ZEN_QUOTES = {
    5: "心流如溪，专注成海。今天你与时间温柔相处。",
    4: "平静的专注最有力，保持自己的节奏。",
    3: "完成比完美更重要，每一步都算数。",
    2: "短暂的游离，是为了让注意力回归时更锋利。",
    1: "允许自己偶尔断电，番茄钟等你随时重启。",
}
"""心情分值 → 箴言映射"""

NO_RECORD_QUOTE = "种下第一个番茄，看看今天能收获多少专注吧。"


def get_zen_quote(mood: int) -> str:
    """根据最近心情分值返回对应箴言

    参数:
        mood: 心情分值 1~5，0 表示无记录
    返回:
        箴言字符串
    """
    return ZEN_QUOTES.get(mood, NO_RECORD_QUOTE)


# ── 每日结算 ──────────────────────────────────────────────

def get_today_key(reset_hour: int = 4) -> str:
    """获取今日日期键（考虑重置时间）

    参数:
        reset_hour: 每日重置小时
    返回:
        YYYY-MM-DD 格式的日期字符串
    """
    now = datetime.now()
    if now.hour < reset_hour:
        now = now - timedelta(days=1)
    return now.strftime("%Y-%m-%d")


def daily_settlement(profile: dict, today_completed: int, today_abandoned: int):
    """每日结算：根据今日表现更新连续专注天数

    规则：
      - 成功番茄 ≥1 且中断 =0 → 连续天数 +1
      - 成功番茄 ≥1 且中断 >0 → 连续天数不变
      - 成功番茄 =0 → 连续天数 -2（最低 0）

    参数:
        profile:      user_profile 字典（原地修改）
        today_completed: 今日成功番茄数
        today_abandoned: 今日中断番茄数
    """
    if today_completed >= 1 and today_abandoned == 0:
        profile["streak_days"] = profile.get("streak_days", 0) + 1
    elif today_completed >= 1 and today_abandoned > 0:
        pass  # 保持不变
    else:
        profile["streak_days"] = max(0, profile.get("streak_days", 0) - 2)

    profile["last_active_date"] = get_today_key()
