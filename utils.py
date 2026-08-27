import os
import shutil
import sys


def app_path():
    """返回程序运行目录：打包后为 exe 所在目录，源码运行时为 .py 所在目录"""
    if hasattr(sys, 'frozen'):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)


def clear_MEI(log=None):
    """清理 Temp 文件夹内的所有内容（文件和文件夹），释放磁盘空间

    被正在运行的程序占用的条目会删除失败，自动跳过；
    被删掉的临时文件在各程序再次运行时会自动重建，不影响使用。
    清理结束后输出一条汇总（清删/跳过的文件数与文件夹数）。
    """
    temp_path = os.environ["TEMP"]
    cleared_files = cleared_dirs = skipped_files = skipped_dirs = 0
    for item in os.listdir(temp_path):
        item_path = os.path.join(temp_path, item)
        is_dir = os.path.isdir(item_path)
        try:
            if is_dir:
                shutil.rmtree(item_path)
                cleared_dirs += 1
            else:
                os.remove(item_path)
                cleared_files += 1
        except OSError:
            # 文件被占用等原因导致删除失败，跳过并计数
            if is_dir:
                skipped_dirs += 1
            else:
                skipped_files += 1
    if log:
        log(f'Temp cleanup: cleared {cleared_files} files, {cleared_dirs} folders; '
            f'skipped {skipped_files} files, {skipped_dirs} folders.')
