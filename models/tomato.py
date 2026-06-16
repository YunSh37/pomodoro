"""番茄记录数据模型"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TomatoRecord:
    """单次番茄钟记录"""

    id: int
    task_id: int
    start_time: str = ""
    end_time: str = ""
    duration_minutes: int = 0
    was_completed: bool = False
    mood: int = 3
    mood_note: str = ""

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_minutes": self.duration_minutes,
            "was_completed": self.was_completed,
            "mood": self.mood,
            "mood_note": self.mood_note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TomatoRecord":
        """从字典创建实例"""
        return cls(
            id=data["id"],
            task_id=data["task_id"],
            start_time=data.get("start_time", ""),
            end_time=data.get("end_time", ""),
            duration_minutes=data.get("duration_minutes", 0),
            was_completed=data.get("was_completed", False),
            mood=data.get("mood", 3),
            mood_note=data.get("mood_note", ""),
        )
