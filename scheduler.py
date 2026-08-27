import threading

RETRY_DELAY = 60         # 失败后的快速重试间隔（秒）
MAX_QUICK_RETRIES = 3    # 连续失败超过此次数后，退回正常周期继续尝试


class Scheduler:
    """常驻工作线程：循环执行任务，失败退避重试，只有 stop() 能让它停下

    这是修复“一次网络失败 = 自动更新永久停止”的核心：
    任务失败不再中断循环，而是记录原因并按策略重试。
    """

    def __init__(self, job, get_interval, log):
        self._job = job                  # 一个完整刷新周期（下载→生成→设壁纸）
        self._get_interval = get_interval  # 返回当前间隔（分钟）
        self._log = log
        self._stop = threading.Event()
        self._thread = None
        self.run_times = 0

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        """启动；若已在运行则先停旧线程再起新线程（等价于旧版点“开始”时取消全部定时器）"""
        self.stop()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name='wallpaper-worker')
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            # 正在下载时最多等这几秒，等不到也不阻塞退出（线程是守护线程）
            self._thread.join(timeout=5)
            self._thread = None

    def _run(self):
        consecutive_failures = 0
        while not self._stop.is_set():
            try:
                self._job()
                self.run_times += 1
                self._log(f'Run_times = {self.run_times}')
                self._log('\n' + '=' * 48 + '\n')
                consecutive_failures = 0
                delay = self._get_interval() * 60
            except Exception as e:
                consecutive_failures += 1
                self._log(f'!!Refresh failed ({consecutive_failures}): {e}')
                self._log('\n' + '=' * 48 + '\n')
                if consecutive_failures <= MAX_QUICK_RETRIES:
                    self._log(f'Will retry in {RETRY_DELAY} seconds')
                    delay = RETRY_DELAY
                else:
                    self._log('Too many consecutive failures, '
                              'waiting for next normal cycle')
                    delay = self._get_interval() * 60
            # 可中断的等待：stop() 置位时立即醒来退出
            if self._stop.wait(delay):
                break
