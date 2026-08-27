import os
import sys
import winreg

RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'

# 注册表键名使用程序文件名（与旧版一致，老用户覆盖 exe 后自启设置无缝衔接）


def _reg_path():
    return os.path.abspath(sys.argv[0])


def _reg_name():
    return os.path.basename(_reg_path())


def is_enabled():
    """是否已设置开机自启"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, _reg_name())
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False


def set_enabled(enabled):
    """设置/取消开机自启；自启时带参数 1，程序启动后自动开始更新壁纸"""
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_ALL_ACCESS)
    try:
        if enabled:
            winreg.SetValueEx(key, _reg_name(), 0, winreg.REG_SZ,
                              f'"{_reg_path()}" 1')
        else:
            try:
                winreg.DeleteValue(key, _reg_name())
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)
