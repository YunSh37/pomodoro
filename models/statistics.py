"""统计计算模块 — 时间范围筛选、图表数据聚合、周报数据生成"""

from datetime import datetime, date, timedelta
from collections import defaultdict
from models.data_manager import load_data


def _parse_start_time(record: dict) -> datetime | None:
    """解析番茄记录的 start_time 字段为 datetime 对象"""
    start_str = record.get("start_time", "")
    if not start_str:
        return None
    try:
        return datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


# ── 时间范围构建 ──────────────────────────────────────────

def get_today_range() -> tuple[datetime, datetime]:
    """返回今日时间范围（00:00:00 ~ 23:59:59）"""
    now = datetime.now()
    start = datetime(now.year, now.month, now.day, 0, 0, 0)
    end = start + timedelta(days=1)
    return start, end


def get_week_range() -> tuple[datetime, datetime]:
    """返回本周时间范围（周一日 00:00:00 ~ 周日 23:59:59）"""
    now = datetime.now()
    weekday = now.weekday()  # 0=周一, 6=周日
    start = datetime(now.year, now.month, now.day, 0, 0, 0) - timedelta(days=weekday)
    end = start + timedelta(days=7)
    return start, end


def get_month_range() -> tuple[datetime, datetime]:
    """返回本月时间范围（1日 00:00:00 ~ 次月1日 00:00:00）"""
    now = datetime.now()
    start = datetime(now.year, now.month, 1, 0, 0, 0)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1, 0, 0, 0)
    else:
        end = datetime(now.year, now.month + 1, 1, 0, 0, 0)
    return start, end


# ── 记录筛选 ──────────────────────────────────────────────

def filter_records(records: list, start: datetime, end: datetime) -> list:
    """筛选指定时间范围内的番茄记录

    参数:
        records: TomatoRecord 字典列表
        start:   起始时间（含）
        end:     结束时间（不含）
    返回:
        筛选后的记录列表
    """
    result = []
    for r in records:
        dt = _parse_start_time(r)
        if dt and start <= dt < end:
            result.append(r)
    return result


def get_records_by_range(range_key: str) -> list:
    """根据范围键获取对应的番茄记录

    参数:
        range_key: "today" / "week" / "month"
    返回:
        筛选后的记录列表
    """
    data = load_data()
    all_records = data.get("tomato_records", [])

    if range_key == "today":
        start, end = get_today_range()
    elif range_key == "week":
        start, end = get_week_range()
    elif range_key == "month":
        start, end = get_month_range()
    else:
        return all_records

    return filter_records(all_records, start, end)


# ── 专注时长柱状图数据 ────────────────────────────────────

def get_duration_bar_data(range_key: str) -> dict:
    """生成专注时长柱状图数据

    参数:
        range_key: "today" / "week" / "month"
    返回:
        {"labels": [...], "values": [...], "title": str, "xlabel": str}
          - today: 按小时分布 (0~23)
          - week:  按天分布 (周一~周日)
          - month: 按天分布 (1日~31日)
    """
    records = get_records_by_range(range_key)

    if range_key == "today":
        # 按小时聚合
        bins = defaultdict(int)
        for r in records:
            dt = _parse_start_time(r)
            if dt:
                bins[dt.hour] += r.get("duration_minutes", 0)
        labels = [f"{h}:00" for h in range(24)]
        values = [bins.get(h, 0) for h in range(24)]
        return {
            "labels": labels,
            "values": values,
            "title": "今日专注时长分布（按小时）",
            "xlabel": "小时",
        }

    elif range_key == "week":
        # 按星期分布
        now = datetime.now()
        weekday = now.weekday()  # 0=周一
        week_start = datetime(now.year, now.month, now.day) - timedelta(days=weekday)
        week_start = datetime(week_start.year, week_start.month, week_start.day)

        bins = defaultdict(int)
        for r in records:
            dt = _parse_start_time(r)
            if dt:
                day_key = datetime(dt.year, dt.month, dt.day)
                bins[str(day_key.date())] += r.get("duration_minutes", 0)

        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        labels = []
        values = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            key = str(day.date())
            day_label = f"{day.month}/{day.day} {day_names[i]}"
            labels.append(day_label)
            values.append(bins.get(key, 0))

        return {
            "labels": labels,
            "values": values,
            "title": "本周专注时长分布（按天）",
            "xlabel": "日期",
        }

    elif range_key == "month":
        # 按日分布
        now = datetime.now()
        days_in_month = 31
        if now.month in (4, 6, 9, 11):
            days_in_month = 30
        elif now.month == 2:
            # 闰年判断
            y = now.year
            days_in_month = 29 if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0) else 28

        bins = defaultdict(int)
        for r in records:
            dt = _parse_start_time(r)
            if dt:
                bins[dt.day] += r.get("duration_minutes", 0)

        labels = [f"{d}日" for d in range(1, days_in_month + 1)]
        values = [bins.get(d, 0) for d in range(1, days_in_month + 1)]
        return {
            "labels": labels,
            "values": values,
            "title": "本月专注时长分布（按天）",
            "xlabel": "日期",
        }

    return {"labels": [], "values": [], "title": "", "xlabel": ""}


# ── 情绪比例饼图数据 ──────────────────────────────────────

MOOD_LABELS = {
    1: "🤤 已傻",
    2: "🫠 没招了",
    3: "😇 不妙",
    4: "🙂 顺利",
    5: "😃 巅峰",
}

# matplotlib 用纯文字标签（部分中文字体不含 emoji）
MOOD_LABELS_TEXT = {
    1: "已傻",
    2: "没招了",
    3: "不妙",
    4: "顺利",
    5: "巅峰",
}

