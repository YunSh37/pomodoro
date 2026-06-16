"""彩蛋动画 — 专注果实/心碎果实满级特效覆盖层"""

import tkinter as tk
import random
import math


class EasterEgg:
    """全屏彩蛋动画（使用 tkinter after() 分帧，不阻塞 UI）

    用法:
        egg = EasterEgg(parent, theme_type="focus", on_done=callback)
        # 动画自动播放，完成后调用 on_done，覆盖层自动销毁
    """

    # ── 专注彩蛋配色（金色/暖色系） ──
    FOCUS_THEME = {
        "flash_colors": ["#FF6B00", "#FF8C00", "#FFD700", "#FFA500", "#FF4500"],
        "text_color":  "#FFD700",
        "glow_color":  "#FFA500",
        "particles":   ["#FFD700", "#FFA500", "#FF6347", "#FFFF00", "#FF8C00",
                         "#FF4500", "#FFEC8B"],
        "bg_flash":    "#1A0A00",
    }

    # ── 心碎彩蛋配色（暗红/紫色系） ──
    HEART_THEME = {
        "flash_colors": ["#8B0000", "#4B0082", "#800020", "#6A0DAD", "#B22222"],
        "text_color":  "#FF4444",
        "glow_color":  "#8B0000",
        "particles":   ["#8B0000", "#4B0082", "#800020", "#FF0000", "#9400D3",
                         "#DC143C", "#551A8B"],
        "bg_flash":    "#0D0010",
    }

    # 帧时长（毫秒）
    TICK_MS = 50
    FLASH_COUNT = 5          # 闪烁次数
    GROW_DURATION = 800      # 文字放大时长 ms
    HOLD_DURATION = 1400     # 停留时长 ms
    FADE_DURATION = 500      # 淡出时长 ms

    PARTICLE_RATE = 6
    PARTICLE_GRAVITY = 0.18
    MAX_PARTICLES = 280

    def __init__(self, parent, theme_type="focus", on_done=None):
        self._parent = parent
        self._on_done = on_done
        self._theme = self.FOCUS_THEME if theme_type == "focus" else self.HEART_THEME
        self._text = "专注之力已满！🏆" if theme_type == "focus" else "心碎成河…💔"
        self._particles = []
        self._frame_idx = 0
        self._after_id = None
        self._done = False

        # 计算阶段边界（帧序号）
        flash_frames = self.FLASH_COUNT * 2
        self._grow_frames = max(1, self.GROW_DURATION // self.TICK_MS)
        self._hold_frames = max(1, self.HOLD_DURATION // self.TICK_MS)
        self._fade_frames = max(1, self.FADE_DURATION // self.TICK_MS)

        self._PHASE_FLASH_END = flash_frames
        self._PHASE_GROW_END = flash_frames + self._grow_frames
        self._PHASE_HOLD_END = flash_frames + self._grow_frames + self._hold_frames
        self._TOTAL = (flash_frames + self._grow_frames +
                       self._hold_frames + self._fade_frames)

        # ── 创建全屏覆盖 Toplevel ──
        self._top = tk.Toplevel(parent)
        self._top.attributes("-fullscreen", True)
        self._top.attributes("-topmost", True)
        self._top.overrideredirect(True)
        self._top.configure(bg="black")
        self._top.attributes("-alpha", 0.0)

        # Canvas
        self._canvas = tk.Canvas(self._top, bg="black", highlightthickness=0)
        self._canvas.pack(fill=tk.BOTH, expand=True)

        # 强制映射窗口，确保后续能拿到正确的宽高
        self._top.update_idletasks()

        # 交互跳过
        self._top.bind("<Escape>", lambda e: self._abort())
        self._top.bind("<Button-1>", lambda e: self._abort())
        self._top.bind("<space>", lambda e: self._abort())

        # 启动
        self._tick()

    # ── 动画主循环 ──────────────────────────────────────

    def _tick(self):
        if self._done:
            return
        if self._frame_idx >= self._TOTAL:
            self._finish()
            return

        idx = self._frame_idx
        self._frame_idx += 1

        # ═══ 阶段 1：背景闪烁 ═══
        if idx < self._PHASE_FLASH_END:
            if idx % 2 == 0:
                ci = (idx // 2) % len(self._theme["flash_colors"])
                c = self._theme["flash_colors"][ci]
                self._top.configure(bg=c)
                self._canvas.configure(bg=c)
                self._top.attributes("-alpha", 0.92)
            else:
                self._top.configure(bg="black")
                self._canvas.configure(bg="black")
                self._top.attributes("-alpha", 0.55)

        # ═══ 阶段 2：文字放大 ═══
        elif idx < self._PHASE_GROW_END:
            self._top.attributes("-alpha", 1.0)  # 关键：恢复完全不透明
            self._top.configure(bg=self._theme["bg_flash"])
            self._canvas.configure(bg=self._theme["bg_flash"])
            progress = (idx - self._PHASE_FLASH_END) / self._grow_frames
            eased = 1.0 - (1.0 - progress) ** 3
            font_size = int(8 + eased * 64)  # 8 → 72
            self._draw_text(font_size)
            self._spawn_particles()
            self._update_particles()

        # ═══ 阶段 3：停留 ═══
        elif idx < self._PHASE_HOLD_END:
            self._top.attributes("-alpha", 1.0)
            self._draw_text(72)
            self._spawn_particles()
            self._update_particles()

        # ═══ 阶段 4：淡出 ═══
        else:
            progress = (idx - self._PHASE_HOLD_END) / self._fade_frames
            self._top.attributes("-alpha", max(0, 1.0 - progress))
            self._draw_text(72)
            self._spawn_particles()
            self._update_particles()

        self._after_id = self._parent.after(self.TICK_MS, self._tick)

    # ── 文字绘制 ────────────────────────────────────────

    def _draw_text(self, font_size):
        # 清理上一帧的文字（所有 text_ 前缀标签）
        self._canvas.delete("text_glow", "text_main")
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w < 100:
            w = self._parent.winfo_screenwidth()
        if h < 100:
            h = self._parent.winfo_screenheight()
        cx, cy = w // 2, h // 2

        glow_c = self._theme["glow_color"]
        # 外发光：8 向偏移
        for dx, dy in [(-3,-3),(3,-3),(-3,3),(3,3),(-2,0),(2,0),(0,-2),(0,2)]:
            self._canvas.create_text(
                cx + dx, cy + dy,
                text=self._text,
                font=("微软雅黑", font_size, "bold"),
                fill=glow_c,
                anchor="center", tags="text_glow",
            )

        # 主文字
        self._canvas.create_text(
            cx, cy,
            text=self._text,
            font=("微软雅黑", font_size, "bold"),
            fill=self._theme["text_color"],
            anchor="center", tags="text_main",
        )

    # ── 粒子系统 ────────────────────────────────────────

    def _spawn_particles(self):
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w < 100:
            w = self._parent.winfo_screenwidth()
        if h < 100:
            h = self._parent.winfo_screenheight()
        cx, cy = w // 2, h // 2

        for _ in range(self.PARTICLE_RATE):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2.5, 10)
            self._particles.append({
                "x": cx + random.uniform(-30, 30),
                "y": cy + random.uniform(-20, 20),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "color": random.choice(self._theme["particles"]),
                "life": random.randint(18, 38),
                "size": random.randint(2, 7),
            })

        if len(self._particles) > self.MAX_PARTICLES:
            self._particles = self._particles[-self.MAX_PARTICLES:]

    def _update_particles(self):
        self._canvas.delete("particle")
        alive = []
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += self.PARTICLE_GRAVITY
            p["life"] -= 1
            if p["life"] > 0:
                r = p["size"] * (p["life"] / 38.0)
                self._canvas.create_oval(
                    p["x"] - r, p["y"] - r,
                    p["x"] + r, p["y"] + r,
                    fill=p["color"], outline="",
                    tags="particle",
                )
                alive.append(p)
        self._particles = alive

    # ── 收尾 ────────────────────────────────────────────

    def _abort(self):
        if self._after_id is not None:
            self._parent.after_cancel(self._after_id)
            self._after_id = None
        self._finish()

    def _finish(self):
        if self._done:
            return
        self._done = True
        if self._after_id is not None:
            self._parent.after_cancel(self._after_id)
            self._after_id = None
        try:
            self._top.destroy()
        except tk.TclError:
            pass
        if self._on_done:
            self._on_done()
