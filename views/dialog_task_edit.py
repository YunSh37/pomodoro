"""任务编辑弹窗 — 修改任务标题和预计番茄数"""

import tkinter as tk
from tkinter import ttk

from views.main_window import CLR


class TaskEditDialog:
    """任务编辑模态弹窗

    用法:
        dialog = TaskEditDialog(parent, title="标题", estimated=3)
        parent.wait_window(dialog.top)
        if dialog.result:
            title, estimated = dialog.result
    """

    def __init__(self, parent, title: str = "", estimated: int = 1):
        self._parent = parent
        self.result = None  # (title, estimated) 或 None（取消）

        # ── 模态顶层窗口 ──
        self.top = tk.Toplevel(parent)
        self.top.title("编辑任务")
        self.top.geometry("300x180")
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        self._build_ui(title, estimated)
        self._apply_theme()

        # 居中
        self.top.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        dw, dh = 300, 180
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self.top.geometry(f"+{x}+{y}")

        self.top.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _build_ui(self, title: str, estimated: int):
        c = CLR
        self._frame = tk.Frame(self.top, bg=c["bg"], padx=16, pady=12)
        self._frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        tk.Label(
            self._frame, text="编辑任务", font=("微软雅黑", 11, "bold"),
            bg=c["bg"], fg=c["text"],
        ).pack(anchor=tk.W, pady=(0, 10))

        # 任务标题
        tk.Label(
            self._frame, text="任务标题", font=("微软雅黑", 9),
            bg=c["bg"], fg=c["text_soft"],
        ).pack(anchor=tk.W)
        self._title_var = tk.StringVar(value=title)
        self._title_entry = tk.Entry(
            self._frame, textvariable=self._title_var,
            font=("微软雅黑", 10), bg=c["surface"], fg=c["text"],
            relief=tk.SOLID, bd=1,
        )
        self._title_entry.pack(fill=tk.X, pady=(2, 8))
        self._title_entry.focus_set()

        # 预计番茄数
        tk.Label(
            self._frame, text="预计番茄数", font=("微软雅黑", 9),
            bg=c["bg"], fg=c["text_soft"],
        ).pack(anchor=tk.W)
        self._est_var = tk.StringVar(value=str(estimated))
        self._est_spin = tk.Spinbox(
            self._frame, textvariable=self._est_var, from_=1, to=99,
            font=("微软雅黑", 10), bg=c["surface"], fg=c["text"],
            relief=tk.SOLID, bd=1, width=6, justify=tk.CENTER,
        )
        self._est_spin.pack(anchor=tk.W, pady=(2, 12))

        # 按钮行
        btn_frame = tk.Frame(self._frame, bg=c["bg"])
        btn_frame.pack(fill=tk.X)
        tk.Button(
            btn_frame, text="取消", font=("微软雅黑", 9),
            bg=c["toggle_bg"], fg=c["toggle_fg"], relief=tk.FLAT,
            padx=12, pady=4, command=self._on_cancel,
        ).pack(side=tk.RIGHT, padx=(6, 0))
        tk.Button(
            btn_frame, text="保存", font=("微软雅黑", 9, "bold"),
            bg=c["primary"], fg=c["text_inverse"], relief=tk.FLAT,
            padx=12, pady=4, command=self._on_save,
        ).pack(side=tk.RIGHT)

    def _on_save(self):
        title = self._title_var.get().strip()
        if not title:
            return
        try:
            est = int(self._est_var.get())
            if est < 1:
                est = 1
        except ValueError:
            est = 1
        self.result = (title, est)
        self.top.destroy()

    def _on_cancel(self):
        self.result = None
        self.top.destroy()

    def _apply_theme(self):
        c = CLR
        self._frame.configure(bg=c["bg"])
        self._title_entry.configure(bg=c["surface"], fg=c["text"])
        self._est_spin.configure(bg=c["surface"], fg=c["text"])
