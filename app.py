import os
import threading

import config
from downloader import DownloadError, download_image
from logbus import LogBus
from scheduler import Scheduler
from sources import SOURCES
from utils import app_path
from wallpaper import SCALE_MODES, change_wallpaper

CERT_PATH = os.path.join(app_path(), 'certs', 'cacert.pem')


class App:
    """应用协调层：持有唯一的状态（AppConfig），把界面、调度器、下载、壁纸串起来

    线程分工：界面在主线程操作 state；工作线程只读 state，
    每个刷新周期开始时取当下值，语义与旧版一致。
    """

    def __init__(self, auto_start=False):
        self.state = config.load()
        self.auto_start = auto_start
        self.logbus = LogBus()
        self.log = self.logbus.log
        self.scheduler = Scheduler(
            job=self.refresh_once,
            get_interval=lambda: self.state.interval_minutes,
            log=self.log,
        )
        self._shutdown_requested = threading.Event()

    # ---------- 工作线程执行的一个完整周期：下载 → 重绘 → 设壁纸 ----------

    def refresh_once(self):
        source = SOURCES[self.state.image_source]
        file_path = download_image(source, self.state.save_path, CERT_PATH, self.log)
        name_pic = os.path.splitext(os.path.basename(file_path))[0]
        flag = SCALE_MODES[self.state.scale_mode]
        ok = change_wallpaper(file_path, self.state.save_path, name_pic,
                              source, flag, self.state.watermark_on, self.log)
        if not ok:
            # 壁纸生成失败（如图片损坏）同样交给调度器重试
            raise DownloadError('Wallpaper generation failed')

    # ---------- 界面（主线程）调用的动作 ----------

    def start(self):
        """点击“开始”：校验 → 保存配置 → 启动调度线程

        返回 None 表示成功；返回 i18n key 表示有参数错误，由界面弹窗提示。
        """
        if not self.state.save_path:
            return '保存提示'
        if not isinstance(self.state.interval_minutes, (int, float)) \
                or self.state.interval_minutes <= 0:
            return '频率提示'
        config.save(self.state)
        self.scheduler.start()
        return None

    def request_shutdown(self):
        """从非主线程（托盘）发起退出：只置位标志，退出流程统一由主线程执行"""
        self._shutdown_requested.set()

    @property
    def shutdown_requested(self):
        return self._shutdown_requested.is_set()

    def prepare_exit(self):
        """退出前的收尾：保存配置、停止工作线程（只允许主线程调用）"""
        config.save(self.state)
        self.scheduler.stop()
