import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image
import pystray

import autostart
from i18n import LANGUAGES, tr
from sources import SOURCES
from utils import app_path, clear_MEI
from wallpaper import SCALE_MODES

POLL_INTERVAL = 100

# 设计稿颜色常量
COLORS = {
    'bg': '#f3f4f6',
    'surface': '#ffffff',
    'surface_muted': '#f8f9fb',
    'text': '#1f2937',
    'text_secondary': '#6b7280',
    'text_tertiary': '#9ca3af',
    'brand': '#4f46e5',
    'brand_hover': '#4338ca',
    'brand_soft': '#eef2ff',
    'danger': '#ef4444',
    'danger_hover': '#dc2626',
    'danger_soft': '#fee2e2',
    'success': '#10b981',
    'success_soft': '#ecfdf5',
    'border': '#e5e7eb',
    'shadow': '#e5e7eb',
    'dialog_bg': '#e5e7eb',
}

# 中文字体
FONT = ('Microsoft YaHei', 13)
FONT_TITLE = ('Microsoft YaHei', 17, 'bold')
FONT_SUBTITLE = ('Microsoft YaHei', 12)
FONT_SMALL = ('Microsoft YaHei', 11)
FONT_CAPTION = ('Microsoft YaHei', 13, 'bold')
FONT_MONO = ('Consolas', 12)


class SmoothSwitch(ctk.CTkFrame):
    """自定义 Canvas 开关，支持平滑 200ms 位移动画。"""

    def __init__(self, master, command=None, initial=False, width=50,
                 height=26, bg_color=COLORS['surface'], **kwargs):
        super().__init__(
            master, width=width, height=height,
            fg_color='transparent', **kwargs,
        )
        self.pack_propagate(False)
        self.width = width
        self.height = height
        self.command = command
        self.state = bool(initial)
        self.animating = False
        self.bg_color = bg_color

        self.canvas = tk.Canvas(
            self, width=width, height=height,
            highlightthickness=0, bg=bg_color,
        )
        self.canvas.pack()

        self.canvas.bind('<Button-1>', self._on_click)
        self.bind('<Button-1>', self._on_click)

        self._redraw(1.0 if self.state else 0.0)

    @staticmethod
    def _hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def _blend(self, color1, color2, t):
        r1, g1, b1 = self._hex_to_rgb(color1)
        r2, g2, b2 = self._hex_to_rgb(color2)
        return (
            int(r2 + (r1 - r2) * t),
            int(g2 + (g1 - g2) * t),
            int(b2 + (b1 - b2) * t),
        )

    def _redraw(self, progress):
        self.canvas.delete('all')
        h = self.height
        w = self.width
        radius = h // 2

        on_color = COLORS['brand']
        off_color = COLORS['border']
        r, g, b = self._blend(on_color, off_color, progress)
        track_color = f'#{r:02x}{g:02x}{b:02x}'

        # 轨道（左右半圆 + 中间矩形），使用整数坐标
        self.canvas.create_oval(0, 0, h, h, fill=track_color, outline='')
        self.canvas.create_oval(w - h, 0, w, h, fill=track_color, outline='')
        self.canvas.create_rectangle(
            radius, 0, w - radius, h, fill=track_color, outline='',
        )

        # 滑块
        knob_radius = radius - 3
        start_x = radius
        end_x = w - radius
        knob_x = int(start_x + (end_x - start_x) * progress)
        self.canvas.create_oval(
            knob_x - knob_radius, radius - knob_radius,
            knob_x + knob_radius, radius + knob_radius,
            fill='white', outline='',
        )

    def _on_click(self, event=None):
        self.toggle()

    def toggle(self):
        self.state = not self.state
        self._animate()
        if self.command:
            self.command()

    def _animate(self):
        if self.animating:
            return
        self.animating = True
        start = 0.0 if self.state else 1.0
        end = 1.0 if self.state else 0.0
        steps = 10
        duration = 120
        step_time = duration // steps
        delta = (end - start) / steps

        def step(i):
            if i > steps:
                self.animating = False
                self._redraw(end)
                return
            self._redraw(start + delta * i)
            self.after(step_time, lambda: step(i + 1))
        step(0)

    def get(self):
        return self.state

    def select(self):
        if not self.state:
            self.state = True
            self._animate()

    def deselect(self):
        if self.state:
            self.state = False
            self._animate()


