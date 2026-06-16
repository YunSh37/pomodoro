"""专注森林绘制工具 — 在 Canvas 上绘制今日番茄树"""

import tkinter as tk


def draw_today_forest(canvas: tk.Canvas, records: list):
    """在给定 Canvas 上绘制今日专注森林

    参数:
        canvas:  右侧森林区的 tk.Canvas 控件
        records: 今日的 TomatoRecord 字典列表
    """
    canvas.delete("all")  # 清空画布

    w = canvas.winfo_width()
    h = canvas.winfo_height()

    # 画布尺寸过小时跳过（初始化期间可能为 1）
    if w < 10 or h < 10:
        return

    # ── 无记录：显示引导文字 ──
    if not records:
        canvas.create_text(
            w / 2, h / 2,
            text="专注一个番茄\n种下第一棵树🌱",
            font=("微软雅黑", 10),
            fill="#9A8895",
            justify=tk.CENTER,
        )
        return

    # ── 草地背景 ──
    _draw_grass(canvas, w, h)

    # ── 分离完成与中断记录 ──
    completed = [r for r in records if r.get("was_completed", False)]
    abandoned = [r for r in records if not r.get("was_completed", False)]

    total = len(completed)
    # 树冠颜色：从浅绿渐变到深绿
    colors = [
        "#A8D5A2",  # 浅绿（第 1 棵）
        "#81C784",
        "#66BB6A",
        "#4CAF50",
        "#43A047",
        "#388E3C",
        "#2E7D32",
        "#1B5E20",  # 深绿（第 8 棵及以后）
    ]

    # 最多绘制 12 棵树
    max_trees = min(total, 12)
    # 树之间的水平间距
    spacing = w / (max_trees + 1) if max_trees > 0 else 0
    # 树的大小基数（根据画布宽度自适应）
    base_size = max(24, min(40, w / 8))

    for i in range(max_trees):
        # 错开位置：让树不排成直线
        x = spacing * (i + 1) + (i % 3 - 1) * (spacing * 0.15)
        y_base = h - 12  # 树干底部在草地线上
        # 树冠颜色按序号递进
        color_idx = min(i, len(colors) - 1)
        crown_color = colors[color_idx]
        _draw_tree(canvas, x, y_base, base_size, crown_color, i)

    # ── 绘制枯萎植物（中断记录） ──
    for i, _ in enumerate(abandoned):
        if i >= 6:  # 最多显示 6 株枯萎植物
            break
        # 放置在右下角区域
        x = w - 30 - i * 28
        y_base = h - 10
        _draw_withered(canvas, x, y_base, base_size * 0.7)


# ═══════════════════════════════════════════════════════════
#  内部绘制函数
# ═══════════════════════════════════════════════════════════

def _draw_grass(canvas: tk.Canvas, w: int, h: int):
    """绘制草地背景 — 底部绿色弧线"""
    # 主草地
    canvas.create_arc(
        -20, h - 30, w + 20, h + 30,
        start=0, extent=180,
        fill="#C8E6C9", outline="", tags="grass",
    )
    # 前景草地
    canvas.create_arc(
        -10, h - 18, w + 10, h + 20,
        start=0, extent=180,
        fill="#A5D6A7", outline="", tags="grass",
    )


def _draw_tree(canvas: tk.Canvas, x: float, y_base: float,
               size: float, crown_color: str, index: int):
    """绘制一棵小树：棕色树干 + 圆形树冠

    参数:
        canvas:      目标画布
        x, y_base:   树干底部中心坐标
        size:        树的大小基数
        crown_color: 树冠颜色
        index:       树的序号（用于微调位置）
    """
    trunk_h = size * 1.1          # 树干高度
    trunk_w = size * 0.15         # 树干宽度
    crown_r = size * 0.38         # 树冠半径

    trunk_top = y_base - trunk_h

    # ── 树干（圆角矩形模拟） ──
    canvas.create_rectangle(
        x - trunk_w / 2, y_base,
        x + trunk_w / 2, trunk_top,
        fill="#8B6B4A", outline="#7A5C3E", width=1, tags="tree",
    )

    # ── 树冠（两个重叠圆，更可爱） ──
    # 大圆（偏上）
    canvas.create_oval(
        x - crown_r, trunk_top - crown_r * 1.6,
        x + crown_r, trunk_top + crown_r * 0.2,
        fill=crown_color, outline=_darken(crown_color), width=1, tags="tree",
    )
    # 小圆（偏下左）
    offset = crown_r * 0.3
    small_r = crown_r * 0.7
    canvas.create_oval(
        x - offset - small_r, trunk_top - crown_r * 0.6,
        x - offset + small_r, trunk_top + crown_r * 0.6,
        fill=_lighten(crown_color), outline="", tags="tree",
    )
    # 小圆（偏下右）
    canvas.create_oval(
        x + offset - small_r, trunk_top - crown_r * 0.5,
        x + offset + small_r, trunk_top + crown_r * 0.7,
        fill=_lighten(crown_color, 0.85), outline="", tags="tree",
    )

    # ── 树冠高光 ──
    highlight_r = crown_r * 0.18
    canvas.create_oval(
        x - crown_r * 0.5 - highlight_r, trunk_top - crown_r * 1.2 - highlight_r,
        x - crown_r * 0.5 + highlight_r, trunk_top - crown_r * 1.2 + highlight_r,
        fill="#FFFFFF", outline="", stipple="gray25", tags="tree",
    )


def _draw_withered(canvas: tk.Canvas, x: float, y_base: float, size: float):
    """绘制一株枯萎植物：灰色细枝 + 枯叶

    参数:
        canvas:      目标画布
        x, y_base:   根部坐标
        size:        大小基数
    """
    trunk_h = size * 0.8
    trunk_w = size * 0.06

    trunk_top = y_base - trunk_h

    # 灰色细干
    canvas.create_line(
        x, y_base, x, trunk_top,
        fill="#9E9E9E", width=max(1, int(trunk_w)), tags="withered",
    )
    # 倾斜细枝
    canvas.create_line(
        x, trunk_top + trunk_h * 0.3,
        x - size * 0.3, trunk_top + trunk_h * 0.1,
        fill="#BDBDBD", width=1, tags="withered",
    )
    canvas.create_line(
        x, trunk_top + trunk_h * 0.4,
        x + size * 0.25, trunk_top,
        fill="#BDBDBD", width=1, tags="withered",
    )
    # 枯叶
    leaf_r = size * 0.1
    canvas.create_oval(
        x - size * 0.3 - leaf_r, trunk_top - leaf_r,
        x - size * 0.3 + leaf_r, trunk_top + leaf_r,
        fill="#A1887F", outline="", tags="withered",
    )
    canvas.create_oval(
        x + size * 0.25 - leaf_r, trunk_top - size * 0.1 - leaf_r,
        x + size * 0.25 + leaf_r, trunk_top - size * 0.1 + leaf_r,
        fill="#BCAAA4", outline="", tags="withered",
    )


# ═══════════════════════════════════════════════════════════
#  颜色辅助函数
# ═══════════════════════════════════════════════════════════

def _darken(hex_color: str, factor: float = 0.85) -> str:
    """将 hex 颜色变暗"""
    c = hex_color.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    r, g, b = int(r * factor), int(g * factor), int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def _lighten(hex_color: str, factor: float = 0.70) -> str:
    """将 hex 颜色变亮（向白色混合）"""
    c = hex_color.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    r = int(r + (255 - r) * (1 - factor))
    g = int(g + (255 - g) * (1 - factor))
    b = int(b + (255 - b) * (1 - factor))
    return f"#{r:02x}{g:02x}{b:02x}"
