\# CLAUDE.md - 番茄钟 + 专注增强系统



\## 技术栈

\- Python 3.9+

\- GUI: tkinter (标准库)

\- 数据: JSON 单文件 `data.json`

\- 图表: matplotlib (自动安装)

\- 图像: Pillow (自动安装)

\- 音效: winsound 或 `print("\\a")`

\- 平台: Windows 10/11 only



\## 架构

\- MVC: models/ views/ controllers/ utils/

\- 每文件 ≤150 行

\- 入口: main.py



\## 行为约束

\- 只输出用户明确要求的代码或 diff，不解释、不举例、不测试。

\- 修改时优先使用 unified diff，并注明文件路径。

\- 问句用中文回答，代码注释用中文。

\- 严格遵守现有设计文档，不自行增加未提及的功能。



\## 自主维护

\- 如需引入第三方库，必须在对应文件中添加导入检查，失败时自动调用 `pip install`。

\- 用户报错时，只输出修复的 diff，不需要解释原因，确保程序能重新运行。

