"""心流笔记弹窗 — 番茄完成后收集心情与备注"""

import tkinter as tk
from tkinter import ttk

# 复用主窗口的配色系统
from views.main_window import CLR


# 心情选项：(emoji, 分值, 标签)
MOODS = [
    ("😃", 5, "很棒"),
    ("🙂", 4, "不错"),
    ("😇", 3, "还行"),
    ("🫠", 2, "疲惫"),
    ("🤤", 1, "累趴"),
]


class FlowNoteDialog:
    """心流笔记模态弹窗

    用法:
        dialog = FlowNoteDialog(parent)
        parent.wait_window(dialog.top)
        mood, note = dialog.result
    """

    def __init__(self, parent):
        """创建弹窗界面

        参数:
            parent: 父窗口（MainWindow 实例）
        """
        self._parent = parent
        self._mood = 0       # 选中的心情分值（0 表示未选）
        self._note = ""      # 备注内容
        self.result = (0, "")  # 最终返回结果

        # ── 模态顶层窗口 ──
        self.top = tk.Toplevel(parent)
        self.top.title("心流笔记")
        self.top.geometry("320x240")
        self.top.resizable(False, False)
        self.top.transient(parent)  # 置顶于父窗口
        self.top.grab_set()          # 模态：阻断父窗口交互

        self._build_ui()
        self._apply_theme()

        # 居中于父窗口
        self.top.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        dw, dh = 320, 240
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self.top.geometry(f"+{x}+{y}")

        # 关闭窗口时的处理
        self.top.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── 界面构建 ──────────────────────────────────────────

    def _build_ui(self):
        """构建弹窗内部控件"""
        c = CLR
        self._frame = tk.Frame(self.top, bg=c["bg"], padx=16, pady=12)
        self._frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        tk.Label(
            self._frame, text="番茄完成！感觉如何？",
            font=("微软雅黑", 11, "bold"),
            bg=c["bg"], fg=c["text"],
        ).pack(pady=(0, 10))

        # 心情 emoji 行
        mood_frame = tk.Frame(self._frame, bg=c["bg"])
        mood_frame.pack(pady=(0, 8))

        self._mood_btns = {}  # {分值: tk.Button}
        for emoji, value, label in MOODS:
            btn = tk.Button(
                mood_frame, text=f"{emoji}\n{label}",
                font=("微软雅黑", 9),
                bg=c["surface"], fg=c["text"],
                relief=tk.FLAT, bd=1,
                padx=6, pady=4,
                command=lambda v=value: self._on_mood_select(v),
            )
            btn.pack(side=tk.LEFT, padx=3)
            self._mood_btns[value] = btn

        # 备注输入框
        tk.Label(
            self._frame, text="可选备注（不超过 50 字）",
            font=("微软雅黑", 8),
            bg=c["bg"], fg=c["text_soft"],
        ).pack(anchor=tk.W, pady=(4, 2))

        self._entry_var = tk.StringVar()
        # 限制输入 50 字符
        self._entry_var.trace_add("write", self._limit_entry)
        self._entry = tk.Entry(
            self._frame,
            textvariable=self._entry_var,
            font=("微软雅黑", 10),
            bg=c["surface"], fg=c["text"],
            relief=tk.SOLID, bd=1,
        )
        self._entry.pack(fill=tk.X, pady=(0, 12))

        # 确认按钮
        self._confirm_btn = tk.Button(
            self._frame, text="确认 ✓",
            font=("微软雅黑", 10, "bold"),
            bg=c["primary"], fg=c["text_inverse"],
            relief=tk.FLAT, padx=20, pady=4,
            command=self._on_confirm,
        )
        self._confirm_btn.pack()

    # ── 回调 ──────────────────────────────────────────────

    def _on_mood_select(self, value: int):
        """心情按钮点击：高亮选中，取消其他

        参数:
            value: 心情分值 1~5
        """
        c = CLR
        self._mood = value
        for v, btn in self._mood_btns.items():
            if v == value:
                btn.configure(
                    bg=c["primary"], fg=c["text_inverse"],
                    relief=tk.SUNKEN,
                )
            else:
                btn.configure(
                    bg=c["surface"], fg=c["text"],
                    relief=tk.FLAT,
                )

    def _limit_entry(self, *_):
        """限制备注输入不超过 50 字符"""
        text = self._entry_var.get()
        if len(text) > 50:
            self._entry_var.set(text[:50])

    def _on_confirm(self):
        """确认按钮：保存结果并关闭"""
        self._note = self._entry_var.get().strip()
        # 心情必选，若未选默认 3（还行）
        if self._mood == 0:
            self._mood = 3
        self.result = (self._mood, self._note)
        self.top.destroy()

    def _on_close(self):
        """关闭窗口（点 X）：使用默认值"""
        if self._mood == 0:
            self._mood = 3
        self._note = self._entry_var.get().strip()
        self.result = (self._mood, self._note)
        self.top.destroy()

    # ── 主题适配 ──────────────────────────────────────────

    def _apply_theme(self):
        """根据当前 CLR 刷新弹窗配色"""
        c = CLR
        self._frame.configure(bg=c["bg"])
        # 更新子控件
        for child in self._frame.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=c["bg"])
        self._entry.configure(bg=c["surface"], fg=c["text"])
        self._confirm_btn.configure(bg=c["primary"], fg=c["text_inverse"])
        # 心情按钮
        for v, btn in self._mood_btns.items():
            if v == self._mood:
                btn.configure(bg=c["primary"], fg=c["text_inverse"])
            else:
                btn.configure(bg=c["surface"], fg=c["text"])
