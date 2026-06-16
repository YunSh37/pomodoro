"""统计视图 — 专注数据可视化与周报生成"""

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import font_manager as fm

from models.data_manager import get_all_tasks
from models.statistics import (
    get_duration_bar_data,
    get_mood_pie_data,
    get_history_records,
    get_weekly_report_data,
    get_week_range,
)

# 中文字体支持
_CN_FONT = None

def _get_cn_font():
    """获取系统中可用的中文字体"""
    global _CN_FONT
    if _CN_FONT is not None:
        return _CN_FONT
    candidates = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC",
                   "WenQuanYi Micro Hei", "PingFang SC", "sans-serif"]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            _CN_FONT = name
            return _CN_FONT
    _CN_FONT = candidates[0]
    return _CN_FONT


class StatsView:
    """统计视图 — 覆盖在主窗口之上的全屏统计页面"""

    # 图表配色（浅色/深色）
    LIGHT_THEME = {
        "bg": "#F9F4F7",
        "surface": "#FFFFFF",
        "text": "#4A3845",
        "text_soft": "#8B7D85",
        "primary": "#C07A90",
        "filter_active_bg": "#C07A90",
        "filter_active_fg": "#FFFFFF",
        "filter_idle_bg": "#EBE0E5",
        "filter_idle_fg": "#8B7D85",
        "bar_color": "#C07A90",
        "bar_edge": "#AE6880",
        "grid_color": "#E8E0E5",
        "figure_bg": "#FFFFFF",
        "figure_fg": "#4A3845",
        "tree_bg": "#FFFFFF",
        "tree_fg": "#4A3845",
        "tree_heading_bg": "#EBE0E5",
        "tree_selected_bg": "#C07A90",
        "tree_selected_fg": "#FFFFFF",
    }

    DARK_THEME = {
        "bg": "#1B1F26",
        "surface": "#252A33",
        "text": "#D8DEE9",
        "text_soft": "#8FA3B8",
        "primary": "#7D9FC0",
        "filter_active_bg": "#7D9FC0",
        "filter_active_fg": "#1B1F26",
        "filter_idle_bg": "#2D333D",
        "filter_idle_fg": "#8FA3B8",
        "bar_color": "#7D9FC0",
        "bar_edge": "#6B8DAE",
        "grid_color": "#333842",
        "figure_bg": "#252A33",
        "figure_fg": "#D8DEE9",
        "tree_bg": "#252A33",
        "tree_fg": "#D8DEE9",
        "tree_heading_bg": "#2D333D",
        "tree_selected_bg": "#7D9FC0",
        "tree_selected_fg": "#1B1F26",
    }

    def __init__(self, parent, main_window):
        """
        参数:
            parent:      主窗口 (tk.Tk)
            main_window: MainWindow 实例（用于回调返回）
        """
        self._parent = parent
        self._main = main_window
        self._dark = main_window._dark
        self._theme = self.DARK_THEME if self._dark else self.LIGHT_THEME
        self._range_key = "today"
        self._records = []

        # 主容器（覆盖整个窗口）
        self._frame = tk.Frame(parent, bg=self._theme["bg"])
        # 不在此处 pack，由 main_window 控制显示

        self._build_ui()

    # ── UI 构建 ──────────────────────────────────────────

    def _build_ui(self):
        c = self._theme

        # ── 顶部工具栏 ──
        self._toolbar = tk.Frame(self._frame, bg=c["bg"])
        self._toolbar.pack(fill=tk.X, padx=16, pady=(12, 8))

        # 返回按钮
        self._back_btn = tk.Button(
            self._toolbar, text="← 返回", font=("微软雅黑", 10),
            bg=c["primary"], fg=c["filter_active_fg"],
            relief=tk.FLAT, padx=12, pady=2,
            command=self._on_back,
        )
        self._back_btn.pack(side=tk.LEFT)

        # 标题
        self._title_label = tk.Label(
            self._toolbar, text="📊 专注统计", font=("微软雅黑", 14, "bold"),
            bg=c["bg"], fg=c["text"],
        )
        self._title_label.pack(side=tk.LEFT, padx=16)

        # 时间范围切换按钮（靠右）
        self._range_btns = {}
        range_frame = tk.Frame(self._toolbar, bg=c["bg"])
        range_frame.pack(side=tk.RIGHT)

        range_opts = [("today", "今日"), ("week", "本周"), ("month", "本月")]
        for key, text in range_opts:
            btn = tk.Label(
                range_frame, text=text, font=("微软雅黑", 9),
                bg=c["filter_idle_bg"], fg=c["filter_idle_fg"],
                padx=10, pady=3, cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=2)
            # 点击事件绑定
            btn.bind("<Button-1>", lambda e, k=key: self._on_range_change(k))
            self._range_btns[key] = btn

        # 更新筛选按钮高亮
        self._update_range_btns()

        # ── 内容区域（左右分栏 + 底部列表） ──
        self._content = tk.Frame(self._frame, bg=c["bg"])
        self._content.pack(fill=tk.BOTH, expand=True, padx=16)

        # 上半部分：左右分栏（图表区）
        self._charts_frame = tk.Frame(self._content, bg=c["bg"])
        self._charts_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧 — 柱状图容器
        self._bar_container = tk.Frame(self._charts_frame, bg=c["surface"],
                                        bd=0, highlightthickness=1,
                                        highlightbackground=c["grid_color"])
        self._bar_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                                  padx=(0, 4), pady=(0, 4))

        # 柱状图标题（持久组件）
        self._bar_title = tk.Label(self._bar_container, text="",
                                    font=("微软雅黑", 10, "bold"),
                                    bg=c["surface"], fg=c["text"])
        self._bar_title.pack(pady=(8, 0))

        # 持久 Figure + Canvas（不再重建，避免闪烁）
        self._bar_fig = Figure(figsize=(4.5, 3.2), dpi=85, facecolor=c["figure_bg"])
        self._bar_ax = self._bar_fig.add_subplot(111)
        self._bar_canvas = FigureCanvasTkAgg(self._bar_fig, master=self._bar_container)
        self._bar_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True,
                                               padx=8, pady=(4, 8))

        # 右侧 — 饼图容器
        self._pie_container = tk.Frame(self._charts_frame, bg=c["surface"],
                                        bd=0, highlightthickness=1,
                                        highlightbackground=c["grid_color"])
        self._pie_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True,
                                  padx=(4, 0), pady=(0, 4))

        # 饼图标题（持久组件）
        self._pie_title = tk.Label(self._pie_container, text="",
                                    font=("微软雅黑", 10, "bold"),
                                    bg=c["surface"], fg=c["text"])
        self._pie_title.pack(pady=(8, 0))

        # 持久 Figure + Canvas
        self._pie_fig = Figure(figsize=(3.8, 3.0), dpi=85, facecolor=c["figure_bg"])
        self._pie_ax = self._pie_fig.add_subplot(111)
        self._pie_canvas = FigureCanvasTkAgg(self._pie_fig, master=self._pie_container)
        self._pie_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True,
                                               padx=8, pady=(4, 8))

        # 下半部分 — 历史记录列表
        self._history_frame = tk.Frame(self._content, bg=c["surface"],
                                        bd=0, highlightthickness=1,
                                        highlightbackground=c["grid_color"])
        self._history_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        # 历史标题行
        self._hist_header = tk.Frame(self._history_frame, bg=c["surface"])
        self._hist_header.pack(fill=tk.X, padx=10, pady=(8, 4))

        self._hist_title = tk.Label(
            self._hist_header, text="📋 历史记录", font=("微软雅黑", 11, "bold"),
            bg=c["surface"], fg=c["text"],
        )
        self._hist_title.pack(side=tk.LEFT)

        self._hist_count = tk.Label(
            self._hist_header, text="共 0 条", font=("微软雅黑", 9),
            bg=c["surface"], fg=c["text_soft"],
        )
        self._hist_count.pack(side=tk.RIGHT)

        # 使用 Treeview 展示历史记录
        tree_columns = ("start", "end", "task", "duration", "mood", "status")
        self._tree = ttk.Treeview(
            self._history_frame, columns=tree_columns,
            show="headings", selectmode="browse",
        )
        self._tree.heading("start", text="开始时间")
        self._tree.heading("end", text="结束时间")
        self._tree.heading("task", text="关联任务")
        self._tree.heading("duration", text="时长(分)")
        self._tree.heading("mood", text="情绪")
        self._tree.heading("status", text="状态")

        self._tree.column("start", width=140, anchor=tk.CENTER)
        self._tree.column("end", width=140, anchor=tk.CENTER)
        self._tree.column("task", width=180, anchor=tk.W)
        self._tree.column("duration", width=60, anchor=tk.CENTER)
        self._tree.column("mood", width=60, anchor=tk.CENTER)
        self._tree.column("status", width=60, anchor=tk.CENTER)

        # 滚动条
        tree_scroll = ttk.Scrollbar(
            self._history_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=tree_scroll.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                         padx=(10, 0), pady=(0, 10))
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10), padx=(0, 10))

        # 初始化 Treeview 样式
        self._apply_tree_style()

        # ── 底部操作栏 ──
        self._bottom_bar = tk.Frame(self._frame, bg=c["bg"])
        self._bottom_bar.pack(fill=tk.X, padx=16, pady=(8, 12))

        self._report_btn = tk.Button(
            self._bottom_bar, text="📄 生成周报", font=("微软雅黑", 10, "bold"),
            bg=c["primary"], fg=c["filter_active_fg"],
            relief=tk.FLAT, padx=16, pady=5,
            command=self._generate_weekly_report,
        )
        self._report_btn.pack(side=tk.RIGHT)

        # 提示文字
        self._hint_label = tk.Label(
            self._bottom_bar, text="周报生成后保存为 PNG 图片至 reports/ 目录",
            font=("微软雅黑", 8), bg=c["bg"], fg=c["text_soft"],
        )
        self._hint_label.pack(side=tk.RIGHT, padx=(0, 12))

        # ── 初始加载图表 ──
        self._refresh_all()

    # ── 主题适配 ──────────────────────────────────────────

    def _apply_tree_style(self):
        """配置 Treeview 样式（初始化 + 主题切换时调用）"""
        c = self._theme
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Stats.Treeview",
                        background=c["tree_bg"],
                        foreground=c["tree_fg"],
                        fieldbackground=c["tree_bg"])
        style.configure("Stats.Treeview.Heading",
                        background=c["tree_heading_bg"],
                        foreground=c["tree_fg"])
        style.map("Stats.Treeview",
                  background=[("selected", c["tree_selected_bg"])],
                  foreground=[("selected", c["tree_selected_fg"])])
        self._tree.configure(style="Stats.Treeview")

    def apply_theme(self, dark: bool):
        """更新整个统计视图的主题配色"""
        self._dark = dark
        self._theme = self.DARK_THEME if dark else self.LIGHT_THEME
        c = self._theme

        self._frame.configure(bg=c["bg"])
        self._toolbar.configure(bg=c["bg"])
        self._title_label.configure(bg=c["bg"], fg=c["text"])
        self._back_btn.configure(bg=c["primary"], fg=c["filter_active_fg"])
        self._content.configure(bg=c["bg"])
        self._charts_frame.configure(bg=c["bg"])
        self._bottom_bar.configure(bg=c["bg"])
        self._hint_label.configure(bg=c["bg"], fg=c["text_soft"])
        self._report_btn.configure(bg=c["primary"], fg=c["filter_active_fg"])

        # 图表容器边框
        grid_c = c["grid_color"]
        surface_c = c["surface"]
        self._bar_container.configure(bg=surface_c, highlightbackground=grid_c)
        self._pie_container.configure(bg=surface_c, highlightbackground=grid_c)
        self._history_frame.configure(bg=surface_c, highlightbackground=grid_c)
        self._hist_header.configure(bg=surface_c)
        self._hist_title.configure(bg=surface_c, fg=c["text"])
        self._hist_count.configure(bg=surface_c, fg=c["text_soft"])

        # 持久图表标题
        self._bar_title.configure(bg=surface_c, fg=c["text"])
        self._pie_title.configure(bg=surface_c, fg=c["text"])

        # 持久 Figure 背景色
        self._bar_fig.patch.set_facecolor(c["figure_bg"])
        self._pie_fig.patch.set_facecolor(c["figure_bg"])

        # Treeview 样式
        self._apply_tree_style()

        # 刷新筛选按钮
        self._update_range_btns()

        # 重绘图表
        self._refresh_all()

    # ── 时间范围切换 ──────────────────────────────────────

    def _on_range_change(self, range_key: str):
        if self._range_key == range_key:
            return
        self._range_key = range_key
        self._update_range_btns()
        self._refresh_all()

    def _update_range_btns(self):
        c = self._theme
        for key, btn in self._range_btns.items():
            if key == self._range_key:
                btn.configure(bg=c["filter_active_bg"], fg=c["filter_active_fg"])
            else:
                btn.configure(bg=c["filter_idle_bg"], fg=c["filter_idle_fg"])

    # ── 刷新全部 ──────────────────────────────────────────

    def _refresh_all(self):
        self._refresh_bar_chart()
        self._refresh_pie_chart()
        self._refresh_history()

    def _refresh_bar_chart(self):
        """刷新柱状图数据（持久 Figure，不清除组件）"""
        c = self._theme
        data = get_duration_bar_data(self._range_key)
        self._bar_title.configure(text=data["title"])

        ax = self._bar_ax
        ax.clear()
        ax.set_facecolor(c["figure_bg"])

        if not data["labels"] or sum(data["values"]) == 0:
            ax.text(0.5, 0.5, "暂无数据", transform=ax.transAxes,
                     ha="center", va="center", fontsize=12,
                     color=c["text_soft"],
                     fontproperties=fm.FontProperties(family=_get_cn_font()))
            ax.set_xticks([])
            ax.set_yticks([])
            self._bar_canvas.draw()
            return

        cn_font = _get_cn_font()
        labels = data["labels"]
        values = data["values"]

        bars = ax.bar(range(len(labels)), values, color=c["bar_color"],
                       edgecolor=c["bar_edge"], linewidth=0.5, width=0.65)

        for bar_obj, val in zip(bars, values):
            if val > 0:
                ax.text(bar_obj.get_x() + bar_obj.get_width() / 2,
                         bar_obj.get_height() + max(values) * 0.02,
                         str(val), ha="center", va="bottom",
                         fontsize=7, color=c["text_soft"],
                         fontproperties=fm.FontProperties(family=cn_font))

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45 if len(labels) > 10 else 0,
                            ha="right" if len(labels) > 10 else "center",
                            fontsize=7,
                            fontproperties=fm.FontProperties(family=cn_font))
        ax.set_ylabel("专注分钟", fontsize=8,
                       fontproperties=fm.FontProperties(family=cn_font),
                       color=c["text_soft"])

        ax.tick_params(axis="x", colors=c["text_soft"])
        ax.tick_params(axis="y", colors=c["text_soft"])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(c["grid_color"])
        ax.spines["bottom"].set_color(c["grid_color"])
        ax.yaxis.grid(True, color=c["grid_color"], linewidth=0.5)
        ax.set_axisbelow(True)

        self._bar_fig.tight_layout(pad=1.5)
        self._bar_canvas.draw()

    def _refresh_pie_chart(self):
        """刷新饼图数据（持久 Figure，不清除组件）"""
        c = self._theme
        data = get_mood_pie_data(self._range_key)
        self._pie_title.configure(text=data["title"])

        ax = self._pie_ax
        ax.clear()

        if not data["labels"] or sum(data["values"]) == 0:
            ax.text(0.5, 0.5, "暂无数据", transform=ax.transAxes,
                     ha="center", va="center", fontsize=12,
                     color=c["text_soft"],
                     fontproperties=fm.FontProperties(family=_get_cn_font()))
            self._pie_canvas.draw()
            return

        cn_font = _get_cn_font()
        fp = fm.FontProperties(family=cn_font)

        wedges, texts, autotexts = ax.pie(
            data["values"],
            labels=data["labels"],
            colors=data["colors"],
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=0.6,
            textprops={"fontsize": 8, "fontproperties": fp,
                        "color": c["text"]},
        )
        for at in autotexts:
            at.set_fontsize(8)
            at.set_color("#FFFFFF")

        self._pie_fig.tight_layout(pad=1.0)
        self._pie_canvas.draw()

    def _refresh_history(self):
        """刷新历史记录列表"""
        c = self._theme
        self._records = get_history_records(self._range_key)

        # 清空现有行
        for item in self._tree.get_children():
            self._tree.delete(item)

        # 加载全部任务映射（含已删除的，id → title）
        all_tasks = get_all_tasks()
        task_map = {}
        for t in all_tasks:
            title = t.get("title", "未知")
            if t.get("is_deleted", False):
                title = f"{title}（已删除）"
            task_map[t["id"]] = title

        # 情绪映射（Treeview 可用 emoji）
        mood_map = {1: "🤤 已傻", 2: "🫠 没招了", 3: "😇 不妙", 4: "🙂 顺利", 5: "😃 巅峰"}

        # 插入记录
        for r in self._records:
            start = r.get("start_time", "")[-8:] if r.get("start_time") else ""
            end = r.get("end_time", "")[-8:] if r.get("end_time") else ""
            task_id = r.get("task_id", 0)
            task_title = task_map.get(task_id, f"任务#{task_id}")
            # 截断过长任务名
            if len(task_title) > 18:
                task_title = task_title[:16] + "…"
            duration = str(r.get("duration_minutes", 0))
            mood_val = r.get("mood", 0)
            mood_str = mood_map.get(mood_val, "—")
            status = "✅" if r.get("was_completed", False) else "❌"

            self._tree.insert("", tk.END, values=(
                start, end, task_title, duration, mood_str, status,
            ))

        # 更新计数
        self._hist_count.configure(text=f"共 {len(self._records)} 条")

    # ── 视图显示/隐藏 ─────────────────────────────────────

    def show(self):
        """显示统计视图（由 main_window 调用）"""
        self._frame.pack(fill=tk.BOTH, expand=True)
        self._refresh_all()

    def hide(self):
        """隐藏统计视图（由 main_window 调用）"""
        self._frame.pack_forget()

    # ── 返回 ──────────────────────────────────────────────

    def _on_back(self):
        self._main.hide_stats_view()

    # ── 周报生成 ──────────────────────────────────────────

    def _generate_weekly_report(self):
        """生成并保存本周专注报告为 PNG"""
        from PIL import Image, ImageDraw, ImageFont

        report = get_weekly_report_data()

        # 创建 reports 目录
        reports_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "reports")
        os.makedirs(reports_dir, exist_ok=True)

        filename = (f"weekly_report_{report['week_start']}"
                     f"_{report['week_end']}.png")
        filepath = os.path.join(reports_dir, filename)

        # ── 生成报告图表 ──
        c = self._theme
        cn_font_name = _get_cn_font()

        # 创建大图
        dpi = 120
        fig = Figure(figsize=(8, 10), dpi=dpi)
        fig.patch.set_facecolor(c["figure_bg"])

        # ── 标题区 ──
        fig.suptitle("📊 番茄钟周报", fontsize=18, fontweight="bold",
                      fontfamily=cn_font_name, color=c["text"], y=0.98)

        # ── 概要信息 ──
        ax_info = fig.add_axes([0.08, 0.82, 0.84, 0.10])
        ax_info.axis("off")
        info_lines = [
            f"周期：{report['week_start']} ~ {report['week_end']}",
            f"总专注时长：{report['total_minutes']} 分钟　"
            f"完成番茄：{report['completed_count']}　"
            f"中断：{report['interrupted_count']}",
            f"连续专注天数：{report['streak_days']}　段位：{report['rank']}　"
            f"任务：{report['tasks_completed']}/{report['tasks_total']} 完成",
        ]
        for i, line in enumerate(info_lines):
            ax_info.text(0.5, 0.85 - i * 0.35, line,
                          transform=ax_info.transAxes,
                          ha="center", va="top", fontsize=10,
                          fontfamily=cn_font_name, color=c["text"])

        # ── 每日柱状图 ──
        bar_data = report["daily_bar"]
        ax_bar = fig.add_axes([0.08, 0.48, 0.88, 0.28])
        ax_bar.set_facecolor(c["figure_bg"])
        ax_bar.set_title(bar_data["title"], fontsize=11,
                          fontfamily=cn_font_name, color=c["text"])
        if bar_data["labels"]:
            x = range(len(bar_data["labels"]))
            ax_bar.bar(x, bar_data["values"], color=c["bar_color"],
                        edgecolor=c["bar_edge"], linewidth=0.5)
            ax_bar.set_xticks(list(x))
            ax_bar.set_xticklabels(bar_data["labels"], rotation=30,
                                    ha="right", fontsize=7,
                                    fontfamily=cn_font_name)
            for xi, vi in zip(x, bar_data["values"]):
                if vi > 0:
                    ax_bar.text(xi, vi + max(bar_data["values"]) * 0.02,
                                 str(vi), ha="center", fontsize=7,
                                 color=c["text_soft"],
                                 fontfamily=cn_font_name)
        ax_bar.set_ylabel("分钟", fontsize=8, fontfamily=cn_font_name,
                           color=c["text_soft"])
        ax_bar.spines["top"].set_visible(False)
        ax_bar.spines["right"].set_visible(False)
        ax_bar.spines["left"].set_color(c["grid_color"])
        ax_bar.spines["bottom"].set_color(c["grid_color"])
        ax_bar.tick_params(axis="x", colors=c["text_soft"])
        ax_bar.tick_params(axis="y", colors=c["text_soft"])
        ax_bar.yaxis.grid(True, color=c["grid_color"], linewidth=0.5)
        ax_bar.set_axisbelow(True)

        # ── 情绪饼图 ──
        pie_data = report["mood_pie"]
        ax_pie = fig.add_axes([0.08, 0.08, 0.40, 0.33])
        ax_pie.set_title(pie_data["title"], fontsize=11,
                          fontfamily=cn_font_name, color=c["text"])
        if pie_data["labels"]:
            ax_pie.pie(
                pie_data["values"],
                labels=pie_data["labels"],
                colors=pie_data["colors"],
                autopct="%1.1f%%",
                startangle=90,
                textprops={"fontsize": 8, "fontfamily": cn_font_name,
                            "color": c["text"]},
            )

        # ── 水印 ──
        ax_water = fig.add_axes([0.50, 0.08, 0.45, 0.33])
        ax_water.axis("off")
        ax_water.text(0.5, 0.6, "番茄钟生成", transform=ax_water.transAxes,
                       ha="center", va="center", fontsize=28,
                       fontfamily=cn_font_name, color=c["grid_color"],
                       alpha=0.5)
        ax_water.text(0.5, 0.3, f"生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                       transform=ax_water.transAxes,
                       ha="center", va="center", fontsize=9,
                       fontfamily=cn_font_name, color=c["text_soft"])

        # 保存
        fig.savefig(filepath, dpi=dpi, bbox_inches="tight",
                     facecolor=c["figure_bg"], edgecolor="none")
        import matplotlib.pyplot as plt
        plt.close(fig)

        # 弹窗提示
        self._show_report_dialog(filepath)

    def _show_report_dialog(self, filepath: str):
        """显示周报保存成功弹窗"""
        dialog = tk.Toplevel(self._parent)
        dialog.title("周报已生成")
        dialog.geometry("380x150")
        dialog.resizable(False, False)
        dialog.transient(self._parent)
        dialog.grab_set()

        c = self._theme
        dialog.configure(bg=c["bg"])

        frame = tk.Frame(dialog, bg=c["bg"], padx=20, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame, text="✅ 周报已生成", font=("微软雅黑", 12, "bold"),
            bg=c["bg"], fg=c["text"],
        ).pack(anchor=tk.W)

        # 截断显示路径
        display_path = filepath
        if len(display_path) > 60:
            display_path = "…" + display_path[-55:]

        tk.Label(
            frame, text=display_path, font=("微软雅黑", 8),
            bg=c["bg"], fg=c["text_soft"], wraplength=340,
        ).pack(anchor=tk.W, pady=(4, 10))

        btn_frame = tk.Frame(frame, bg=c["bg"])
        btn_frame.pack(fill=tk.X)

        tk.Button(
            btn_frame, text="关闭", font=("微软雅黑", 9),
            bg=c["filter_idle_bg"], fg=c["filter_idle_fg"],
            relief=tk.FLAT, padx=12, pady=4,
            command=dialog.destroy,
        ).pack(side=tk.RIGHT)

        def open_folder():
            folder = os.path.dirname(filepath)
            # 跨平台打开文件夹
            try:
                os.startfile(folder)
            except Exception:
                try:
                    subprocess.run(["explorer", folder], shell=True)
                except Exception:
                    pass
            dialog.destroy()

        tk.Button(
            btn_frame, text="📂 打开文件夹", font=("微软雅黑", 9, "bold"),
            bg=c["primary"], fg=c["filter_active_fg"],
            relief=tk.FLAT, padx=12, pady=4,
            command=open_folder,
        ).pack(side=tk.RIGHT, padx=(0, 8))

        # 居中
        dialog.update_idletasks()
        pw, ph = self._parent.winfo_width(), self._parent.winfo_height()
        px, py = self._parent.winfo_x(), self._parent.winfo_y()
        dw, dh = 380, 150
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        dialog.geometry(f"+{x}+{y}")
