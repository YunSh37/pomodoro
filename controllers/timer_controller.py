"""计时器控制器 — 管理番茄钟计时状态与核心逻辑"""

import time
from datetime import datetime
from enum import Enum, auto

from models.data_manager import (
    load_data, save_data, get_next_id,
)
from models.tomato import TomatoRecord
from views.flow_note_dialog import FlowNoteDialog


class TimerState(Enum):
    """计时器状态枚举"""
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()


DURATION_OPTIONS = {
    "5":  5 * 60,
    "10": 10 * 60,
    "15": 15 * 60,
    "25": 25 * 60,
    "45": 45 * 60,
    "60": 60 * 60,
}


class TimerController:
    """番茄钟计时控制器"""

    TICK_INTERVAL = 50

    def __init__(self, main_window):
        self._window = main_window
        self._state = TimerState.IDLE
        self._total_seconds = DURATION_OPTIONS["25"]
        self._start_time = 0.0
        self._paused_remaining = 0.0
        self._after_id = None
        self._active_duration_key = "25"
        self._session_start_str = ""
        self._active_task_id = 0  # 当前关联任务 ID

    # ── 时长切换 ──────────────────────────────────────────

    def switch_duration(self, duration_key: str):
        if self._state != TimerState.IDLE:
            self._record_interrupt()
        self._cancel_timer()
        self._active_duration_key = duration_key
        self._total_seconds = DURATION_OPTIONS.get(duration_key, 25 * 60)
        self._state = TimerState.IDLE
        self._paused_remaining = self._total_seconds
        self._update_display(self._total_seconds)
        self._set_button_states(TimerState.IDLE)

    # ── 开始 ──────────────────────────────────────────────

    def start(self):
        if self._state == TimerState.RUNNING:
            return
        if self._state == TimerState.PAUSED:
            self.resume()
            return
        # 获取窗口选中的任务 ID
        task_id = self._window.get_selected_task_id()
        if not task_id:
            return  # 窗口侧已弹窗提示，此处直接返回
        self._active_task_id = task_id
        self._state = TimerState.RUNNING
        self._start_time = time.time()
        self._paused_remaining = self._total_seconds
        self._session_start_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._set_button_states(TimerState.RUNNING)
        self._window.update_status("专注中…")
        self._tick()

    # ── 暂停 / 继续 ──────────────────────────────────────

    def pause(self):
        if self._state != TimerState.RUNNING:
            return
        elapsed = time.time() - self._start_time
        self._paused_remaining = max(0, self._total_seconds - elapsed)
        self._state = TimerState.PAUSED
        self._cancel_timer()
        self._set_button_states(TimerState.PAUSED)
        self._window.update_status("已暂停")
        self._update_display(self._paused_remaining)

    def resume(self):
        if self._state != TimerState.PAUSED:
            return
        self._start_time = time.time() - (self._total_seconds - self._paused_remaining)
        self._state = TimerState.RUNNING
        self._set_button_states(TimerState.RUNNING)
        self._window.update_status("专注中…")
        self._tick()

    # ── 放弃（记录中断） ──────────────────────────────────

    def abandon(self):
        """放弃当前计时：始终记录中断番茄（无论是否暂停过）"""
        if self._state == TimerState.IDLE:
            return
        self._record_interrupt()
        self._cancel_timer()
        self._state = TimerState.IDLE
        self._paused_remaining = self._total_seconds
        self._update_display(self._total_seconds)
        self._set_button_states(TimerState.IDLE)
        self._window.update_status("已放弃")

    # ── 重置（不产生任何记录） ────────────────────────────

    def reset(self):
        """重置计时器：停止计时，恢复初始状态，不产生任何记录"""
        if self._state == TimerState.IDLE:
            return
        self._cancel_timer()
        self._state = TimerState.IDLE
        self._session_start_str = ""
        self._active_task_id = 0
        self._paused_remaining = self._total_seconds
        self._update_display(self._total_seconds)
        self._set_button_states(TimerState.IDLE)
        self._window.update_status("准备专注")

    # ── 计时循环 ──────────────────────────────────────────

    def _tick(self):
        if self._state != TimerState.RUNNING:
            return
        elapsed = time.time() - self._start_time
        remaining = self._total_seconds - elapsed
        if remaining <= 0:
            self._finish()
            return
        self._update_display(remaining)
        self._after_id = self._window.after(self.TICK_INTERVAL, self._tick)

    def _finish(self):
        """计时正常结束：保存 → 弹窗 → 更新任务完成数 → 刷新面板"""
        self._cancel_timer()
        self._state = TimerState.IDLE
        self._paused_remaining = 0.0
        self._update_display(0.0)
        self._set_button_states(TimerState.IDLE)
        self._window.update_status("完成！")
        print("\a")

        # 持久化番茄记录
        data = load_data()
        records = data.get("tomato_records", [])
        new_id = get_next_id(records)
        end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration_min = max(1, round(self._total_seconds / 60))
        record = TomatoRecord(
            id=new_id,
            task_id=self._active_task_id,
            start_time=self._session_start_str,
            end_time=end_time_str,
            duration_minutes=duration_min,
            was_completed=True, mood=0, mood_note="",
        )
        records.append(record.to_dict())
        save_data(data)

        # 心流笔记
        dialog = FlowNoteDialog(self._window)
        self._window.wait_window(dialog.top)
        mood, note = dialog.result

        # 重新加载数据（避免 update_task 和其他操作的覆盖问题），
        # 统一更新 mood + note 和任务完成数，一次写盘
        data = load_data()
        recs = data.get("tomato_records", [])
        if recs:
            recs[-1]["mood"] = mood
            recs[-1]["mood_note"] = note

        # 关联任务 completed_pomodoros +1
        if self._active_task_id:
            for t in data.get("tasks", []):
                if t.get("id") == self._active_task_id:
                    t["completed_pomodoros"] = t.get("completed_pomodoros", 0) + 1
                    break

        save_data(data)

        # 刷新状态面板与任务列表
        self._window.update_status_panel()
        self._window.refresh_task_list()
        self._active_task_id = 0

    def _record_interrupt(self):
        """记录中断番茄（放弃/切换时长均会调用）

        修复：不再跳过 elapsed<=0 的情况，只要 _session_start_str 非空即保存，
        确保「开始→放弃」（未经过暂停）也能正确增加心碎记录。
        """
        if not self._session_start_str:
            return
        # 计算实际经过的秒数
        elapsed = self._total_seconds - self._paused_remaining
        # 至少计 1 分钟
        duration_min = max(1, round(max(elapsed, 1) / 60))

        data = load_data()
        records = data.get("tomato_records", [])
        new_id = get_next_id(records)
        end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = TomatoRecord(
            id=new_id,
            task_id=self._active_task_id,
            start_time=self._session_start_str,
            end_time=end_time_str,
            duration_minutes=duration_min,
            was_completed=False, mood=0, mood_note="",
        )
        records.append(record.to_dict())
        save_data(data)
        self._session_start_str = ""
        # 刷新面板与任务列表
        self._window.update_status_panel()
        self._window.refresh_task_list()

    def _cancel_timer(self):
        if self._after_id is not None:
            self._window.after_cancel(self._after_id)
            self._after_id = None

    # ── UI 刷新 ───────────────────────────────────────────

    def _update_display(self, remaining_seconds: float):
        total_sec = int(remaining_seconds)
        minutes, seconds = total_sec // 60, total_sec % 60
        mmss = f"{minutes:02d}:{seconds:02d}"
        frac = remaining_seconds - total_sec
        hundredths = int(frac * 100)
        ms = f".{hundredths:02d}"
        self._window.update_timer_display(mmss, ms)
        if self._total_seconds > 0:
            pct = 1.0 - (remaining_seconds / self._total_seconds)
        else:
            pct = 1.0
        pct = max(0.0, min(1.0, pct))
        self._window.update_progress(pct)

    def _set_button_states(self, state: TimerState):
        if state == TimerState.IDLE:
            self._window.set_button_states(True, False, False, False)
        elif state == TimerState.RUNNING:
            self._window.set_button_states(False, True, True, True)
        elif state == TimerState.PAUSED:
            self._window.set_button_states(True, False, True, True)
