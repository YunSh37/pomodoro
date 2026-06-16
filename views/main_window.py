"""主窗口视图 — 番茄钟专注界面"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date

# 数据与统计
from models.data_manager import (
    get_today_records, get_profile, update_profile,
    load_tasks, save_tasks, add_task, update_task, delete_task,
    restore_task, hard_delete_task,
    get_next_id, get_all_tasks,
    get_theme_preference, set_theme_preference,
)
from utils.statistics import (
    calc_fruits, calc_broken_hearts, get_rank, get_zen_quote,
    daily_settlement, get_today_key,
)
from utils.advice_text import get_advice_text, should_show_advice
from views.stats_view import StatsView
from views.easter_egg import EasterEgg


# ═══════════════════════════════════════════════════════════
#  浅色配色 — 柔和粉紫色系
# ═══════════════════════════════════════════════════════════
LIGHT = {
    "bg":            "#F9F4F7",
    "surface":       "#FFFFFF",
    "primary":       "#C07A90",
    "primary_hover": "#AE6880",
    "secondary":     "#8AAA90",
    "accent":        "#E0B894",
    "text":          "#4A3845",
    "text_soft":     "#9A8895",
    "text_inverse":  "#FEF9FB",
    "danger":        "#CF7A72",
    "ring_bg":       "#EDE1E7",
    "ring_active":   "#C07A90",
    "forest_bg":     "#ECF0E8",
    "divider":       "#ECE0E6",
    "toggle_bg":     "#ECE0E6",
    "toggle_fg":     "#4A3845",
    "dur_active_bg": "#C07A90",
    "dur_active_fg": "#FEF9FB",
    "dur_idle_bg":   "#F0EAEE",
    "dur_idle_fg":   "#9A8895",
    "dur_hover_bg":  "#EDE1E7",
    "popup_border":  "#D5C8D0",
    # 状态面板专用色
    "panel_bg":      "#FFFFFF",
    "fruit_bg":      "#FAF8F5",
    "progress_trough": "#EDE1E7",
    "progress_bar":  "#C07A90",
    "rank_gold":     "#D4A843",
    # 重置按钮专用色
    "reset_bg":      "#F0EAEE",
    "reset_fg":      "#9A8895",
    "reset_hover":   "#E0D4DD",
    # 建议条专用色
    "advice_bg":     "#FFF8E1",
    "advice_fg":     "#8D6E00",
    "advice_border": "#FFE082",
    # 任务筛选色
    "filter_active_bg": "#C07A90",
    "filter_active_fg": "#FEF9FB",
    "filter_idle_bg":   "#F0EAEE",
    "filter_idle_fg":   "#9A8895",
    # 橙色提示（任务超预估）
    "orange":        "#E67E22",
}
"""浅色模式"""


# ═══════════════════════════════════════════════════════════
#  深色配色 — 灰蓝色系
# ═══════════════════════════════════════════════════════════
DARK = {
    "bg":            "#1B1F26",
    "surface":       "#242933",
    "primary":       "#7D9FC0",
    "primary_hover": "#8FB2D0",
    "secondary":     "#7BA382",
    "accent":        "#C0A078",
    "text":          "#D7DEE7",
    "text_soft":     "#8A939E",
    "text_inverse":  "#1B1F26",
    "danger":        "#C0706A",
    "ring_bg":       "#313843",
    "ring_active":   "#7D9FC0",
    "forest_bg":     "#28302B",
    "divider":       "#313843",
    "toggle_bg":     "#313843",
    "toggle_fg":     "#D7DEE7",
    "dur_active_bg": "#7D9FC0",
    "dur_active_fg": "#1B1F26",
    "dur_idle_bg":   "#2C323D",
    "dur_idle_fg":   "#8A939E",
    "dur_hover_bg":  "#353C48",
    "popup_border":  "#3D4552",
    # 状态面板专用色
    "panel_bg":      "#242933",
    "fruit_bg":      "#2C3239",
    "progress_trough": "#313843",
    "progress_bar":  "#7D9FC0",
    "rank_gold":     "#C0A060",
    # 重置按钮专用色
    "reset_bg":      "#313843",
    "reset_fg":      "#8A939E",
    "reset_hover":   "#3D4552",
    # 建议条专用色
    "advice_bg":     "#3D3520",
    "advice_fg":     "#D4A843",
    "advice_border": "#5A4A2A",
    # 任务筛选色
    "filter_active_bg": "#7D9FC0",
    "filter_active_fg": "#1B1F26",
    "filter_idle_bg":   "#2C323D",
    "filter_idle_fg":   "#8A939E",
    # 橙色提示（任务超预估）
    "orange":        "#E67E22",
}
"""深色模式"""


# 当前激活配色
CLR = dict(LIGHT)


# 时长选项
DURATION_OPTIONS = [
    ("3秒（测试）",  "3"),
    ("5 分钟",       "5"),
    ("10 分钟",      "10"),
    ("15 分钟",      "15"),
    ("25 分钟",      "25"),
    ("45 分钟",      "45"),
    ("1 小时",       "60"),
]

# 果实颜色常量（不受主题影响，四级：白绿紫红）
FRUIT_COLORS = {
    "white":  "#F5F5F5",
    "green":  "#4CAF50",
    "purple": "#9C27B0",
    "red":    "#F44336",
}
FRUIT_ORDER = ["red", "purple", "green"]


class MainWindow(tk.Tk):
    """番茄钟主窗口"""

    DEFAULT_SIZE = "460x620"
    COMPACT_SIZE = "300x350"

    def __init__(self):
        super().__init__()
        self.title("番茄钟")
        self.geometry(self.DEFAULT_SIZE)
        self.minsize(460, 500)
        # ── 启动时主题判断 ──
        self._dark = self._resolve_initial_theme()
        if self._dark:
            CLR.update(DARK)
        self._compact_mode = False
        self._stats_active = False   # 统计视图是否激活
        self._controller = None
        self._ring_pct = 0.0
        self._timer_text = "25:00"
        self._ms_text = ".00"
        self._duration_key = "25"
        self._dropdown_open = False
        self._goal_var = tk.StringVar()
        self._selected_task_id = None  # 当前选中任务 ID
        self._task_filter = "all"      # 筛选：all / active / finished
        self._tasks = []               # 任务字典列表缓存
        self._listbox_task_map = {}    # listbox index → task dict
        # 彩蛋触发追踪（每日每种仅一次）
        self._prev_focus_red = 0       # 上次果实红色数量
        self._prev_heart_black = 0     # 上次心碎黑色数量
        self._easter_egg_active = False  # 动画播放中

        self.configure(bg=CLR["bg"])

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self._configure_styles()

        self._build_top_bar()
        self._build_hero_section()
        self._build_bottom_section()
        # 统计视图（懒加载）
        self._stats_view = StatsView(self, self)
        # 首次加载：每日结算 + 刷新面板
        self.after(150, self._on_startup)

    # ── 启动结算 ──────────────────────────────────────────

    @staticmethod
    def _resolve_initial_theme() -> bool:
        """启动时根据偏好或系统时间判断是否使用深色模式

        优先级：用户手动偏好 > 系统时间自动判断。
        若偏好为 "dark" 则深色，"light" 则浅色，
        "auto" 则在 18:00~次日 6:00 间深色，其余浅色。

        返回:
            True 表示使用深色模式
        """
        pref = get_theme_preference()
        if pref == "dark":
            return True
        if pref == "light":
            return False
        # "auto"：按系统时间判断
        hour = datetime.now().hour
        return hour >= 18 or hour < 6

    def _on_startup(self):
        """启动时执行每日结算并刷新状态面板、窗口标题"""
        profile = get_profile()
        today_key = get_today_key()
        if profile.get("last_active_date", "") != today_key:
            records = get_today_records()
            completed = sum(
                1 for r in records if r.get("was_completed", False))
            abandoned = sum(
                1 for r in records if not r.get("was_completed", False))
            daily_settlement(profile, completed, abandoned)
            update_profile(profile)
        self._load_and_refresh_tasks()
        self.update_status_panel()

    # ── 控制器绑定 ────────────────────────────────────────

    def set_controller(self, controller):
        self._controller = controller

    def get_selected_task_id(self) -> int | None:
        """返回当前选中任务 ID，供控制器调用"""
        return self._selected_task_id

    # ── ttk 样式 ──────────────────────────────────────────

    def _configure_styles(self):
        c = CLR
        self.style.configure(".", font=("微软雅黑", 10), background=c["bg"])
        self.style.configure("TFrame", background=c["bg"])
        self.style.configure("Card.TFrame", background=c["surface"])
        self.style.configure("Title.TLabel", font=("微软雅黑", 12, "bold"),
                              foreground=c["text"], background=c["surface"])
        self.style.configure("Soft.TLabel", font=("微软雅黑", 9),
                              foreground=c["text_soft"], background=c["bg"])
        self.style.configure("Primary.TButton", font=("微软雅黑", 10, "bold"),
                              background=c["primary"], foreground=c["text_inverse"])
        self.style.map("Primary.TButton",
                        background=[("active", c["primary_hover"]),
                                    ("disabled", c["ring_bg"])])
        self.style.configure("Secondary.TButton", font=("微软雅黑", 9),
                              background=c["secondary"], foreground=c["text_inverse"])
        self.style.configure("Danger.TButton", font=("微软雅黑", 9),
                              background=c["danger"], foreground=c["text_inverse"])
        self.style.configure("Toggle.TButton", font=("微软雅黑", 9),
                              background=c["toggle_bg"], foreground=c["toggle_fg"])
        self.style.map("Toggle.TButton",
                        background=[("active", c["dur_hover_bg"])])
        self.style.configure("TEntry", font=("微软雅黑", 9),
                              fieldbackground=c["surface"], foreground=c["text"])
        self.style.configure("Energy.Horizontal.TProgressbar",
                              troughcolor=c["progress_trough"],
                              background=c["progress_bar"],
                              thickness=14)

    # ── 顶部栏 ────────────────────────────────────────────

    def _build_top_bar(self):
        self._top_bar = ttk.Frame(self)
        self._top_bar.pack(fill=tk.X, padx=16, pady=(12, 0))

        self._logo_label = tk.Label(
            self._top_bar, text="🍅", font=("微软雅黑", 16),
            bg=CLR["bg"], fg=CLR["text"],
        )
        self._logo_label.pack(side=tk.LEFT)

        self.label_status = tk.Label(
            self._top_bar, text="准备专注",
            font=("微软雅黑", 9), bg=CLR["bg"], fg=CLR["text_soft"],
        )
        self.label_status.pack(side=tk.LEFT, padx=8)

        right_group = ttk.Frame(self._top_bar)
        right_group.pack(side=tk.RIGHT)

        action_frame = ttk.Frame(right_group)
        action_frame.pack(side=tk.LEFT, padx=(0, 8))

        self._compact_btn = ttk.Button(
            action_frame, text="⊟", width=3,
            style="Toggle.TButton", command=self._toggle_compact,
        )
        self._compact_btn.pack(side=tk.LEFT, padx=1)

        self._reset_btn = ttk.Button(
            action_frame, text="🔄", width=3,
            style="Toggle.TButton", command=self._reset_layout,
        )
        self._reset_btn.pack(side=tk.LEFT, padx=1)

        self._stats_btn = ttk.Button(
            action_frame, text="统计", width=4,
            style="Toggle.TButton", command=self._show_stats_view,
        )
        self._stats_btn.pack(side=tk.LEFT, padx=1)

        self._pomo_icon = tk.Label(
            right_group, text="🍅", font=("微软雅黑", 12),
            bg=CLR["bg"], fg=CLR["text"],
        )
        self._pomo_icon.pack(side=tk.LEFT)
        self.label_pomo_count = tk.Label(
            right_group, text="0", font=("微软雅黑", 14, "bold"),
            bg=CLR["bg"], fg=CLR["primary"],
        )
        self.label_pomo_count.pack(side=tk.LEFT, padx=(2, 10))

        self._toggle_btn = ttk.Button(
            right_group, text="🌙", width=3,
            style="Toggle.TButton", command=self._toggle_theme,
        )
        self._toggle_btn.pack(side=tk.RIGHT)

    # ── 布局控制 ──────────────────────────────────────────

    def _toggle_compact(self):
        if self._stats_active:
            return  # 统计视图激活时不响应折叠
        self._compact_mode = not self._compact_mode
        if self._compact_mode:
            self._bottom_frame.pack_forget()
            self.minsize(280, 300)
            self.geometry(self.COMPACT_SIZE)
            self._compact_btn.configure(text="⊞")
        else:
            self.minsize(460, 500)
            self._bottom_frame.pack(
                fill=tk.BOTH, padx=16, pady=(0, 4),
                after=self._hero_frame,
            )
            self.geometry(self.DEFAULT_SIZE)
            self._compact_btn.configure(text="⊟")

    def _reset_layout(self):
        if self._stats_active:
            return  # 统计视图激活时不响应
        self.minsize(460, 500)
        self.geometry(self.DEFAULT_SIZE)
        if self._compact_mode:
            self._compact_mode = False
            self._bottom_frame.pack(
                fill=tk.BOTH, padx=16, pady=(0, 4),
                after=self._hero_frame,
            )
            self._compact_btn.configure(text="⊟")
        self._update_advice_banner()

    def _show_stats_view(self):
        """切换到统计视图（全屏展开）"""
        self._stats_active = True
        # 保存当前窗口几何信息
        self._pre_stats_geo = self.geometry()
        # 隐藏正常内容
        self._hero_frame.pack_forget()
        self._bottom_frame.pack_forget()
        # 显示统计视图
        self._stats_view.show()
        self._stats_btn.configure(text="返回", command=self.hide_stats_view)
        # 全屏展开
        self.attributes("-fullscreen", True)

    def hide_stats_view(self):
        """从统计视图返回主界面（恢复原始尺寸）"""
        self._stats_active = False
        # 退出全屏
        self.attributes("-fullscreen", False)
        self._stats_view.hide()
        # 恢复正常内容
        self._hero_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        if not self._compact_mode:
            self._bottom_frame.pack(
                fill=tk.BOTH, padx=16, pady=(0, 4),
                after=self._hero_frame,
            )
        self._stats_btn.configure(text="统计", command=self._show_stats_view)
        # 恢复原来的窗口尺寸
        if hasattr(self, "_pre_stats_geo"):
            self.geometry(self._pre_stats_geo)

    # ── 时长下拉选择器 ────────────────────────────────────

    def _build_duration_dropdown(self, parent):
        self._dur_trigger = tk.Label(
            parent, text="25 分钟 ▾",
            font=("微软雅黑", 9),
            bg=CLR["dur_active_bg"], fg=CLR["dur_active_fg"],
            padx=10, pady=3, cursor="hand2", relief=tk.FLAT, bd=0,
        )
        self._dur_trigger.place(relx=0.97, rely=0.04, anchor=tk.NE)
        self._dur_trigger.bind("<Button-1>", lambda e: self._toggle_dropdown())

        self._dur_popup = tk.Frame(parent, bg=CLR["surface"], bd=1, relief=tk.SOLID)
        self._dur_popup.configure(highlightbackground=CLR["popup_border"],
                                   highlightthickness=0)
        self._dur_popup_items = {}
        for label_text, key in DURATION_OPTIONS:
            lbl = tk.Label(
                self._dur_popup, text=label_text,
                font=("微软雅黑", 9), bg=CLR["surface"], fg=CLR["text"],
                padx=14, pady=4, anchor=tk.W, cursor="hand2",
            )
            lbl.pack(fill=tk.X)
            lbl.bind("<Button-1>", lambda e, k=key: self._on_duration_select(k))
            lbl.bind("<Enter>", lambda e, l=lbl: l.configure(bg=CLR["dur_hover_bg"]))
            lbl.bind("<Leave>", lambda e, l=lbl: l.configure(bg=CLR["surface"]))
            self._dur_popup_items[key] = lbl

    def _toggle_dropdown(self):
        if self._dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self):
        x = self._dur_trigger.winfo_x()
        y = self._dur_trigger.winfo_y() + self._dur_trigger.winfo_height()
        self._dur_popup.place(x=x, y=y, anchor=tk.NW)
        self._dur_popup.lift()
        self._dropdown_open = True
        self.after(100, self._bind_click_outside)

    def _close_dropdown(self):
        self._dur_popup.place_forget()
        self._dropdown_open = False
        self._unbind_click_outside()

    def _bind_click_outside(self):
        self._hero_card.bind("<Button-1>", self._on_click_outside, add="+")

    def _unbind_click_outside(self):
        try:
            self._hero_card.unbind("<Button-1>")
        except tk.TclError:
            pass

    def _on_click_outside(self, event):
        if self._dropdown_open:
            self._close_dropdown()

    def _on_duration_select(self, key: str):
        self._duration_key = key
        label_map = {k: t for t, k in DURATION_OPTIONS}
        trigger_text = label_map.get(key, "25 分钟").replace("（测试）", "") + " ▾"
        self._dur_trigger.configure(text=trigger_text)
        self._close_dropdown()
        if self._controller:
            self._controller.switch_duration(key)

    def _refresh_dropdown_style(self):
        c = CLR
        self._dur_trigger.configure(bg=c["dur_active_bg"], fg=c["dur_active_fg"])
        self._dur_popup.configure(bg=c["surface"], highlightbackground=c["popup_border"])
        for lbl in self._dur_popup_items.values():
            lbl.configure(bg=c["surface"], fg=c["text"])
            lbl.unbind("<Enter>"); lbl.unbind("<Leave>")
            lbl.bind("<Enter>", lambda e, l=lbl: l.configure(bg=c["dur_hover_bg"]))
            lbl.bind("<Leave>", lambda e, l=lbl: l.configure(bg=c["surface"]))

    # ── 核心计时区 ────────────────────────────────────────

    def _build_hero_section(self):
        self._hero_frame = ttk.Frame(self)
        self._hero_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        self._hero_card = tk.Canvas(
            self._hero_frame, bg=CLR["surface"],
            highlightthickness=0, bd=0, relief="flat",
        )
        self._hero_card.pack(fill=tk.BOTH, expand=True)

        def _draw_card_bg(w, h):
            c = self._hero_card; r = 16; s = CLR["surface"]
            c.delete("card_bg")
            c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=s, outline="", tags="card_bg")
            c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=s, outline="", tags="card_bg")
            c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=s, outline="", tags="card_bg")
            c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=s, outline="", tags="card_bg")
            c.create_rectangle(r, 0, w-r, h, fill=s, outline="", tags="card_bg")
            c.create_rectangle(0, r, w, h-r, fill=s, outline="", tags="card_bg")

        self._hero_card.bind("<Configure>", lambda e: _draw_card_bg(e.width, e.height))
        self._build_duration_dropdown(self._hero_card)

        self.canvas_ring = tk.Canvas(
            self._hero_card, width=200, height=200,
            bg=CLR["surface"], highlightthickness=0,
        )
        self.canvas_ring.place(relx=0.5, rely=0.44, anchor=tk.CENTER)
        self._draw_ring(self._ring_pct)

        self.timer_text_id = self.canvas_ring.create_text(
            100, 82, text=self._timer_text,
            font=("微软雅黑", 32, "bold"), fill=CLR["text"],
        )
        self.ms_text_id = self.canvas_ring.create_text(
            100, 116, text=self._ms_text,
            font=("微软雅黑", 12), fill=CLR["text_soft"],
        )
        self.timer_label_id = self.canvas_ring.create_text(
            100, 142, text="准备",
            font=("微软雅黑", 10), fill=CLR["text_soft"],
        )

        # ── 当前任务标签 ──
        self._task_info_label = tk.Label(
            self._hero_card, text="📌 未选择任务",
            font=("微软雅黑", 9), bg=CLR["surface"], fg=CLR["text_soft"],
        )
        self._task_info_label.place(relx=0.5, rely=0.78, anchor=tk.CENTER)

        # ── 重置按钮 ──
        self._build_reset_button()

        btn_area = ttk.Frame(self._hero_card)
        btn_area.place(relx=0.5, rely=0.91, anchor=tk.CENTER)
        self.btn_start = ttk.Button(
            btn_area, text="▶  开始", style="Primary.TButton",
            command=self._on_start,
        )
        self.btn_start.pack(side=tk.LEFT, padx=6)
        self.btn_pause = ttk.Button(
            btn_area, text="⏸  暂停", width=8,
            command=self._on_pause, state=tk.DISABLED,
        )
        self.btn_pause.pack(side=tk.LEFT, padx=6)
        self.btn_abandon = ttk.Button(
            btn_area, text="✕  放弃", width=8,
            command=self._on_abandon, state=tk.DISABLED,
        )
        self.btn_abandon.pack(side=tk.LEFT, padx=6)

    # ── 重置按钮 ──────────────────────────────────────────

    def _build_reset_button(self):
        c = self.canvas_ring
        cx, cy, r = 26, 26, 13
        self._reset_circle = c.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=CLR["reset_bg"], outline=CLR["reset_fg"], width=1,
            tags="reset_btn",
        )
        self._reset_icon = c.create_text(
            cx, cy, text="↺", font=("微软雅黑", 12, "bold"),
            fill=CLR["reset_fg"], tags="reset_btn",
        )
        c.tag_bind("reset_btn", "<Button-1>", lambda e: self._on_reset())
        c.tag_bind("reset_btn", "<Enter>", lambda e: c.itemconfigure(
            self._reset_circle, fill=CLR["reset_hover"]))
        c.tag_bind("reset_btn", "<Leave>", lambda e: c.itemconfigure(
            self._reset_circle, fill=CLR["reset_bg"]))

    def _refresh_reset_button_style(self):
        c = self.canvas_ring
        c.itemconfigure(self._reset_circle, fill=CLR["reset_bg"], outline=CLR["reset_fg"])
        c.itemconfigure(self._reset_icon, fill=CLR["reset_fg"])
        c.tag_unbind("reset_btn", "<Enter>")
        c.tag_unbind("reset_btn", "<Leave>")
        c.tag_bind("reset_btn", "<Enter>", lambda e: c.itemconfigure(
            self._reset_circle, fill=CLR["reset_hover"]))
        c.tag_bind("reset_btn", "<Leave>", lambda e: c.itemconfigure(
            self._reset_circle, fill=CLR["reset_bg"]))

    def _on_reset(self):
        if self._controller:
            self._controller.reset()

    def _draw_ring(self, pct: float):
        c = self.canvas_ring
        c.delete("ring")
        cx, cy, r = 100, 100, 72
        sw = 10
        c.create_oval(cx-r, cy-r, cx+r, cy+r,
                      outline=CLR["ring_bg"], width=sw, tags="ring_bg")
        if pct <= 0:
            return
        c.create_arc(cx-r, cy-r, cx+r, cy+r,
                     start=90, extent=-(pct*360),
                     outline=CLR["ring_active"], width=sw,
                     style="arc", tags="ring")

    # ── 底部双栏 ──────────────────────────────────────────

    def _build_bottom_section(self):
        self._bottom_frame = ttk.Frame(self)
        self._bottom_frame.pack(fill=tk.BOTH, padx=16, pady=(0, 4))
        self._bottom_frame.columnconfigure(0, weight=1)
        self._bottom_frame.columnconfigure(1, weight=1)
        self._bottom_frame.rowconfigure(0, weight=1)
        self._build_task_card(self._bottom_frame)
        self._build_status_panel(self._bottom_frame)

    # ── 任务卡片（左侧） ──────────────────────────────────

    def _build_task_card(self, parent):
        self._task_card = tk.Canvas(parent, bg=CLR["surface"], highlightthickness=0, bd=0)
        self._task_card.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        def _draw(rw, rh):
            c = self._task_card; r = 12; s = CLR["surface"]
            c.delete("bg")
            c.create_rectangle(r, 0, rw-r, rh, fill=s, outline="", tags="bg")
            c.create_rectangle(0, r, rw, rh-r, fill=s, outline="", tags="bg")
            c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=s, outline="", tags="bg")
            c.create_arc(rw-2*r, 0, rw, 2*r, start=0, extent=90, fill=s, outline="", tags="bg")
            c.create_arc(0, rh-2*r, 2*r, rh, start=180, extent=90, fill=s, outline="", tags="bg")
            c.create_arc(rw-2*r, rh-2*r, rw, rh, start=270, extent=90, fill=s, outline="", tags="bg")
        self._task_card.bind("<Configure>", lambda e: _draw(e.width, e.height))

        self._task_inner = ttk.Frame(self._task_card)
        self._task_inner.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._task_inner.configure(style="Card.TFrame")

        # 标题行
        self._task_title_frame = tk.Frame(self._task_inner, bg=CLR["surface"])
        self._task_title_frame.pack(fill=tk.X, padx=10, pady=(10, 4))
        self._task_title = tk.Label(
            self._task_title_frame, text="📋  任务列表",
            font=("微软雅黑", 12, "bold"), bg=CLR["surface"], fg=CLR["text"],
        )
        self._task_title.pack(side=tk.LEFT)

        # ── 筛选按钮 ──
        self._task_filter_frame = tk.Frame(self._task_inner, bg=CLR["surface"])
        self._task_filter_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        self._filter_btns = {}
        for value, label in [("all", "全部"), ("active", "进行中"),
                              ("finished", "已完成"), ("deleted", "已删除")]:
            btn = tk.Label(
                self._task_filter_frame, text=label, font=("微软雅黑", 8),
                bg=CLR["filter_active_bg"] if value == "all" else CLR["filter_idle_bg"],
                fg=CLR["filter_active_fg"] if value == "all" else CLR["filter_idle_fg"],
                padx=8, pady=1, cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=1)
            btn.bind("<Button-1>", lambda e, v=value: self._on_filter_change(v))
            self._filter_btns[value] = btn

        # 任务列表
        self.listbox_tasks = tk.Listbox(
            self._task_inner, height=8,
            bg=CLR["surface"], fg=CLR["text"],
            selectbackground=CLR["primary"], selectforeground=CLR["text_inverse"],
            font=("微软雅黑", 9), bd=0, exportselection=False,
            highlightthickness=1, highlightbackground=CLR["surface"],
            highlightcolor=CLR["surface"], activestyle="none",
        )
        self.listbox_tasks.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.listbox_tasks.bind("<<ListboxSelect>>", self._on_task_select)
        self.listbox_tasks.bind("<Double-1>", self._on_task_double_click)
        # 右键菜单 (Windows: Button-3, macOS: Button-2)
        self.listbox_tasks.bind("<Button-3>", self._on_task_right_click)
        self.listbox_tasks.bind("<Button-2>", self._on_task_right_click)

        # 输入区
        self._task_entry_frame = tk.Frame(self._task_inner, bg=CLR["surface"])
        self._task_entry_frame.pack(fill=tk.X, padx=8, pady=(4, 10))
        self.entry_task = tk.Entry(
            self._task_entry_frame,
            font=("微软雅黑", 9), bg=CLR["surface"], fg=CLR["text"],
            insertbackground=CLR["text"],
            relief=tk.SOLID, bd=1,
        )
        self.entry_task.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.entry_task.bind("<Return>", lambda e: self._on_add_task())
        self.btn_add_task = tk.Button(
            self._task_entry_frame, text="＋", width=3,
            font=("微软雅黑", 10, "bold"),
            bg=CLR["primary"], fg=CLR["text_inverse"],
            relief=tk.FLAT, bd=0, padx=4, pady=2,
            command=self._on_add_task,
            cursor="hand2",
        )
        self.btn_add_task.pack(side=tk.RIGHT)

        # 空状态引导
        self._task_empty_label = tk.Label(
            self._task_inner, text="添加第一个任务，开始专注吧",
            font=("微软雅黑", 9), bg=CLR["surface"], fg=CLR["text_soft"],
        )

    # ── 任务数据操作 ──────────────────────────────────────

    def _load_and_refresh_tasks(self):
        """从 data.json 加载任务并刷新列表"""
        self._tasks = load_tasks()
        self.refresh_task_list()

    def refresh_task_list(self):
        """刷新任务列表显示（根据筛选加载对应任务）"""
        self.listbox_tasks.delete(0, tk.END)
        self._listbox_task_map = {}  # 重建映射，避免残留旧条目

        # 已删除筛选：加载全部任务（含软删除）
        if self._task_filter == "deleted":
            all_tasks = get_all_tasks()
            self._tasks = [t for t in all_tasks if not t.get("is_deleted", False)]
            filtered = [t for t in all_tasks if t.get("is_deleted", False)]
        else:
            self._tasks = load_tasks()  # 重新加载（不含已删除）
            filtered = self._tasks
            if self._task_filter == "active":
                filtered = [t for t in self._tasks if not t.get("is_finished", False)]
            elif self._task_filter == "finished":
                filtered = [t for t in self._tasks if t.get("is_finished", False)]

        if not filtered:
            self._task_empty_label.place(relx=0.5, rely=0.55, anchor=tk.CENTER)
        else:
            self._task_empty_label.place_forget()

        for idx, task in enumerate(filtered):
            display = self._format_task_display(task)
            self.listbox_tasks.insert(tk.END, display)
            self._listbox_task_map[idx] = task

            # 颜色标记
            if task.get("is_deleted", False):
                self.listbox_tasks.itemconfigure(idx, fg=CLR["danger"])
            elif task.get("is_finished", False):
                self.listbox_tasks.itemconfigure(idx, fg=CLR["text_soft"])
            elif (task.get("completed_pomodoros", 0) >= task.get("estimated_pomodoros", 1)
                  and task.get("estimated_pomodoros", 0) > 0):
                self.listbox_tasks.itemconfigure(idx, fg=CLR["orange"])
            else:
                self.listbox_tasks.itemconfigure(idx, fg=CLR["text"])

        # 保留选中状态
        if self._selected_task_id:
            self._highlight_selected_task()

        # 更新当前任务标签
        self._update_task_info_label()

        # 检查建议条
        self._update_advice_banner()

    def _format_task_display(self, task: dict) -> str:
        """格式化任务列表项显示文本"""
        title = task.get("title", "")
        est = task.get("estimated_pomodoros", 0) or 0
        done = task.get("completed_pomodoros", 0)
        finished = task.get("is_finished", False)
        deleted = task.get("is_deleted", False)
        progress = f"[{done}/{est}]" if est > 0 else f"[{done}/-]"
        if deleted:
            return f"✕  {title}  {progress}"
        if finished:
            return f"✓  {title}  {progress}"
        elif est > 0 and done >= est:
            return f"⚠  {title}  {progress}"
        else:
            return f"    {title}  {progress}"

    def _highlight_selected_task(self):
        """在列表中高亮当前选中任务"""
        for idx in self._listbox_task_map:
            task = self._listbox_task_map[idx]
            if task.get("id") == self._selected_task_id:
                self.listbox_tasks.selection_clear(0, tk.END)
                self.listbox_tasks.selection_set(idx)
                self.listbox_tasks.activate(idx)
                return

    def _update_task_info_label(self):
        """更新计时区当前任务标签"""
        if not self._selected_task_id:
            self._task_info_label.configure(text="📌 未选择任务", fg=CLR["text_soft"])
            return
        for t in self._tasks:
            if t.get("id") == self._selected_task_id:
                title = t.get("title", "")
                est = t.get("estimated_pomodoros", 0) or 0
                done = t.get("completed_pomodoros", 0)
                info = f"📌 {title}"
                if est > 0:
                    info += f"  [{done}/{est}]"
                self._task_info_label.configure(text=info, fg=CLR["primary"])
                return
        self._task_info_label.configure(text="📌 未选择任务", fg=CLR["text_soft"])

    # ── 任务事件处理 ──────────────────────────────────────

    def _on_task_select(self, event):
        """列表项选中（已删除任务不可选为计时目标，但仍可查看）"""
        sel = self.listbox_tasks.curselection()
        if not sel:
            self._selected_task_id = None
        else:
            task = self._listbox_task_map.get(sel[0])
            if task and not task.get("is_deleted", False):
                self._selected_task_id = task.get("id")
            else:
                self._selected_task_id = None
        self._update_task_info_label()

    def _on_task_double_click(self, event):
        """双击编辑任务（已删除任务双击恢复）"""
        sel = self.listbox_tasks.curselection()
        if not sel:
            return
        task = self._listbox_task_map.get(sel[0])
        if not task:
            return
        if task.get("is_deleted", False):
            self._on_restore_task(task)
        else:
            self._edit_task(task)

    def _on_task_right_click(self, event):
        """右键菜单"""
        idx = self.listbox_tasks.nearest(event.y)
        if idx < 0:
            return
        task = self._listbox_task_map.get(idx)
        if not task:
            return
        # 先选中
        self.listbox_tasks.selection_clear(0, tk.END)
        self.listbox_tasks.selection_set(idx)

        # 弹出菜单（根据是否为已删除任务显示不同选项）
        menu = tk.Menu(self, tearoff=0, bg=CLR["surface"], fg=CLR["text"],
                       activebackground=CLR["primary"],
                       activeforeground=CLR["text_inverse"],
                       font=("微软雅黑", 9))
        is_deleted = task.get("is_deleted", False)
        if is_deleted:
            menu.add_command(label="↩ 恢复", command=lambda: self._on_restore_task(task))
            menu.add_command(label="✕ 永久删除",
                             command=lambda: self._on_hard_delete_task(task))
        else:
            self._selected_task_id = task.get("id")
            self._update_task_info_label()
            is_finished = task.get("is_finished", False)
            menu.add_command(
                label="✓ 标记完成" if not is_finished else "↩ 取消完成",
                command=lambda: self._on_toggle_finish(task),
            )
            menu.add_command(label="✎ 编辑", command=lambda: self._edit_task(task))
            menu.add_separator()
            menu.add_command(label="✕ 删除", command=lambda: self._on_delete_task(task))
            menu.add_command(label="撤销",
                             command=lambda: self._on_hard_delete_task(task))
        menu.tk_popup(event.x_root, event.y_root)

    def _on_add_task(self):
        """添加任务"""
        try:
            title = self.entry_task.get().strip()
        except Exception:
            title = ""
        if not title:
            # 视觉反馈：输入框闪烁警告色
            self.entry_task.configure(bg=CLR["danger"])
            self.entry_task.focus_set()
            self.after(300, lambda: self.entry_task.configure(bg=CLR["surface"]))
            self.bell()  # 系统提示音
            return
        try:
            tasks = load_tasks()
            new_id = get_next_id(tasks)
            task_dict = {
                "id": new_id,
                "title": title,
                "estimated_pomodoros": 1,
                "completed_pomodoros": 0,
                "is_finished": False,
                "is_deleted": False,
                "created_date": date.today().strftime("%Y-%m-%d"),
            }
            add_task(task_dict)
        except Exception:
            return
        self.entry_task.delete(0, tk.END)
        self._tasks = load_tasks()
        self.refresh_task_list()
        # 确保新任务可见：必要时切回"全部"筛选
        if self._task_filter in ("finished", "deleted"):
            self._on_filter_change("all")

    def _edit_task(self, task: dict):
        """弹出编辑对话框"""
        from views.dialog_task_edit import TaskEditDialog
        dialog = TaskEditDialog(
            self,
            title=task.get("title", ""),
            estimated=task.get("estimated_pomodoros", 1),
        )
        self.wait_window(dialog.top)
        if dialog.result is None:
            return
        new_title, new_est = dialog.result
        update_task(task["id"], {
            "title": new_title,
            "estimated_pomodoros": new_est,
        })
        self._tasks = load_tasks()
        self.refresh_task_list()

    def _on_toggle_finish(self, task: dict):
        """切换任务完成状态"""
        new_state = not task.get("is_finished", False)
        update_task(task["id"], {"is_finished": new_state})
        self._tasks = load_tasks()
        self.refresh_task_list()

    def _on_delete_task(self, task: dict):
        """软删除任务（二次确认，可在"已删除"中恢复）"""
        ok = messagebox.askyesno(
            "确认删除",
            f"确定要删除任务「{task.get('title', '')}」吗？\n"
            "可在「已删除」筛选中恢复。",
            parent=self,
        )
        if not ok:
            return
        delete_task(task["id"])
        if self._selected_task_id == task["id"]:
            self._selected_task_id = None
        self._tasks = load_tasks()
        self.refresh_task_list()

    def _on_restore_task(self, task: dict):
        """恢复已删除任务"""
        restore_task(task["id"])
        self._selected_task_id = None
        self.refresh_task_list()

    def _on_hard_delete_task(self, task: dict):
        """永久删除任务及其所有番茄记录（不可恢复）"""
        ok = messagebox.askyesno(
            "永久删除",
            f"确定要永久删除「{task.get('title', '')}」吗？\n\n"
            "此操作将同时删除该任务的所有番茄记录，\n"
            "包括历史数据和统计数据，且不可恢复！",
            parent=self,
        )
        if not ok:
            return
        hard_delete_task(task["id"])
        if self._selected_task_id == task["id"]:
            self._selected_task_id = None
        self._tasks = load_tasks()
        self.refresh_task_list()
        # 刷新统计面板（番茄记录可能被清除）
        self.update_status_panel()

    def _on_filter_change(self, value: str):
        """切换筛选器"""
        self._task_filter = value
        c = CLR
        for v, btn in self._filter_btns.items():
            if v == value:
                btn.configure(bg=c["filter_active_bg"], fg=c["filter_active_fg"])
            else:
                btn.configure(bg=c["filter_idle_bg"], fg=c["filter_idle_fg"])
        self.refresh_task_list()

    # ── 建议提示浮窗 ──────────────────────────────────────

    def _update_advice_banner(self):
        """根据任务状态判断是否弹出建议浮窗（非模态 Toplevel）"""
        # 若已有提示窗则不再重复弹出
        if hasattr(self, "_advice_top") and self._advice_top is not None:
            try:
                if self._advice_top.winfo_exists():
                    return
            except tk.TclError:
                self._advice_top = None

        # 查找第一个触发条件的任务
        triggered_task = None
        for t in self._tasks:
            if should_show_advice(
                t.get("estimated_pomodoros", 0),
                t.get("completed_pomodoros", 0),
                t.get("is_finished", False),
            ):
                triggered_task = t
                break

        if triggered_task is None or self._compact_mode:
            return

        # 获取最近情绪
        try:
            records = get_today_records()
        except Exception:
            records = []
        completed = [r for r in records if r.get("was_completed", False)]
        last_mood = 0
        if completed:
            last_mood = completed[-1].get("mood", 0)

        c = CLR
        text = get_advice_text(last_mood)
        msg = f"💡 {text}\n（{triggered_task['title']}）"

        # 创建非模态浮动提示窗
        top = tk.Toplevel(self)
        top.title("")
        top.resizable(False, False)
        top.overrideredirect(True)  # 无边框
        top.attributes("-topmost", True)
        top.configure(bg=c["advice_bg"])

        # 内边距容器
        inner = tk.Frame(top, bg=c["advice_bg"], padx=14, pady=10)
        inner.pack()

        # 文案
        tk.Label(
            inner, text=msg,
            font=("微软雅黑", 9), bg=c["advice_bg"], fg=c["advice_fg"],
            wraplength=280, justify=tk.LEFT,
        ).pack(side=tk.LEFT)

        # 关闭按钮
        close = tk.Label(
            inner, text="✕", font=("微软雅黑", 10, "bold"),
            bg=c["advice_bg"], fg=c["advice_fg"],
            padx=6, cursor="hand2",
        )
        close.pack(side=tk.RIGHT, anchor=tk.N)
        close.bind("<Button-1>", lambda e: self._dismiss_advice())

        # 定位到主窗口右下角附近
        top.update_idletasks()
        tw = top.winfo_reqwidth()
        th = top.winfo_reqheight()
        px = self.winfo_x() + self.winfo_width() - tw - 20
        py = self.winfo_y() + self.winfo_height() - th - 20
        top.geometry(f"+{px}+{py}")

        # 8 秒后自动消失
        self._advice_top = top
        self._advice_after_id = self.after(8000, self._dismiss_advice)

    def _dismiss_advice(self):
        """关闭建议浮窗"""
        if hasattr(self, "_advice_after_id") and self._advice_after_id is not None:
            self.after_cancel(self._advice_after_id)
            self._advice_after_id = None
        if hasattr(self, "_advice_top") and self._advice_top is not None:
            try:
                self._advice_top.destroy()
            except tk.TclError:
                pass
            self._advice_top = None

    # ── 专注状态面板 ──────────────────────────────────────

    def _build_status_panel(self, parent):
        """构建右下专注状态面板：能量条 + 段位 + 果实 + 心碎"""
        self._status_card = tk.Canvas(parent, bg=CLR["surface"], highlightthickness=0, bd=0)
        self._status_card.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        def _draw(rw, rh):
            c = self._status_card; r = 12; s = CLR["surface"]
            c.delete("bg")
            c.create_rectangle(r, 0, rw-r, rh, fill=s, outline="", tags="bg")
            c.create_rectangle(0, r, rw, rh-r, fill=s, outline="", tags="bg")
            c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=s, outline="", tags="bg")
            c.create_arc(rw-2*r, 0, rw, 2*r, start=0, extent=90, fill=s, outline="", tags="bg")
            c.create_arc(0, rh-2*r, 2*r, rh, start=180, extent=90, fill=s, outline="", tags="bg")
            c.create_arc(rw-2*r, rh-2*r, rw, rh, start=270, extent=90, fill=s, outline="", tags="bg")
        self._status_card.bind("<Configure>", lambda e: _draw(e.width, e.height))

        self._status_inner = ttk.Frame(self._status_card)
        self._status_inner.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._status_inner.configure(style="Card.TFrame")

        # 标题
        self._status_title = tk.Label(
            self._status_inner, text="📊 今日专注状态",
            font=("微软雅黑", 12, "bold"), bg=CLR["surface"], fg=CLR["text"],
        )
        self._status_title.pack(anchor=tk.W, padx=10, pady=(10, 6))

        # ── 1. 能量进度条行 ──
        self._energy_frame = tk.Frame(self._status_inner, bg=CLR["surface"])
        self._energy_frame.pack(fill=tk.X, padx=10, pady=(0, 2))

        self._energy_label = tk.Label(
            self._energy_frame, text="今日 0 / 10 个番茄",
            font=("微软雅黑", 8), bg=CLR["surface"], fg=CLR["text_soft"],
        )
        self._energy_label.pack(side=tk.LEFT)

        self._goal_entry = tk.Entry(
            self._energy_frame,
            textvariable=self._goal_var,
            font=("微软雅黑", 8), width=4,
            bg=CLR["surface"], fg=CLR["text"],
            relief=tk.SOLID, bd=1,
            justify=tk.CENTER,
        )
        self._goal_entry.pack(side=tk.RIGHT, padx=(4, 0))
        self._goal_entry.bind("<Return>", lambda e: self._on_goal_change())
        self._goal_entry.bind("<FocusOut>", lambda e: self._on_goal_change())

        self._energy_bar = ttk.Progressbar(
            self._energy_frame, style="Energy.Horizontal.TProgressbar",
            mode="determinate", maximum=100, value=0,
        )
        self._energy_bar.pack(fill=tk.X, pady=(2, 0), side=tk.BOTTOM)

        # 段位标签
        self._rank_label = tk.Label(
            self._status_inner, text="🏆 青铜专注者 · 连续 0 天",
            font=("微软雅黑", 9), bg=CLR["surface"], fg=CLR["rank_gold"],
        )
        self._rank_label.pack(anchor=tk.W, padx=10, pady=(3, 6))

        # 分割线 1
        self._sep1 = tk.Frame(self._status_inner, height=1, bg=CLR["divider"])
        self._sep1.pack(fill=tk.X, padx=10)

        # ── 2. 果实收集区 ──
        self._fruit_header = tk.Label(
            self._status_inner, text="🍅 专注果实",
            font=("微软雅黑", 9, "bold"), bg=CLR["surface"], fg=CLR["text"],
        )
        self._fruit_header.pack(anchor=tk.W, padx=10, pady=(6, 2))

        self._fruit_canvas = tk.Canvas(
            self._status_inner, height=38,
            bg=CLR["surface"], highlightthickness=0,
        )
        self._fruit_canvas.pack(fill=tk.X, padx=10)

        # ── 3. 心碎收集区 ──
        self._heart_header = tk.Label(
            self._status_inner, text="💔 心碎记录",
            font=("微软雅黑", 9, "bold"), bg=CLR["surface"], fg=CLR["text"],
        )
        self._heart_header.pack(anchor=tk.W, padx=10, pady=(4, 1))

        self._heart_label = tk.Label(
            self._status_inner, text="",
            font=("微软雅黑", 11), bg=CLR["surface"], fg=CLR["text"],
        )
        self._heart_label.pack(anchor=tk.W, padx=10, pady=(0, 4))

        # 分割线 2
        self._sep2 = tk.Frame(self._status_inner, height=1, bg=CLR["divider"])
        self._sep2.pack(fill=tk.X, padx=10)

    # ── 目标番茄数变更 ────────────────────────────────────

    def _on_goal_change(self):
        """用户修改每日目标番茄数"""
        raw = self._goal_var.get().strip()
        try:
            val = int(raw)
            if val < 3:
                val = 3
        except ValueError:
            val = 3
        self._goal_var.set(str(val))
        profile = get_profile()
        profile["daily_tomato_goal"] = val
        update_profile(profile)
        self.update_status_panel()

    # ── 主题切换 ──────────────────────────────────────────

    def _toggle_theme(self):
        self._dark = not self._dark
        new = DARK if self._dark else LIGHT
        CLR.update(new)
        # 保存用户手动偏好（不再自动判断）
        set_theme_preference("dark" if self._dark else "light")
        self._apply_theme()

    def _apply_theme(self):
        c = CLR
        self.configure(bg=c["bg"])
        self._configure_styles()

        # 顶部栏
        self._top_bar.configure(style="TFrame")
        self._logo_label.configure(bg=c["bg"], fg=c["text"])
        self.label_status.configure(bg=c["bg"], fg=c["text_soft"])
        self._pomo_icon.configure(bg=c["bg"], fg=c["text"])
        self.label_pomo_count.configure(bg=c["bg"], fg=c["primary"])
        self._compact_btn.configure(style="Toggle.TButton")
        self._reset_btn.configure(style="Toggle.TButton")
        self._stats_btn.configure(style="Toggle.TButton")
        self._toggle_btn.configure(
            text="☀️" if self._dark else "🌙", style="Toggle.TButton")
        self._refresh_dropdown_style()

        # 环形画布
        self.canvas_ring.configure(bg=c["surface"])
        self.canvas_ring.itemconfig(self.timer_text_id, fill=c["text"])
        self.canvas_ring.itemconfig(self.ms_text_id, fill=c["text_soft"])
        self.canvas_ring.itemconfig(self.timer_label_id, fill=c["text_soft"])
        self._draw_ring(self._ring_pct)

        # 任务信息标签
        self._task_info_label.configure(bg=c["surface"])

        # 重置按钮
        self._refresh_reset_button_style()

        # 卡片重绘
        self._hero_card.configure(bg=c["surface"])
        self._hero_card.event_generate("<Configure>")

        # 任务卡片
        self._task_card.configure(bg=c["surface"])
        self._task_card.event_generate("<Configure>")
        self._task_inner.configure(style="Card.TFrame")
        self._task_title_frame.configure(bg=c["surface"])
        self._task_title.configure(bg=c["surface"], fg=c["text"])
        self._task_filter_frame.configure(bg=c["surface"])
        self._task_entry_frame.configure(bg=c["surface"])
        self._task_empty_label.configure(bg=c["surface"], fg=c["text_soft"])
        self.listbox_tasks.configure(
            bg=c["surface"], fg=c["text"],
            selectbackground=c["primary"], selectforeground=c["text_inverse"],
            highlightbackground=c["surface"], highlightcolor=c["surface"],
        )
        self.entry_task.configure(
            bg=c["surface"], fg=c["text"], insertbackground=c["text"])
        self.btn_add_task.configure(bg=c["primary"], fg=c["text_inverse"])

        # 筛选按钮
        for v, btn in self._filter_btns.items():
            if v == self._task_filter:
                btn.configure(bg=c["filter_active_bg"], fg=c["filter_active_fg"])
            else:
                btn.configure(bg=c["filter_idle_bg"], fg=c["filter_idle_fg"])

        # 状态面板
        self._status_card.configure(bg=c["surface"])
        self._status_card.event_generate("<Configure>")
        self._status_inner.configure(style="Card.TFrame")
        self._status_title.configure(bg=c["surface"], fg=c["text"])
        self._energy_frame.configure(bg=c["surface"])
        self._energy_label.configure(bg=c["surface"], fg=c["text_soft"])
        self._goal_entry.configure(bg=c["surface"], fg=c["text"],
                                    insertbackground=c["text"])
        self._rank_label.configure(bg=c["surface"], fg=c["rank_gold"])
        self._sep1.configure(bg=c["divider"])
        self._fruit_header.configure(bg=c["surface"], fg=c["text"])
        self._fruit_canvas.configure(bg=c["surface"])
        self._heart_header.configure(bg=c["surface"], fg=c["text"])
        self._heart_label.configure(bg=c["surface"], fg=c["text"])
        self._sep2.configure(bg=c["divider"])

        # 刷新
        self.refresh_task_list()
        self.update_status_panel()
        # 统计视图主题适配
        self._stats_view.apply_theme(self._dark)

    # ── 状态面板更新 ──────────────────────────────────────

    def update_status_panel(self):
        """刷新专注状态面板：能量条、段位、果实、心碎，并更新窗口标题箴言"""
        try:
            records = get_today_records()
        except Exception:
            records = []

        # 统计今日数据（仅今日记录）
        completed = [r for r in records if r.get("was_completed", False)]
        abandoned = [r for r in records if not r.get("was_completed", False)]
        completed_count = len(completed)
        abandoned_count = len(abandoned)

        # ── 能量进度条（按今日成功番茄数计算） ──
        profile = get_profile()
        goal = profile.get("daily_tomato_goal", 10)
        self._goal_var.set(str(goal))
        pct = min(100, int(completed_count / goal * 100)) if goal > 0 else 0
        self._energy_bar.configure(value=pct)
        self._energy_label.configure(text=f"今日 {completed_count} / {goal} 个番茄")

        # ── 段位 ──
        streak = profile.get("streak_days", 0)
        rank = get_rank(streak)
        self._rank_label.configure(text=f"🏆 {rank} · 连续 {streak} 天")

        # ── 果实绘制 ──
        self._draw_fruits(self._fruit_canvas, completed_count)

        # ── 心碎 ──
        hearts = calc_broken_hearts(abandoned_count)
        heart_text = ("🖤" * hearts["black"] +
                      "🤡" * hearts["clown"] +
                      "💔" * hearts["broken"])
        if not heart_text:
            heart_text = "暂无"
        self._heart_label.configure(text=heart_text)

        # ── 窗口标题（箴言） ──
        last_mood = 0
        if completed:
            last_mood = completed[-1].get("mood", 0)
        quote = get_zen_quote(last_mood)
        self.title(f"“{quote}”")

        # ── 顶部番茄计数 ──
        self.label_pomo_count.configure(text=str(completed_count))

        # ── 建议条 ──
        self._update_advice_banner()

        # ── 彩蛋触发检查 ──
        self._check_easter_eggs(completed_count, abandoned_count)

    def _check_easter_eggs(self, completed_count: int, abandoned_count: int):
        """检查专注/心碎彩蛋触发条件（每日每种仅一次）"""
        if self._easter_egg_active:
            return  # 动画播放中，跳过

        today = date.today().strftime("%Y-%m-%d")
        profile = get_profile()

        fruits = calc_fruits(completed_count)
        hearts = calc_broken_hearts(abandoned_count)

        current_red = fruits.get("red", 0)
        current_black = hearts.get("black", 0)

        # 专注彩蛋：红色果实满 5 个且计数增长
        if (current_red >= 5 and completed_count > getattr(self, "_prev_completed_count", 0)
                and profile.get("last_focus_easter_date", "") != today):
            self._prev_completed_count = completed_count
            self._prev_focus_red = current_red
            self._launch_easter_egg("focus", "last_focus_easter_date")
            return

        # 心碎彩蛋：黑心满 5 个且中断计数增长
        if (current_black >= 5 and abandoned_count > getattr(self, "_prev_abandoned_count", 0)
                and profile.get("last_heart_easter_date", "") != today):
            self._prev_abandoned_count = abandoned_count
            self._prev_heart_black = current_black
            self._launch_easter_egg("heart", "last_heart_easter_date")
            return

        # 更新追踪值
        self._prev_completed_count = completed_count
        self._prev_abandoned_count = abandoned_count
        self._prev_focus_red = current_red
        self._prev_heart_black = current_black

    def _launch_easter_egg(self, theme_type: str, date_key: str):
        """启动彩蛋动画：禁用按钮 → 播放 → 恢复 → 持久化日期"""
        self._easter_egg_active = True

        # 禁用计时按钮（防止动画期间误操作）
        if hasattr(self, "btn_start"):
            self.btn_start.configure(state=tk.DISABLED)
        if hasattr(self, "btn_pause"):
            self.btn_pause.configure(state=tk.DISABLED)
        if hasattr(self, "btn_abandon"):
            self.btn_abandon.configure(state=tk.DISABLED)

        def on_done():
            """动画完成回调：恢复按钮状态 + 持久化触发日期"""
            self._easter_egg_active = False
            # 恢复按钮（由控制器根据当前状态决定）
            if self._controller:
                self._controller._set_button_states(self._controller._state)
            # 持久化触发日期
            today = date.today().strftime("%Y-%m-%d")
            profile = get_profile()
            profile[date_key] = today
            update_profile(profile)

        EasterEgg(self, theme_type=theme_type, on_done=on_done)

    def _draw_fruits(self, canvas: tk.Canvas, total_fragments: int):
        """在 Canvas 上绘制专注果实收集盘（四级：红→紫→绿）"""
        canvas.delete("all")
        w = canvas.winfo_width()
        if w < 20:
            return

        fruits = calc_fruits(total_fragments)
        cx = 12; cy = 18; dot_r = 6

        for level_name in FRUIT_ORDER:
            count = fruits.get(level_name, 0)
            color = FRUIT_COLORS.get(level_name, "#CCC")
            for _ in range(count):
                if cx > w - 14:
                    break
                canvas.create_oval(
                    cx - dot_r, cy - dot_r,
                    cx + dot_r, cy + dot_r,
                    fill=color, outline=_darken_hex(color, 0.8), width=1,
                )
                cx += dot_r * 2 + 3

        white_count = fruits.get("white", 0)
        progress_r = 5
        cx += 4
        for i in range(5):
            if cx > w - 10:
                break
            filled = i < white_count
            canvas.create_oval(
                cx - progress_r, cy - progress_r,
                cx + progress_r, cy + progress_r,
                fill=FRUIT_COLORS["white"] if filled else "",
                outline=FRUIT_COLORS["white"] if not filled else _darken_hex(FRUIT_COLORS["white"], 0.8),
                width=1,
            )
            cx += progress_r * 2 + 3

        if total_fragments == 0:
            canvas.create_text(
                10, cy, text="暂无果实", anchor=tk.W,
                font=("微软雅黑", 8), fill=CLR["text_soft"],
            )

    # ── 公共 UI 更新接口 ──────────────────────────────────

    def update_timer_display(self, mmss: str, ms: str = ".00"):
        self._timer_text = mmss; self._ms_text = ms
        self.canvas_ring.itemconfig(self.timer_text_id, text=mmss)
        self.canvas_ring.itemconfig(self.ms_text_id, text=ms)

    def update_progress(self, pct: float):
        self._ring_pct = pct
        self._draw_ring(pct)

    def update_status(self, text: str):
        self.label_status.config(text=text)

    def set_button_states(self, start: bool, pause: bool, abandon: bool, reset: bool = False):
        st, ds = tk.NORMAL, tk.DISABLED
        self.btn_start.configure(state=st if start else ds)
        self.btn_pause.configure(state=st if pause else ds)
        self.btn_abandon.configure(state=st if abandon else ds)
        if not reset:
            self.canvas_ring.itemconfigure(self._reset_circle, state=tk.HIDDEN)
            self.canvas_ring.itemconfigure(self._reset_icon, state=tk.HIDDEN)
        else:
            self.canvas_ring.itemconfigure(self._reset_circle, state=tk.NORMAL)
            self.canvas_ring.itemconfigure(self._reset_icon, state=tk.NORMAL)

    # ── 按钮回调 ──────────────────────────────────────────

    def _on_start(self):
        """开始按钮：检查任务选择后启动计时"""
        if not self._selected_task_id:
            messagebox.showwarning("提示", "请先选择一个任务")
            return
        if self._controller:
            self._controller.start()

    def _on_pause(self):
        if self._controller:
            self._controller.pause()

    def _on_abandon(self):
        if self._controller:
            self._controller.abandon()


# ═══════════════════════════════════════════════════════════
#  颜色辅助
# ═══════════════════════════════════════════════════════════

def _darken_hex(hex_color: str, factor: float = 0.85) -> str:
    c = hex_color.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    r, g, b = int(r*factor), int(g*factor), int(b*factor)
    return f"#{r:02x}{g:02x}{b:02x}"