class MainWindow:
    """基于 customtkinter 的现代卡片式主界面。"""

    def __init__(self, app):
        self.app = app
        self.icon = None
        self._images = {}

        ctk.set_appearance_mode('light')
        self._build_window()
        self._build_title_bar()
        self._build_source_card()
        self._build_two_col_card()
        self._build_action_bar()
        self._build_toggles_card()
        self._build_log_card()
        self._build_footer()
        self._build_tray()
        self._render()

        if app.auto_start:
            self.window.after(1000, self._on_start)

    # ---------- 通用容器 ----------

    def _card(self, parent):
        """白色圆角卡片，内部预留 12px 内边距。"""
        container = ctk.CTkFrame(
            parent, fg_color=COLORS['surface'], corner_radius=14,
            border_width=1, border_color=COLORS['border'],
        )
        card = ctk.CTkFrame(container, fg_color='transparent')
        card.pack(fill=ctk.BOTH, expand=True, padx=12, pady=12)
        return container, card

    def _section_title(self, parent, text, icon=None, icon_size=12):
        frame = ctk.CTkFrame(parent, fg_color='transparent', height=20)
        frame.pack_propagate(False)
        x_offset = 0
        if icon:
            icon_lbl = ctk.CTkLabel(
                frame, text=icon, font=('Microsoft YaHei', icon_size, 'bold'),
                text_color=COLORS['brand'], fg_color='transparent',
            )
            icon_lbl.place(x=0, rely=0.5, anchor=ctk.W)
            x_offset = icon_size + 10
        text_lbl = ctk.CTkLabel(
            frame, text=text, font=FONT_CAPTION,
            text_color=COLORS['text'], fg_color='transparent',
        )
        text_lbl.place(x=x_offset, rely=0.5, anchor=ctk.W)
        frame.text_label = text_lbl
        return frame

    # ---------- 窗口 ----------

    def _build_window(self):
        # 临时窗口获取屏幕分辨率并计算缩放，避免主窗口创建后闪烁
        temp = tk.Tk()
        sw = temp.winfo_screenwidth()
        sh = temp.winfo_screenheight()
        temp.destroy()

        base_h = 1440
        design_w, design_h = 540, 1120
        scale = sh / base_h
        self._scale = max(0.7, min(scale, 2.0))
        ctk.set_window_scaling(self._scale)
        ctk.set_widget_scaling(self._scale)
        self._win_width = design_w
        self._win_height = design_h
        self._frame_pad_x = 20
        self._frame_pad_y = 40

        self.window = ctk.CTk()
        self.window.title(tr(self.app.state.language, '窗口名称'))

        # 路径3：无边框窗口 + 透明色裁角，实现整体圆角
        self._transparent_color = '#010101'
        self.window.overrideredirect(True)
        self.window.configure(fg_color=self._transparent_color)
        self.window.wm_attributes('-transparentcolor', self._transparent_color)

        # 直接定位到屏幕中心
        x = (sw - self._win_width) // 2
        y = (sh - self._win_height) // 2 if self._win_height <= sh else 20
        self.window.geometry(f'{self._win_width}x{self._win_height}+{x}+{y}')
        # 等所有控件创建完成后再整体显示，避免元素逐个出现
        self.window.attributes('-alpha', 0.0)

        try:
            self.window.iconbitmap(os.path.join(app_path(), 'tmp.ico'))
        except Exception:
            pass

        # 主容器使用透明色，让窗口四角完全透明；真正可见区域交给居中的圆角 main_frame
        self.main_container = ctk.CTkFrame(
            self.window, fg_color=self._transparent_color, corner_radius=0,
            border_width=0,
        )
        self.main_container.pack(fill=ctk.BOTH, expand=True)

        self.main_frame = ctk.CTkFrame(
            self.main_container, fg_color=COLORS['bg'], corner_radius=14,
            border_width=0,
        )
        self.main_frame.pack_propagate(False)
        self.main_frame.pack(
            fill=ctk.BOTH, expand=True,
            padx=self._frame_pad_x // 2, pady=self._frame_pad_y // 2,
        )

    # ---------- 标题栏 ----------

    def _build_title_bar(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color='transparent', height=48)
        frame.pack(fill=ctk.X, padx=20, pady=(12, 14))
        frame.pack_propagate(False)

        self.title_label = ctk.CTkLabel(
            frame, text='', font=FONT_TITLE, text_color=COLORS['text'],
            fg_color='transparent',
        )
        self.title_label.place(x=0, rely=0.5, anchor='w')

        self.status_pill = ctk.CTkLabel(
            frame, text='', font=FONT_SMALL, fg_color=COLORS['success_soft'],
            text_color=COLORS['success'], corner_radius=999,
            padx=12, pady=5,
        )
        self.status_pill.place(x=135, rely=0.5, anchor='w')

        # 自绘最小化 / 关闭按钮
        btn_frame = ctk.CTkFrame(frame, fg_color='transparent', width=66, height=28)
        btn_frame.place(relx=1.0, rely=0.5, anchor='e')

        min_btn = ctk.CTkButton(
            btn_frame, text='−', width=28, height=28,
            command=self._minimize_window,
            fg_color='transparent', hover_color=COLORS['surface_muted'],
            text_color=COLORS['text'], font=('Microsoft YaHei', 16),
            corner_radius=6,
        )
        min_btn.pack(side=ctk.LEFT, padx=(0, 6))

        close_btn = ctk.CTkButton(
            btn_frame, text='×', width=28, height=28,
            command=self.window.withdraw,
            fg_color='transparent', hover_color=COLORS['danger_soft'],
            text_color=COLORS['text'], font=('Microsoft YaHei', 16),
            corner_radius=6,
        )
        close_btn.pack(side=ctk.LEFT)

        # 标题栏拖动支持
        for widget in (frame, self.title_label, self.status_pill):
            widget.bind('<Button-1>', self._start_move)
            widget.bind('<B1-Motion>', self._on_move)

    def _minimize_window(self):
        try:
            self.window.state('iconic')
        except Exception:
            self.window.withdraw()

    def _start_move(self, event):
        self._drag_x = event.x_root - self.window.winfo_x()
        self._drag_y = event.y_root - self.window.winfo_y()

    def _on_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.window.geometry(f'+{x}+{y}')

    def _load_icon(self):
        # 标题栏图标已移除，此方法保留但不再调用
        pass

    # ---------- 图源卡片 ----------

    def _build_source_card(self):
        container, card = self._card(self.main_frame)
        container.pack(fill=ctk.X, padx=20, pady=(0, 8))

        self.source_title = self._section_title(card, '', icon='🛰')
        self.source_title.pack(anchor=ctk.W, pady=(0, 10))

        self.source_var = ctk.StringVar(value=self.app.state.image_source)
        self.source_hints = {
            '风云4B': '风云4B范围',
            'GOES-East': 'GOES-East范围',
            'GOES-West': 'GOES-West范围',
        }
        self.source_radios = []
        self.source_radio_frames = []
        self.source_radio_inners = []
        self.source_hint_labels = []
        for key in SOURCES:
            radio_frame = ctk.CTkFrame(
                card, fg_color=COLORS['surface'], corner_radius=10,
                border_width=1, border_color=COLORS['border'],
            )
            radio_frame.pack(fill=ctk.X, pady=(0, 6))
            self.source_radio_frames.append(radio_frame)

            inner = ctk.CTkFrame(
                radio_frame, fg_color=COLORS['surface'], corner_radius=8,
            )
            inner.pack(fill=ctk.BOTH, expand=True, padx=8, pady=3)
            self.source_radio_inners.append(inner)

            left_group = ctk.CTkFrame(inner, fg_color='transparent')
            left_group.pack(side=ctk.LEFT)

            radio = ctk.CTkRadioButton(
                left_group, variable=self.source_var, value=key,
                text='', font=FONT, width=18, height=18,
                fg_color=COLORS['brand'], border_color=COLORS['text_tertiary'],
                hover_color=COLORS['brand_hover'], radiobutton_width=18,
                radiobutton_height=18,
            )
            radio.pack(side=ctk.LEFT)
            self.source_radios.append(radio)

            lbl = ctk.CTkLabel(
                left_group, text=tr(self.app.state.language, key),
                font=FONT, text_color=COLORS['text'], fg_color='transparent',
            )
            lbl.pack(side=ctk.LEFT, padx=(8, 0))
            radio.text_label = lbl

            hint = ctk.CTkLabel(
                inner, text=tr(self.app.state.language, self.source_hints[key]),
                font=FONT_SMALL, text_color=COLORS['text_tertiary'],
                fg_color='transparent',
            )
            hint.pack(side=ctk.RIGHT)
            self.source_hint_labels.append(hint)

        self.source_var.trace_add('write', self._on_source_changed)
        self._refresh_radio_frames(
            self.source_radio_frames, self.source_radio_inners,
            self.source_radios, self.source_var,
        )

    def _refresh_radio_frames(self, frames, inners, radios, variable):
        # 仅由 CTkRadioButton 自身处理小圆点选中状态，
        # 不额外改变卡片边框和背景颜色。
        pass

    # ---------- 双列设置卡片 ----------

    def _build_two_col_card(self):
        row = ctk.CTkFrame(self.main_frame, fg_color='transparent')
        row.pack(fill=ctk.X, padx=20, pady=(0, 8))
        row.grid_columnconfigure(0, weight=1, uniform='col')
        row.grid_columnconfigure(1, weight=1, uniform='col')

        self._build_scale_card(row, 0)
        self._build_freq_path_card(row, 1)

    def _build_scale_card(self, parent, column):
        container, card = self._card(parent)
        container.grid(row=0, column=column, sticky='nsew', padx=(0, 6))

        self.scale_title = self._section_title(card, '', icon='▣', icon_size=18)
        self.scale_title.pack(anchor=ctk.W, pady=(0, 10))

        self.scale_var = ctk.StringVar(value=self.app.state.scale_mode)
        self.scale_radios = []
        self.scale_radio_frames = []
        self.scale_radio_inners = []
        for key in SCALE_MODES:
            radio_frame = ctk.CTkFrame(
                card, fg_color=COLORS['surface'], corner_radius=10,
                border_width=1, border_color=COLORS['border'],
            )
            radio_frame.pack(fill=ctk.X, pady=(0, 6))
            self.scale_radio_frames.append(radio_frame)

            inner = ctk.CTkFrame(
                radio_frame, fg_color=COLORS['surface'], corner_radius=8,
            )
            inner.pack(fill=ctk.BOTH, expand=True, padx=8, pady=3)
            self.scale_radio_inners.append(inner)

            left_group = ctk.CTkFrame(inner, fg_color='transparent')
            left_group.pack(side=ctk.LEFT)

            radio = ctk.CTkRadioButton(
                left_group, variable=self.scale_var, value=key,
                text='', font=FONT, width=18, height=18,
                fg_color=COLORS['brand'], border_color=COLORS['text_tertiary'],
                hover_color=COLORS['brand_hover'], radiobutton_width=18,
                radiobutton_height=18,
            )
            radio.pack(side=ctk.LEFT)
            self.scale_radios.append(radio)

            lbl = ctk.CTkLabel(
                left_group, text=tr(self.app.state.language, key),
                font=FONT, text_color=COLORS['text'], fg_color='transparent',
            )
            lbl.pack(side=ctk.LEFT, padx=(8, 0))
            radio.text_label = lbl

        self.scale_var.trace_add('write', self._on_scale_changed)
        self._refresh_radio_frames(
            self.scale_radio_frames, self.scale_radio_inners,
            self.scale_radios, self.scale_var,
        )

    def _build_freq_path_card(self, parent, column):
        container, card = self._card(parent)
        container.grid(row=0, column=column, sticky='nsew', padx=(6, 0))

        # 更新频率
        self.freq_title = self._section_title(card, '', icon='◷', icon_size=18)
        self.freq_title.pack(anchor=ctk.W, pady=(0, 8))

        freq_row = ctk.CTkFrame(card, fg_color='transparent')
        freq_row.pack(fill=ctk.X, pady=(0, 16))

        self.interval_var = ctk.StringVar(value=str(self.app.state.interval_minutes))
        self.interval_entry = ctk.CTkEntry(
            freq_row, textvariable=self.interval_var, width=56, justify='center',
            font=FONT, fg_color=COLORS['surface_muted'], text_color=COLORS['text'],
            border_color=COLORS['border'], border_width=1, corner_radius=8,
        )
        self.interval_entry.pack(side=ctk.LEFT, padx=(0, 8))

        self.freq_unit = ctk.CTkLabel(
            freq_row, text='', font=FONT, text_color=COLORS['text_secondary'],
            fg_color='transparent',
        )
        self.freq_unit.pack(side=ctk.LEFT)

        # 保存位置
        self.path_title = self._section_title(card, '', icon='▤', icon_size=18)
        self.path_title.pack(anchor=ctk.W, pady=(0, 8))

        path_row = ctk.CTkFrame(card, fg_color='transparent')
        path_row.pack(fill=ctk.X)

        self.save_path_var = ctk.StringVar(value=self.app.state.save_path)
        self.path_display = ctk.CTkEntry(
            path_row, textvariable=self.save_path_var, state='readonly',
            font=FONT_SMALL, fg_color=COLORS['surface_muted'],
            text_color=COLORS['text_secondary'], border_color=COLORS['border'],
            border_width=1, corner_radius=8,
        )
        self.path_display.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=(0, 8))

        self.browse_btn = ctk.CTkButton(
            path_row, text='', command=self._on_browse, font=FONT,
            fg_color=COLORS['surface_muted'], hover_color=COLORS['border'],
            text_color=COLORS['text'], corner_radius=8,
            border_width=1, border_color=COLORS['border'],
            width=70, height=32,
        )
        self.browse_btn.pack(side=ctk.RIGHT)

    # ---------- 操作按钮 ----------

    def _build_action_bar(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color='transparent')
        frame.pack(fill=ctk.X, padx=20, pady=(0, 8))
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        self.start_btn = ctk.CTkButton(
            frame, text='', command=self._on_start, font=FONT,
            fg_color=COLORS['brand'], hover_color=COLORS['brand_hover'],
            text_color='white', corner_radius=12, height=42,
        )
        self.start_btn.grid(row=0, column=0, sticky='ew', padx=(0, 6))

        self.exit_btn = ctk.CTkButton(
            frame, text='', command=self._on_exit, font=FONT,
            fg_color=COLORS['danger_soft'], hover_color='#fecaca',
            text_color='#dc2626', corner_radius=12, height=42,
        )
        self.exit_btn.grid(row=0, column=1, sticky='ew', padx=(6, 0))

    # ---------- 开关与语言卡片 ----------

    def _build_toggles_card(self):
        container, card = self._card(self.main_frame)
        container.pack(fill=ctk.X, padx=20, pady=(0, 8))

        # 时间水印
        self.water_row, self.water_switch = self._toggle_row(
            card, '时间水印', '时间水印描述',
            self.app.state.watermark_on, self._on_watermark,
        )
        self.water_row.pack(fill=ctk.X, pady=(0, 4))

        sep1 = tk.Frame(card, height=1, bg='#d1d5db')
        sep1.pack(fill=ctk.X, pady=12)

        # 开机自启
        self.auto_row, self.auto_switch = self._toggle_row(
            card, '开机自启', '开机自启描述',
            autostart.is_enabled(), self._on_auto_start,
        )
        self.auto_row.pack(fill=ctk.X, pady=(0, 4))

        sep2 = tk.Frame(card, height=1, bg='#d1d5db')
        sep2.pack(fill=ctk.X, pady=12)

        # 界面语言
        self.lang_row = ctk.CTkFrame(card, fg_color='transparent')
        self.lang_row.pack(fill=ctk.X, pady=(4, 0))

        lang_left = ctk.CTkFrame(self.lang_row, fg_color='transparent')
        lang_left.pack(side=ctk.LEFT)
        self.lang_title = ctk.CTkLabel(
            lang_left, text='', font=FONT_CAPTION, text_color=COLORS['text'],
            fg_color='transparent',
        )
        self.lang_title.pack(anchor=ctk.W)
        self.lang_desc = ctk.CTkLabel(
            lang_left, text='', font=FONT_SMALL,
            text_color=COLORS['text_tertiary'], fg_color='transparent',
        )
        self.lang_desc.pack(anchor=ctk.W)

        self.lang_var = ctk.StringVar(value=self.app.state.language)

        lang_frame = ctk.CTkFrame(
            self.lang_row, fg_color=COLORS['surface'], corner_radius=8,
            border_width=1, border_color=COLORS['border'],
        )
        lang_frame.pack(side=ctk.RIGHT)

        self.lang_combo = ctk.CTkOptionMenu(
            lang_frame, values=list(LANGUAGES), variable=self.lang_var,
            command=self._on_language_changed, font=FONT,
            fg_color=COLORS['surface'], text_color=COLORS['text'],
            button_color=COLORS['surface_muted'], button_hover_color=COLORS['border'],
            dropdown_fg_color=COLORS['surface'], dropdown_text_color=COLORS['text'],
            dropdown_hover_color=COLORS['brand_soft'], dropdown_font=FONT,
            corner_radius=8, width=120, height=30,
        )
        self.lang_combo.pack(padx=1, pady=1)

    def _toggle_row(self, parent, title_key, desc_key, initial, command):
        row = ctk.CTkFrame(parent, fg_color='transparent', height=44)
        row.pack(fill=ctk.X)
        row.pack_propagate(False)

        left = ctk.CTkFrame(row, fg_color='transparent')
        left.place(relx=0, rely=0.5, anchor=ctk.W)

        title_label = ctk.CTkLabel(
            left, text='', font=FONT_CAPTION, text_color=COLORS['text'],
            fg_color='transparent',
        )
        title_label.pack(anchor=ctk.W)
        desc_label = ctk.CTkLabel(
            left, text='', font=FONT_SMALL,
            text_color=COLORS['text_tertiary'], fg_color='transparent',
        )
        desc_label.pack(anchor=ctk.W)

        switch = SmoothSwitch(
            row, command=command, initial=initial,
            width=int(50 * self._scale), height=int(26 * self._scale),
            bg_color=COLORS['surface'],
        )
        switch.place(relx=1.0, rely=0.5, anchor=ctk.E)

        row.title_label = title_label
        row.desc_label = desc_label
        return row, switch

    # ---------- 日志 ----------

    def _build_log_card(self):
        container, card = self._card(self.main_frame)
        container.pack(fill=ctk.BOTH, expand=True, padx=20, pady=(0, 8))

        header = ctk.CTkFrame(card, fg_color='transparent')
        header.pack(fill=ctk.X, pady=(0, 8))

        self.log_title = self._section_title(header, '')
        self.log_title.pack(side=ctk.LEFT)

        self.log_clear = ctk.CTkLabel(
            header, text='', font=FONT_SMALL, text_color=COLORS['text_tertiary'],
            fg_color='transparent', cursor='hand2',
        )
        self.log_clear.pack(side=ctk.RIGHT)
        self.log_clear.bind('<Button-1>', self._on_clear_log)

        self.log_text = ctk.CTkTextbox(
            card, height=150, font=FONT_MONO,
            fg_color=COLORS['surface_muted'], text_color=COLORS['text_secondary'],
            border_color=COLORS['border'], border_width=1, corner_radius=10,
            wrap='word', state='disabled',
        )
        self.log_text.pack(fill=ctk.BOTH, expand=True)

    # ---------- 底部提示 ----------

    def _build_footer(self):
        self.footer_hint = ctk.CTkLabel(
            self.main_frame, text='', font=FONT_SMALL,
            text_color=COLORS['text_tertiary'], fg_color='transparent',
        )
        self.footer_hint.pack(padx=20, pady=(0, 12))

    # ---------- 托盘 ----------

    def _build_tray(self):
        lang = self.app.state.language
        menu = pystray.Menu(
            pystray.MenuItem(tr(lang, '显示'), self._show_window, default=True),
            pystray.MenuItem(tr(lang, '退出'), self._on_tray_quit),
        )
        try:
            image = Image.open(os.path.join(app_path(), 'tmp.ico'))
        except Exception:
            image = Image.new('RGB', (64, 64), COLORS['brand'])
        self.icon = pystray.Icon(
            'current_earth_wallpaper', image,
            tr(lang, '窗口名称'), menu,
        )
        threading.Thread(target=self.icon.run, daemon=True).start()

    # ---------- 渲染 ----------

    def _render(self):
        lang = self.app.state.language

        self.window.title(tr(lang, '窗口名称'))
        self.title_label.configure(text=tr(lang, '窗口名称'))

        status_key = '运行中' if self.app.scheduler.is_running() else '已停止'
        fg = COLORS['success_soft'] if self.app.scheduler.is_running() else COLORS['surface_muted']
        text = COLORS['success'] if self.app.scheduler.is_running() else COLORS['text_tertiary']
        self.status_pill.configure(
            text=tr(lang, status_key), fg_color=fg, text_color=text,
        )

        self.source_title.text_label.configure(text=tr(lang, '选择图像源'))
        for radio, key in zip(self.source_radios, SOURCES):
            if hasattr(radio, 'text_label'):
                radio.text_label.configure(text=tr(lang, key))
        for key, hint_lbl in zip(SOURCES, self.source_hint_labels):
            hint_lbl.configure(text=tr(lang, self.source_hints[key]))
        self._refresh_radio_frames(
            self.source_radio_frames, self.source_radio_inners,
            self.source_radios, self.source_var,
        )

        self.scale_title.text_label.configure(text=tr(lang, '壁纸比例'))
        for radio, key in zip(self.scale_radios, SCALE_MODES):
            if hasattr(radio, 'text_label'):
                radio.text_label.configure(text=tr(lang, key))
        self._refresh_radio_frames(
            self.scale_radio_frames, self.scale_radio_inners,
            self.scale_radios, self.scale_var,
        )

        self.freq_title.text_label.configure(text=tr(lang, '更新频率'))
        self.freq_unit.configure(text=tr(lang, '分钟/张'))
        self.path_title.text_label.configure(text=tr(lang, '保存位置'))
        self.browse_btn.configure(text=tr(lang, '浏览'))

        self.start_btn.configure(text=tr(lang, '开始更新'))
        self.exit_btn.configure(text=tr(lang, '退出程序'))

        self.water_row.title_label.configure(text=tr(lang, '时间水印'))
        self.water_row.desc_label.configure(text=tr(lang, '时间水印描述'))
        self.auto_row.title_label.configure(text=tr(lang, '开机自启'))
        self.auto_row.desc_label.configure(text=tr(lang, '开机自启描述'))

        self.lang_title.configure(text=tr(lang, '界面语言'))
        self.lang_desc.configure(text=tr(lang, '界面语言描述'))

        self.log_title.text_label.configure(text=tr(lang, '运行日志'))
        self.log_clear.configure(text=tr(lang, '清空'))
        self.footer_hint.configure(text=tr(lang, '托盘提示'))

        if self.icon is not None:
            self.icon.title = tr(lang, '窗口名称')
            self.icon.menu = pystray.Menu(
                pystray.MenuItem(tr(lang, '显示'), self._show_window, default=True),
                pystray.MenuItem(tr(lang, '退出'), self._on_tray_quit),
            )
            self.icon.update_menu()

    # ---------- 事件处理 ----------

    def _on_language_changed(self, *_args):
        self.app.state.language = self.lang_var.get()
        self._render()

    def _on_source_changed(self, *_args):
        self.app.state.image_source = self.source_var.get()
        self._refresh_radio_frames(
            self.source_radio_frames, self.source_radio_inners,
            self.source_radios, self.source_var,
        )

    def _on_scale_changed(self, *_args):
        self.app.state.scale_mode = self.scale_var.get()
        self._refresh_radio_frames(
            self.scale_radio_frames, self.scale_radio_inners,
            self.scale_radios, self.scale_var,
        )

    def _on_browse(self):
        selected = ctk.filedialog.askdirectory()
        if selected:
            self.app.state.save_path = selected + '\\'
            self.save_path_var.set(self.app.state.save_path)

    def _on_watermark(self):
        self.app.state.watermark_on = bool(self.water_switch.get())

    def _on_auto_start(self):
        value = bool(self.auto_switch.get())
        lang = self.app.state.language
        try:
            autostart.set_enabled(value)
        except OSError as e:
            self._show_auto_start_error(value, f"{tr(lang, '自启失败提示')}\n{e}")
            return
        if autostart.is_enabled() == value:
            key = '自启开启提示' if value else '自启取消提示'
            self._show_info(tr(lang, '窗口名称'), tr(lang, key))
        else:
            self._show_auto_start_error(value, tr(lang, '自启失败提示'))

    def _show_auto_start_error(self, value, msg):
        lang = self.app.state.language
        self._show_error(msg)
        # 回退开关状态，避免触发递归（通过 set 不触发 command）
        if value:
            self.auto_switch.deselect()
        else:
            self.auto_switch.select()

    def _on_start(self):
        try:
            minutes = int(float(self.interval_var.get().strip()))
        except ValueError:
            minutes = 0
        if minutes <= 0:
            self._show_error(tr(self.app.state.language, '频率提示'))
            return
        self.app.state.interval_minutes = minutes
        error_key = self.app.start()
        if error_key:
            self._show_error(tr(self.app.state.language, error_key))
        self._render()

    def _center_popup(self, popup, width, height):
        self.window.update_idletasks()
        px = self.window.winfo_x() + (self.window.winfo_width() - width) // 2
        py = self.window.winfo_y() + (self.window.winfo_height() - height) // 2
        popup.geometry(f'{width}x{height}+{px}+{py}')

    def _message_dialog(self, title, msg, buttons='ok'):
        dialog = ctk.CTkToplevel(self.window)
        dialog.title(title)
        # 弹窗同样使用无边框 + 透明色裁角实现圆角
        dialog.overrideredirect(True)
        dialog.configure(fg_color=COLORS['bg'])
        # 把弹窗背景色设为透明，只露出中间的圆角灰色卡片
        dialog.wm_attributes('-transparentcolor', COLORS['bg'])
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.resizable(False, False)

        try:
            dialog.iconbitmap(os.path.join(app_path(), 'tmp.ico'))
        except Exception:
            pass

        dialog_width, dialog_height = 380, 190
        self._center_popup(dialog, dialog_width, dialog_height)

        frame = ctk.CTkFrame(
            dialog, fg_color=COLORS['dialog_bg'], corner_radius=14,
            border_width=1, border_color=COLORS['border'],
        )
        frame.pack_propagate(False)
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        title_lbl = ctk.CTkLabel(
            frame, text=title, font=FONT_TITLE, text_color=COLORS['text'],
            fg_color='transparent',
        )
        title_lbl.pack(pady=(24, 8))

        msg_lbl = ctk.CTkLabel(
            frame, text=msg, font=FONT, text_color=COLORS['text'],
            wraplength=320, fg_color='transparent',
        )
        msg_lbl.pack(padx=20, pady=(0, 20))

        btn_frame = ctk.CTkFrame(frame, fg_color='transparent')
        btn_frame.pack(fill=ctk.X, padx=20, pady=(0, 20))

        result = [None]

        def on_ok():
            result[0] = True
            try:
                dialog.grab_release()
            except Exception:
                pass
            dialog.destroy()

        def on_cancel():
            result[0] = False
            try:
                dialog.grab_release()
            except Exception:
                pass
            dialog.destroy()

        lang = self.app.state.language
        if buttons == 'okcancel':
            cancel_btn = ctk.CTkButton(
                btn_frame, text=tr(lang, '取消'), command=on_cancel,
                fg_color=COLORS['surface_muted'], text_color=COLORS['text'],
                hover_color=COLORS['border'], corner_radius=8, width=80, height=32,
            )
            cancel_btn.pack(side=ctk.RIGHT, padx=(8, 0))

        ok_btn = ctk.CTkButton(
            btn_frame, text=tr(lang, '确定'), command=on_ok,
            fg_color=COLORS['brand'], text_color='white',
            hover_color=COLORS['brand_hover'], corner_radius=8, width=80, height=32,
        )
        ok_btn.pack(side=ctk.RIGHT)

        self.window.wait_window(dialog)
        # 弹窗关闭后把焦点还给主窗口，避免输入框无法获得光标
        try:
            self.window.focus_force()
        except Exception:
            pass
        return result[0]

    def _show_error(self, msg):
        self._message_dialog(tr(self.app.state.language, '错误'), msg)

    def _show_info(self, title, msg):
        self._message_dialog(title, msg)

    def _on_exit(self):
        lang = self.app.state.language
        if self._message_dialog(tr(lang, '退出'), tr(lang, '退出提示'), buttons='okcancel'):
            self._do_shutdown()

    def _on_tray_quit(self):
        self.app.request_shutdown()

    def _show_window(self):
        self.window.deiconify()

    def _on_clear_log(self, _event=None):
        self.log_text.configure(state='normal')
        self.log_text.delete('0.0', ctk.END)
        self.log_text.configure(state='disabled')

    # ---------- 主线程轮询 ----------

    def _poll(self):
        self.app.logbus.flush(self._append_log)
        if self.app.scheduler.is_running():
            self.status_pill.configure(
                text=tr(self.app.state.language, '运行中'),
                fg_color=COLORS['success_soft'], text_color=COLORS['success'],
            )
        else:
            self.status_pill.configure(
                text=tr(self.app.state.language, '已停止'),
                fg_color=COLORS['surface_muted'], text_color=COLORS['text_tertiary'],
            )
        if self.app.shutdown_requested:
            self._do_shutdown()
            return
        self.window.after(POLL_INTERVAL, self._poll)

    def _append_log(self, text):
        self.log_text.configure(state='normal')
        self.log_text.insert(ctk.END, text)
        self.log_text.see(ctk.END)
        self.log_text.configure(state='disabled')

    def _do_shutdown(self):
        self._sync_interval()
        self.app.prepare_exit()
        try:
            if self.icon is not None:
                self.icon.stop()
        except Exception:
            pass
        self.window.destroy()

    def _sync_interval(self):
        try:
            minutes = int(float(self.interval_var.get().strip()))
            if minutes > 0:
                self.app.state.interval_minutes = minutes
        except ValueError:
            pass

    # ---------- 窗口居中与主循环 ----------

    def run(self):
        # 所有控件已创建完成，整体显示窗口
        self.window.attributes('-alpha', 1.0)
        clear_MEI(self.app.log)
        self.window.after(POLL_INTERVAL, self._poll)
        self.window.mainloop()
