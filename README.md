# 番茄钟 + 专注增强系统

一个基于 Python tkinter 的番茄工作法桌面应用，集成了任务管理、数据统计、情绪追踪与专注果实系统。

## 技术栈

- **语言**: Python 3.9+
- **GUI**: tkinter (标准库)
- **数据存储**: JSON 单文件 (`data.json`)
- **图表**: matplotlib
- **图像处理**: Pillow

## 快速启动

```bash
# 克隆项目
git clone https://github.com/YunSh37/pomodoro.git
cd pomodoro

# 安装依赖（程序首次运行时会自动安装 matplotlib 和 Pillow）
# 或手动安装：
pip install matplotlib Pillow

# 启动应用
python main.py
```

## 功能特性

- **番茄钟计时器** — 多档时长可选（5/10/15/25/45/60 分钟）
- **任务管理** — 添加、编辑、完成、软删除、恢复、永久删除
- **专注果实系统** — 累计番茄数合成果实（白→绿→紫→红，5:1 合成）
- **心碎果实系统** — 累计中断数合成心碎（💔→🤡→🖤，3:1 合成）
- **情绪追踪** — 完成番茄时记录心情（已傻→巅峰）和备注
- **数据统计** — 今日/本周/本月专注时长柱状图、情绪饼图、历史记录
- **周报生成** — 自动生成本周专注报告 PNG
- **段位系统** — 连续专注天数晋升（青铜→白银→黄金→钻石→大师→番茄神）
- **深色模式** — 自动/手动切换深色/浅色主题
- **彩蛋动画** — 专注果实/心碎果实满级时触发全屏特效

## 项目结构

```
pomodoro/
├── main.py                    # 程序入口
├── models/
│   ├── task.py                # 任务数据模型
│   ├── tomato.py              # 番茄记录数据模型
│   ├── data_manager.py        # JSON 数据持久化
│   └── statistics.py          # 统计计算模块
├── views/
│   ├── main_window.py         # 主窗口
│   ├── stats_view.py          # 统计视图
│   ├── easter_egg.py          # 彩蛋动画
│   ├── dialog_task_edit.py    # 任务编辑对话框
│   └── flow_note_dialog.py    # 心流笔记对话框
├── controllers/
│   └── timer_controller.py    # 计时器控制器
├── utils/
│   ├── statistics.py          # 段位/果实合成/每日结算
│   ├── forest.py              # 森林绘制工具
│   ├── config.py              # 全局配置常量
│   └── advice_text.py         # 自适应建议文案
└── reports/                   # 周报 PNG 输出目录
```

## 平台支持

- Windows 10/11
