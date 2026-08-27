import os
import queue

from utils import app_path

LOG_FILE = 'log.txt'
MAX_LOG_SIZE = 1024 * 1024   # 超过 1MB 轮转为 log.txt.old


class LogBus:
    """线程安全的日志总线

    任意线程调用 log() 投递消息（队列本身线程安全），
    主线程每 100ms 调用 flush() 一次性取出，刷入界面和文件。
    tkinter 只在主线程被触碰，这是整个线程模型的基石。
    """

    def __init__(self):
        self._queue = queue.Queue()

    def log(self, msg):
        self._queue.put(str(msg))

    def flush(self, write_to_widget):
        """主线程调用：取出全部待写日志，交给回调刷入界面，同时落盘"""
        messages = []
        while True:
            try:
                messages.append(self._queue.get_nowait())
            except queue.Empty:
                break
        if not messages:
            return
        text = ''.join(m if m.endswith('\n') else m + '\n' for m in messages)
        write_to_widget(text)
        self._write_file(text)

    def _write_file(self, text):
        """追加写日志文件；超过 1MB 时轮转，避免无限增长"""
        try:
            path = os.path.join(app_path(), LOG_FILE)
            if os.path.exists(path) and os.path.getsize(path) > MAX_LOG_SIZE:
                old_path = path + '.old'
                if os.path.exists(old_path):
                    os.remove(old_path)
                os.replace(path, old_path)
            with open(path, 'a', encoding='utf-8') as f:
                f.write(text)
        except OSError:
            # 日志落盘失败不影响主流程
            pass
