"""数据持久化管理 — 加载、保存与查询"""

import json
import os
from datetime import datetime, timedelta

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.json")

DEFAULT_DATA = {
    "tasks": [],
    "tomato_records": [],
    "user_settings": {
        "focus_duration": 25,
        "short_break": 5,
        "long_break": 15,
        "long_break_interval": 4,
        "daily_reset_hour": 4,
        "theme_preference": "auto",   # auto / dark / light
    },
    "user_profile": {
        "daily_focus_goal": 100,      # 每日目标专注分钟数（旧，保留兼容）
        "daily_tomato_goal": 10,      # 每日目标番茄个数
        "streak_days": 0,              # 连续专注天数
        "last_active_date": "",        # 最后活跃日期 YYYY-MM-DD
        "last_focus_easter_date": "",  # 专注彩蛋最后触发日期
        "last_heart_easter_date": "",  # 心碎彩蛋最后触发日期
    },
}


def load_data() -> dict:
    """加载数据文件，首次运行返回默认结构并自动创建文件

    自动迁移：若旧数据缺少 user_profile 字段则补全；
    若 user_profile 缺少 daily_tomato_goal 则补全。
    """
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 自动迁移：补全缺失字段
    if "user_profile" not in data:
        data["user_profile"] = dict(DEFAULT_DATA["user_profile"])
        save_data(data)
    elif "daily_tomato_goal" not in data["user_profile"]:
        data["user_profile"]["daily_tomato_goal"] = DEFAULT_DATA["user_profile"]["daily_tomato_goal"]
        save_data(data)
    # 自动迁移：补充 theme_preference
    if "theme_preference" not in data.get("user_settings", {}):
        data.setdefault("user_settings", {})["theme_preference"] = "auto"
        save_data(data)
    # 自动迁移：补全彩蛋触发日期
    profile = data.get("user_profile", {})
    for key in ("last_focus_easter_date", "last_heart_easter_date"):
        if key not in profile:
            profile[key] = ""
            save_data(data)
    return data


def save_data(data: dict) -> None:
    """保存数据到 JSON 文件"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_next_id(records: list) -> int:
    """返回记录列表中的下一个可用 ID（自增）

    参数:
        records: TomatoRecord 或 Task 的字典列表
    返回:
        最大 id + 1，若列表为空则返回 1
    """
    if not records:
        return 1
    return max(r.get("id", 0) for r in records) + 1


def get_profile() -> dict:
    """获取 user_profile，不含写盘"""
    data = load_data()
    return data.get("user_profile", dict(DEFAULT_DATA["user_profile"]))


def update_profile(profile: dict) -> None:
    """更新 user_profile 并保存

    参数:
        profile: 新的 user_profile 字典
    """
    data = load_data()
    data["user_profile"] = profile
    save_data(data)


def get_today_records() -> list:
    """获取今日的番茄记录列表

    根据 user_settings 中的 daily_reset_hour 判定「今天」的起点。
    例如 reset_hour=4 表示凌晨 4 点前算作前一天。

    返回:
        今日的 TomatoRecord 字典列表
    """
    data = load_data()
    all_records = data.get("tomato_records", [])
    settings = data.get("user_settings", {})
    reset_hour = settings.get("daily_reset_hour", 4)

    # 计算今天的起始时间
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day, reset_hour)
    if now.hour < reset_hour:
        today_start = today_start - timedelta(days=1)

    today_records = []
    for r in all_records:
        start_str = r.get("start_time", "")
        if not start_str:
            continue
        try:
            start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        if start_dt >= today_start:
            today_records.append(r)

    return today_records


def load_tasks() -> list:
    """加载任务列表（排除已软删除的任务）"""
    data = load_data()
    tasks = data.get("tasks", [])
    # 自动迁移：补全 is_deleted 字段
    migrated = False
    for t in tasks:
        if "is_deleted" not in t:
            t["is_deleted"] = False
            migrated = True
    if migrated:
        save_data(data)
    return [t for t in tasks if not t.get("is_deleted", False)]


def get_all_tasks() -> list:
    """加载全部任务列表（含已删除的，供统计视图查询任务名）"""
    data = load_data()
    tasks = data.get("tasks", [])
    # 自动迁移：补全 is_deleted 字段
    migrated = False
    for t in tasks:
        if "is_deleted" not in t:
            t["is_deleted"] = False
            migrated = True
    if migrated:
        save_data(data)
    return tasks


def save_tasks(tasks: list) -> None:
    """保存任务列表并写盘"""
    data = load_data()
    data["tasks"] = tasks
    save_data(data)


def add_task(task_dict: dict) -> list:
    """添加一个任务并返回更新后的任务列表"""
    data = load_data()
    tasks = data.get("tasks", [])
    tasks.append(task_dict)
    save_data(data)
    return tasks


def update_task(task_id: int, updates: dict) -> None:
    """更新指定任务的字段

    参数:
        task_id: 任务 ID
        updates: 要更新的字段字典
    """
    data = load_data()
    for t in data.get("tasks", []):
        if t.get("id") == task_id:
            t.update(updates)
            break
    save_data(data)


def delete_task(task_id: int) -> None:
    """软删除指定任务（标记 is_deleted，保留历史查询）

    参数:
        task_id: 任务 ID
    """
    data = load_data()
    for t in data.get("tasks", []):
        if t.get("id") == task_id:
            t["is_deleted"] = True
            break
    save_data(data)


def restore_task(task_id: int) -> None:
    """恢复已软删除的任务（撤销删除）

    参数:
        task_id: 任务 ID
    """
    data = load_data()
    for t in data.get("tasks", []):
        if t.get("id") == task_id:
            t["is_deleted"] = False
            break
    save_data(data)


def hard_delete_task(task_id: int) -> None:
    """永久删除任务及其所有关联番茄记录

    参数:
        task_id: 任务 ID
    """
    data = load_data()
    # 移除任务
    data["tasks"] = [t for t in data.get("tasks", []) if t.get("id") != task_id]
    # 移除关联的番茄记录
    data["tomato_records"] = [
        r for r in data.get("tomato_records", [])
        if r.get("task_id") != task_id
    ]
    save_data(data)


def get_task_by_id(task_id: int) -> dict | None:
    """根据 ID 获取任务字典（含已删除的，供历史记录查询）

    参数:
        task_id: 任务 ID
    返回:
        任务字典，未找到返回 None
    """
    data = load_data()
    for t in data.get("tasks", []):
        if t.get("id") == task_id:
            return t
    return None


def get_theme_preference() -> str:
    """获取主题偏好设置

    返回:
        "auto" / "dark" / "light"
    """
    data = load_data()
    return data.get("user_settings", {}).get("theme_preference", "auto")


def set_theme_preference(pref: str) -> None:
    """保存主题偏好设置

    参数:
        pref: "auto" / "dark" / "light"
    """
    data = load_data()
    data.setdefault("user_settings", {})["theme_preference"] = pref
    save_data(data)
