"""番茄钟 + 专注增强系统 - 程序入口"""

import sys
import subprocess
import importlib

# 自动安装依赖
REQUIRED_LIBS = {
    "PIL": "Pillow",
    "matplotlib": "matplotlib",
}

for module, pip_name in REQUIRED_LIBS.items():
    try:
        importlib.import_module(module)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])

from views.main_window import MainWindow
from controllers.timer_controller import TimerController


def main():
    window = MainWindow()
    controller = TimerController(window)
    window.set_controller(controller)
    window.mainloop()


if __name__ == "__main__":
    main()
