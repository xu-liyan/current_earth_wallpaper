import sys

from app import App
from ui import MainWindow


def _autostart_flag():
    """快捷方式/注册表以参数 1 启动时，程序自动开始更新壁纸"""
    if len(sys.argv) > 1:
        try:
            return int(sys.argv[1]) == 1
        except ValueError:
            pass
    return False


def main():
    application = App(auto_start=_autostart_flag())
    window = MainWindow(application)
    window.run()


if __name__ == '__main__':
    main()
