import os
import threading
import tkinter as tk
import tkinter.scrolledtext as st
from tkinter import ttk, filedialog, messagebox

import pystray
from PIL import Image

import autostart
from i18n import LANGUAGES, tr
from sources import SOURCES
from utils import app_path, clear_MEI
from wallpaper import SCALE_MODES

POLL_INTERVAL = 100   # 主线程轮询日志/退出请求的间隔（毫秒）


class MainWindow:
    """界面层：只负责渲染和转发事件，业务全部交给 app

    铁律：tkinter 控件只在主线程被触碰。
    工作线程的日志走 LogBus 队列，托盘线程的退出请求走 Event，
    都由 _poll() 在主线程统一消化。
    """

    def __init__(self, app):
        self.app = app
        self.icon = None
        self._build_widgets()
        self._build_tray()
        self._render()
        # 快捷方式带参数 1 启动（开机自启）时，自动开始更新
        if app.auto_start:
            self.window.after(1000, self._on_start)

    # ---------- 界面构建（只建骨架，文案统一由 _render 填充） ----------

    def _build_widgets(self):
        state = self.app.state

        self.window = tk.Tk()
        # 关闭窗口 = 隐藏到托盘继续运行
        self.window.protocol('WM_DELETE_WINDOW', self.window.withdraw)
        self.window.iconbitmap(os.path.join(app_path(), 'tmp.ico'))

        # 语言下拉框
        self.lang_var = tk.StringVar(value=state.language)
        self.combo_lang = ttk.Combobox(self.window, textvariable=self.lang_var,
                                       state='readonly', width=9)
        self.combo_lang['values'] = LANGUAGES
        self.combo_lang.bind('<<ComboboxSelected>>',
                             lambda e: self._on_language_changed())

        # 图像源单选
        self.source_frame = ttk.LabelFrame(self.window)
        self.current_url_var = tk.StringVar(value=state.image_source)
        self.source_radios = []
        for key in SOURCES:
            radio = ttk.Radiobutton(self.source_frame, value=key,
                                    variable=self.current_url_var,
                                    command=self._on_source_changed)
            radio.pack(anchor=tk.W)
            self.source_radios.append(radio)
        self.source_frame.pack(fill=tk.X, padx=10, pady=10)

        # 壁纸比例单选
        self.scale_frame = ttk.LabelFrame(self.window)
        self.current_scale_var = tk.StringVar(value=state.scale_mode)
        self.scale_radios = []
        for key in SCALE_MODES:
            radio = ttk.Radiobutton(self.scale_frame, value=key,
                                    variable=self.current_scale_var,
                                    command=self._on_scale_changed)
            radio.pack(anchor=tk.W)
            self.scale_radios.append(radio)
        self.scale_frame.pack(fill=tk.X, padx=10, pady=10)

        # 保存位置
        folder_frame = ttk.Frame(self.window)
        self.folder_label = ttk.Label(folder_frame)
        self.folder_label.pack(side=tk.LEFT)
        self.save_path_var = tk.StringVar(value=state.save_path)
        folder_entry = ttk.Entry(folder_frame, textvariable=self.save_path_var,
                                 state='readonly')
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.folder_button = ttk.Button(folder_frame, command=self._on_browse)
        self.folder_button.pack(side=tk.RIGHT)
        folder_frame.pack(fill=tk.X, padx=10, pady=10)

        # 获取频率
        interval_frame = ttk.Frame(self.window)
        self.interval_label = ttk.Label(interval_frame)
        self.interval_label.pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value=str(state.interval_minutes))
        interval_entry = ttk.Entry(interval_frame, width=5,
                                   textvariable=self.interval_var)
        interval_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.interval_unit = ttk.Label(interval_frame)
        self.interval_unit.pack(side=tk.LEFT)
        interval_frame.pack(anchor=tk.W, padx=10, pady=10)

        # 开始 / 退出 / 水印 / 自启按钮
        self.start_button = ttk.Button(self.window, command=self._on_start)
        self.exit_button = ttk.Button(self.window, command=self._on_exit)
        self.water_button = ttk.Button(self.window, command=self._on_watermark)
        self.auto_start_button = ttk.Button(self.window, command=self._on_auto_start)
        self.start_button.pack()
        self.exit_button.pack()
        self.water_button.pack()
        self.auto_start_button.pack()
        self.combo_lang.pack()

        # 运行日志
        self.log_frame = ttk.LabelFrame(self.window)
        self.log_text = st.ScrolledText(self.log_frame, width=40, height=20)
        self.log_text.pack(fill='both', expand='yes')
        self.log_frame.pack(side=tk.TOP, fill='both', expand='yes')

    def _build_tray(self):
        lang = self.app.state.language
        menu = pystray.Menu(
            pystray.MenuItem(tr(lang, '显示'), self._show_window, default=True),
            pystray.MenuItem(tr(lang, '退出'), self._on_tray_quit),
        )
        image = Image.open(os.path.join(app_path(), 'tmp.ico'))
        self.icon = pystray.Icon('icon', image, tr(lang, '窗口名称'), menu)
        # 托盘在独立守护线程运行，避免阻塞 tk 事件循环
        threading.Thread(target=self.icon.run, daemon=True).start()

    # ---------- 渲染：所有界面文案的唯一出口 ----------

    def _render(self):
        lang = self.app.state.language
        state = self.app.state

        self.window.title(tr(lang, '窗口名称'))
        self.combo_lang.set(lang)
        self.source_frame.config(text=tr(lang, '选择图像源'))
        self.scale_frame.config(text=tr(lang, '选择壁纸比例'))
        self.folder_label.config(text=tr(lang, '选择图像保存位置'))
        self.folder_button.config(text=tr(lang, '浏览'))
        self.interval_label.config(text=tr(lang, '图像获取频率'))
        self.interval_unit.config(text=tr(lang, '分钟/张'))
        self.start_button.config(text=tr(lang, '开始'))
        self.exit_button.config(text=tr(lang, '退出'))
        self.log_frame.config(text=tr(lang, '运行日志'))

        # 水印按钮显示“当前动作”：开着 → 显示“取消时间水印”
        water_key = '取消时间水印' if state.watermark_on else '添加时间水印'
        self.water_button.config(text=tr(lang, water_key))

        # 自启按钮：注册表是唯一事实来源
        auto_key = '取消开机自启' if autostart.is_enabled() else '设为开机自启'
        self.auto_start_button.config(text=tr(lang, auto_key))

        for radio, key in zip(self.source_radios, SOURCES):
            radio.config(text=tr(lang, key))
        for radio, key in zip(self.scale_radios, SCALE_MODES):
            radio.config(text=tr(lang, key))

        # 托盘标题与菜单跟随语言
        if self.icon is not None:
            self.icon.title = tr(lang, '窗口名称')
            self.icon.menu = pystray.Menu(
                pystray.MenuItem(tr(lang, '显示'), self._show_window, default=True),
                pystray.MenuItem(tr(lang, '退出'), self._on_tray_quit),
            )
            self.icon.update_menu()

    # ---------- 事件处理（主线程） ----------

    def _on_language_changed(self):
        self.app.state.language = self.combo_lang.get()
        self._render()

    def _on_source_changed(self):
        self.app.state.image_source = self.current_url_var.get()

    def _on_scale_changed(self):
        self.app.state.scale_mode = self.current_scale_var.get()

    def _on_browse(self):
        selected = filedialog.askdirectory()
        if selected:
            self.app.state.save_path = selected + '\\'
            self.save_path_var.set(self.app.state.save_path)

    def _on_watermark(self):
        self.app.state.watermark_on = not self.app.state.watermark_on
        self._render()

    def _on_auto_start(self):
        lang = self.app.state.language
        target = not autostart.is_enabled()   # 目标状态：当前开着就取消，没开就设置
        try:
            autostart.set_enabled(target)
        except OSError as e:
            messagebox.showerror(tr(lang, '错误'),
                                 f"{tr(lang, '自启失败提示')}\n{e}")
            return
        # 以注册表实际状态为准判断成败，成功弹提示，失败也弹提示
        if autostart.is_enabled() == target:
            key = '自启开启提示' if target else '自启取消提示'
            messagebox.showinfo(tr(lang, '窗口名称'), tr(lang, key))
        else:
            messagebox.showerror(tr(lang, '错误'), tr(lang, '自启失败提示'))
        self._render()

    def _on_start(self):
        # 频率先校验（旧版在子线程里 float() 崩溃会导致静默停更）
        try:
            minutes = int(float(self.interval_var.get().strip()))
        except ValueError:
            minutes = 0
        if minutes <= 0:
            self._show_error('频率提示')
            return
        self.app.state.interval_minutes = minutes

        error_key = self.app.start()
        if error_key:
            self._show_error(error_key)

    def _show_error(self, key):
        lang = self.app.state.language
        messagebox.showerror(tr(lang, '错误'), tr(lang, key))

    def _on_exit(self):
        lang = self.app.state.language
        if messagebox.askokcancel(tr(lang, '退出'), tr(lang, '退出提示')):
            self._do_shutdown()

    def _on_tray_quit(self):
        # 托盘线程里只发信号，退出流程统一由主线程 _poll 执行
        self.app.request_shutdown()

    def _show_window(self):
        self.window.deiconify()

    # ---------- 主线程轮询：刷日志 + 响应退出请求 ----------

    def _poll(self):
        self.app.logbus.flush(self._append_log)
        if self.app.shutdown_requested:
            self._do_shutdown()
            return
        self.window.after(POLL_INTERVAL, self._poll)

    def _append_log(self, text):
        self.log_text.insert(tk.END, text)
        # 自动滚动到末尾，方便查看最新一次的运行日志
        self.log_text.see(tk.END)

    def _do_shutdown(self):
        # 收尾只允许主线程执行：保存配置 → 停工作线程 → 停托盘 → 销毁窗口
        self._sync_interval()
        self.app.prepare_exit()
        try:
            if self.icon is not None:
                self.icon.stop()
        except Exception:
            pass
        self.window.destroy()

    def _sync_interval(self):
        """退出前把输入框里的频率写回状态（无效值则保持上次的有效值）"""
        try:
            minutes = int(float(self.interval_var.get().strip()))
            if minutes > 0:
                self.app.state.interval_minutes = minutes
        except ValueError:
            pass

    # ---------- 窗口居中与主循环 ----------

    def _center_window(self):
        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        self.window.geometry(f'{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}')

    def run(self):
        self._center_window()
        clear_MEI(self.app.log)
        self.window.after(POLL_INTERVAL, self._poll)
        self.window.mainloop()
