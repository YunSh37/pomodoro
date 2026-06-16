"""任务数据模型"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    """番茄钟任务"""

    id: int
    title: str
    estimated_pomodoros: int = 1
    completed_pomodoros: int = 0
    is_finished: bool = False
    is_deleted: bool = False
    created_date: str = ""

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "estimated_pomodoros": self.estimated_pomodoros,
            "completed_pomodoros": self.completed_pomodoros,
            "is_finished": self.is_finished,
            "is_deleted": self.is_deleted,
            "created_date": self.created_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """从字典创建实例"""
        return cls(
            id=data["id"],
            title=data["title"],
            estimated_pomodoros=data.get("estimated_pomodoros", 1),
            completed_pomodoros=data.get("completed_pomodoros", 0),
            is_finished=data.get("is_finished", False),
            is_deleted=data.get("is_deleted", False),
            created_date=data.get("created_date", ""),
        )