MOOD_COLORS = {
    1: "#B0BEC5",  # Blue Grey
    2: "#81C784",  # Green
    3: "#64B5F6",  # Blue
    4: "#FFB74D",  # Orange
    5: "#E57373",  # Red
}


def get_mood_pie_data(range_key: str) -> dict:
    """生成情绪比例饼图数据

    参数:
        range_key: "today" / "week" / "month"
    返回:
        {"labels": [...], "values": [...], "colors": [...], "title": str}
        仅包含有记录的情绪值
    """
    records = get_records_by_range(range_key)

    # 仅统计已完成且有情绪值的记录
    mood_counts = defaultdict(int)
    for r in records:
        if r.get("was_completed", False):
            mood = r.get("mood", 0)
            if mood in MOOD_LABELS:
                mood_counts[mood] += 1

    labels = []
    values = []
    colors = []
    for mood in sorted(mood_counts.keys()):
        labels.append(MOOD_LABELS_TEXT[mood])  # 纯文字标签，避免 emoji 字体缺失
        values.append(mood_counts[mood])
        colors.append(MOOD_COLORS[mood])

    return {
        "labels": labels,
        "values": values,
        "colors": colors,
        "title": "情绪分布",
    }


# ── 历史记录列表 ──────────────────────────────────────────

def get_history_records(range_key: str) -> list:
    """获取时间范围内的历史记录，按时间倒序排列

    参数:
        range_key: "today" / "week" / "month"
    返回:
        记录列表（按 start_time 倒序）
    """
    records = get_records_by_range(range_key)
    # 按开始时间倒序
    records.sort(key=lambda r: r.get("start_time", ""), reverse=True)
    return records


# ── 周报数据生成 ──────────────────────────────────────────

def get_weekly_report_data() -> dict:
    """生成本周专注报告数据

    返回:
        {
            "week_start": str,         # 本周一日期
            "week_end": str,           # 本周日日期
            "total_minutes": int,      # 本周总专注分钟数
            "completed_count": int,    # 完成番茄数
            "interrupted_count": int,  # 中断次数
            "mood_pie": dict,          # 情绪饼图数据
            "daily_bar": dict,         # 每日专注柱状图数据
            "streak_days": int,        # 连续专注天数
            "rank": str,               # 段位名称
            "tasks_completed": int,    # 本周完成任务数
            "tasks_total": int,        # 本周任务总数
        }
    """
    from utils.statistics import get_rank

    data = load_data()
    all_records = data.get("tomato_records", [])
    tasks = data.get("tasks", [])
    profile = data.get("user_profile", {})

    # 本周范围
    start, end = get_week_range()
    week_records = filter_records(all_records, start, end)

    # 基础统计
    completed = [r for r in week_records if r.get("was_completed", False)]
    interrupted = [r for r in week_records if not r.get("was_completed", False)]
    total_minutes = sum(r.get("duration_minutes", 0) for r in completed)

    # 情绪分布
    mood_counts = defaultdict(int)
    for r in completed:
        mood = r.get("mood", 0)
        if mood in MOOD_LABELS:
            mood_counts[mood] += 1
    mood_labels = []
    mood_values = []
    mood_colors = []
    for mood in sorted(mood_counts.keys()):
        mood_labels.append(MOOD_LABELS_TEXT[mood])  # 纯文字，避免 emoji 缺失
        mood_values.append(mood_counts[mood])
        mood_colors.append(MOOD_COLORS[mood])

    # 每日柱状图
    weekday = datetime.now().weekday()
    week_start = datetime(datetime.now().year, datetime.now().month, datetime.now().day) - timedelta(days=weekday)
    week_start = datetime(week_start.year, week_start.month, week_start.day)

    daily_bins = defaultdict(int)
    for r in completed:
        dt = _parse_start_time(r)
        if dt:
            day_key = datetime(dt.year, dt.month, dt.day)
            daily_bins[str(day_key.date())] += r.get("duration_minutes", 0)

    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    bar_labels = []
    bar_values = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        key = str(day.date())
        bar_labels.append(f"{day.month}/{day.day} {day_names[i]}")
        bar_values.append(daily_bins.get(key, 0))

    # 任务完成统计（排除已软删除的任务）
    tasks_completed = 0
    tasks_total = 0
    for t in tasks:
        if t.get("is_deleted", False):
            continue
        created = t.get("created_date", "")
        if created:
            try:
                created_dt = datetime.strptime(created, "%Y-%m-%d")
                if created_dt <= end:  # 本周或之前创建的任务
                    tasks_total += 1
                    if t.get("is_finished", False):
                        tasks_completed += 1
            except ValueError:
                pass

    streak = profile.get("streak_days", 0)
    rank = get_rank(streak)

    return {
        "week_start": week_start.strftime("%Y-%m-%d"),
        "week_end": (week_start + timedelta(days=6)).strftime("%Y-%m-%d"),
        "total_minutes": total_minutes,
        "completed_count": len(completed),
        "interrupted_count": len(interrupted),
        "mood_pie": {
            "labels": mood_labels,
            "values": mood_values,
            "colors": mood_colors,
            "title": "本周情绪分布",
        },
        "daily_bar": {
            "labels": bar_labels,
            "values": bar_values,
            "title": "本周每日专注时长",
            "xlabel": "日期",
        },
        "streak_days": streak,
        "rank": rank,
        "tasks_completed": tasks_completed,
        "tasks_total": tasks_total,
    }
