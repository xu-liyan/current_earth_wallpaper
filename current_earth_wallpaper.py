'''
1、启动程序之后，从网址“http://img.nsmc.org.cn/CLOUDIMAGE/FY4A/MTCC/FY4A_DISK.JPG”或
“http://img.nsmc.org.cn/CLOUDIMAGE/FY4B/AGRI/GCLR/FY4B_DISK_GCLR.JPG”获取图片，并保存到指定文件夹，图片名称以获取图片的具体日期和时间命名
2、可以自行选择从哪个网址获取图片
3、每隔xx分钟获取一张图片，并根据当前显示屏分辨率，将图片设置为桌面背景
4、文件夹图片最大保存数量为96张，超过之后从最旧的文件开始依次删除，最终保留96张图片
5、GUI窗口关闭后，程序最小化到托盘运行
6、多语言版本（中文，English）
'''

import os
import requests
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import pystray
from pystray import MenuItem
from PIL import Image
import sys
import pickle
import winreg
import io
import tkinter.scrolledtext as st
import _tkinter
import shutil
import auto_wallpaper_V6

global loaddata

# 设置下载图片的网址
IMAGE_URLS = {
    '风云4A': 'http://img.nsmc.org.cn/CLOUDIMAGE/FY4A/MTCC/FY4A_DISK.JPG',
    '风云4B': 'http://img.nsmc.org.cn/CLOUDIMAGE/FY4B/AGRI/GCLR/FY4B_DISK_GCLR.JPG',
}

# 设置壁纸缩放比例
scale = {
    '铺满屏幕': 0 ,
    '原始大小': 1 ,
    '黄金比例': 2 ,
    '更小尺寸': 3 ,
}

# 定义app_path()函数，返回exe文件的运行路径
def app_path():
    if hasattr(sys, 'frozen'):  # frozen属性是在使用pyinstaller打包exe文件时添加的，表示程序是被打包过的
        # os.path.dirname()用于获取一个文件路径的目录部分
        # sys.executable是一个变量，表示当前运行的程序文件的完整路径；在没有打包的情况下，它指向Python解释器
        # 在打包后的情况下，它指向exe文件本身。所以，如果你想加载和exe文件同一目录下的资源文件，你可以使用sys.executable来获取它们的绝对路径。
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(__file__) # 没打包，就返回当前运行的py文件的完整路径
    
def clear_MEI():
    # 获取 Temp 文件夹的路径
    temp_path = os.environ["TEMP"]

    # 遍历 Temp 文件夹中的所有文件和文件夹
    for item in os.listdir(temp_path):
        # 获取完整的路径
        item_path = os.path.join(temp_path, item)
        # 判断是否是文件夹
        if os.path.isdir(item_path):
            # 尝试删除文件夹，如果出错则跳过
            try:
                shutil.rmtree(item_path)
                print("Clear: %s - %s." % (item_path, item))
            except OSError as e:
                print("Skip: %s - %s." % (e.filename, e.strerror))


class DesktopBackgroundChanger:
    run_times = 0
    timers = [] # 创建一个空列表来存储定时器对象
    self_start_flag = 0
    watermark_flag = 0
    water_time = 1

    # 获取快捷方式中传入的参数，用以判断是否自动开始图片更新
    if len(sys.argv) > 1:
        self_start_flag = int(sys.argv[1])

    def __init__(self, interval=30*60): #默认30 min 拉取一次图片
        self.interval = interval
        self.timer = None
        self.image_urls = IMAGE_URLS
        self.current_image_url = self.image_urls['风云4A']
        self.scale = scale
        self.current_image_scale = self.scale['黄金比例']
        self.save_path = ''
        self.create_gui()


    def create_gui(self):

        # 打开配置文件，用二进制读取模式
        with open(os.path.join(app_path(), "wallpaperdata.pkl"), "rb") as f:
            # 用pickle模块将文件中的内容加载为一个字典
            loaddata = pickle.load(f)

        self.window = tk.Tk()

        # 创建一个字符串变量，用于存储选择的语言
        lang_var = tk.StringVar()
        # 设置默认值为中文
        lang_var.set('中文')

        # 创建一个下拉框对象，用于显示不同语言的选项
        combo_lang = ttk.Combobox(self.window, textvariable=lang_var, state='readonly', width=9)
        # 设置下拉框的选项列表
        combo_lang['values'] = ('中文', 'English')
        # 设置下拉框的默认值
        combo_lang.set(loaddata["language"])
        # 为下拉框添加一个回调函数，用于调用切换语言函数
        combo_lang.bind('<<ComboboxSelected>>', lambda event: switch_language())

        # 定义一个函数，用于切换语言
        def switch_language():
            # 获取选择的语言
            lang = combo_lang.get()
            # 更新语言
            self.window.title(loaddata[lang]['窗口名称'])

            source_frame.config(text=loaddata[lang]['选择图像源'])
            # 遍历所有的图像源Radiobutton控件，根据当前语言设置它们的文本
            for i, url_key in enumerate(self.image_urls.keys()):
                self.radios[i].config(text=loaddata[lang][url_key])

            scale_frame.config(text=loaddata[lang]['选择壁纸比例'])
            # 遍历所有的壁纸比例Radiobutton控件，根据当前语言设置它们的文本
            for j, scale_key in enumerate(self.scale.keys()):
                self.radios2[j].config(text=loaddata[lang][scale_key])

            folder_label.config(text=loaddata[lang]['选择图像保存位置'])
            folder_button.config(text=loaddata[lang]['浏览'])
            interval_label.config(text=loaddata[lang]['图像获取频率'])
            interval_unit.config(text=loaddata[lang]['分钟/张'])
            start_button.config(text=loaddata[lang]['开始'])
            exit_button.config(text=loaddata[lang]['退出'])

            if DesktopBackgroundChanger.watermark_flag == 0 :
                water_button.config(text=loaddata[lang]['添加时间水印'])
            else:
                water_button.config(text=loaddata[lang]['取消时间水印'])
            
            button_auto_start.config(text=read_auto_start())
            log_frame.config(text=loaddata[lang]['运行日志'])

            icon.title = loaddata[lang]['窗口名称']
            update_menu()
            

        self.window.title(loaddata[lang_var.get()]['窗口名称'])
        # 定义窗口图标
        # self.window.iconbitmap(get_resource_path('tmp.ico'))
        self.window.iconbitmap(os.path.join(app_path(), 'tmp.ico'))
        # self.window.iconbitmap('tmp.ico')
        # 创建关闭按钮的处理
        self.window.protocol('WM_DELETE_WINDOW', lambda: self.window.withdraw())

        # 实现关闭窗口后，程序隐藏到托盘运行
        # 定义退出函数：取消定时器线程、关闭tk窗口、关闭托盘图标、结束程序
        def quit_window(icon:pystray.Icon):
            # 保存输入框中的配置内容、取消定时器线程、关闭托盘图标、销毁主窗口、并结束程序
            save()
            print('times = ' , DesktopBackgroundChanger.timers)
            # 遍历列表，取消所有正在运行的定时器
            for self.timer in DesktopBackgroundChanger.timers:
                self.timer.cancel()
            self.window.destroy()
            icon.stop()
            sys.exit()

        # 定义显示函数，恢复tk窗口
        def show_window():
            self.window.deiconify()

        # 定义托盘图标的右键菜单，可以添加更多的选项和回调函数
        menu = (
            MenuItem(loaddata[lang_var.get()]['显示'], show_window, default=True),
            MenuItem(loaddata[lang_var.get()]['退出'], quit_window),
        )

        # 定义附加文件的路径 打包成exe时，必须将 “tmp.ico” 添加为附加文件 ！！
        # def get_resource_path(relative_path):
        #     # 获取附加文件的绝对路径
        #     try:
        #         # PyInstaller 创建一个临时文件夹并将路径存储在 _MEIPASS 中
        #         # sys._MEIPASS是在使用pyinstaller打包exe文件时添加的一个属性，它指向exe文件解压后的临时文件夹
        #         base_path = sys._MEIPASS
        #     except Exception:
        #         base_path = os.path.abspath(".")
        #     return os.path.join(base_path, relative_path)

        
        # 加载图标文件，可以使用自己的图标
        # image = Image.open(get_resource_path('tmp.ico'))
        image = Image.open(os.path.join(app_path(), 'tmp.ico'))
        # image = Image.open('tmp.ico')

        # 创建托盘图标对象，设置图标、名称和菜单
        icon = pystray.Icon("icon", image, loaddata[lang_var.get()]['窗口名称'], menu)

        # 开启一个守护线程来运行托盘图标，防止阻塞tk的事件循环
        threading.Thread(target=icon.run, daemon=True).start()

        def update_menu():
            menu = icon.menu
            new_menu = list(menu)
            new_menu[0] = pystray.MenuItem(loaddata[combo_lang.get()]['显示'], show_window, default=True)
            new_menu[1] = pystray.MenuItem(loaddata[combo_lang.get()]['退出'], quit_window)
            icon.menu = pystray.Menu(*new_menu)
            icon.update_menu()

        # 图像源选项
        source_frame = ttk.LabelFrame(self.window, text=loaddata[lang_var.get()]['选择图像源'])
        self.current_url_var = tk.StringVar()
        # 创建一个列表，用于存放Radiobutton控件
        self.radios = []
        for url_key in self.image_urls.keys():
            radio = ttk.Radiobutton(source_frame, text=url_key, value=url_key, variable=self.current_url_var, command=self.update_image_url)
            radio.pack(anchor=tk.W)
            # 将Radiobutton控件添加到列表中
            self.radios.append(radio)
        source_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 壁纸缩放比例选项
        scale_frame = ttk.LabelFrame(self.window, text=loaddata[lang_var.get()]['选择壁纸比例'])
        self.current_scale_var = tk.StringVar()
        # 创建一个列表，用于存放Radiobutton控件
        self.radios2 = []
        for scale_key in self.scale.keys():
            radio2 = ttk.Radiobutton(scale_frame, text=scale_key, value=scale_key, variable=self.current_scale_var, command=self.scale_flag)
            radio2.pack(anchor=tk.W)
            # 将Radiobutton控件添加到列表中
            self.radios2.append(radio2)  
        scale_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 文件夹选择器
        folder_frame = ttk.Frame(self.window)
        folder_label = ttk.Label(folder_frame, text=loaddata[lang_var.get()]['选择图像保存位置'])
        folder_label.pack(side=tk.LEFT)
        self.save_path_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.save_path_var, state='readonly')
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        folder_entry.insert(0, 'Select folder')
        folder_button = ttk.Button(folder_frame, text=loaddata[lang_var.get()]['浏览'], command=lambda: self.set_save_path(folder_entry))
        folder_button.pack(side=tk.RIGHT)
        folder_frame.pack(fill=tk.X, padx=10, pady=10)

        # 时间间隔设置
        interval_frame = ttk.Frame(self.window)
        interval_label = ttk.Label(interval_frame, text=loaddata[lang_var.get()]['图像获取频率'])
        interval_label.pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value='30')   #默认30 min 拉取一次图片
        interval_entry = ttk.Entry(interval_frame, width=5, textvariable=self.interval_var)
        interval_entry.pack(side=tk.LEFT, padx=(0, 5))
        interval_unit = ttk.Label(interval_frame, text=loaddata[lang_var.get()]['分钟/张'])
        interval_unit.pack(side=tk.LEFT)
        interval_frame.pack(anchor=tk.W, padx=10, pady=10)


        # 创建一个函数，用于保存输入框中的内容到一个文件中
        def save():
            # 创建一个字典，存放输入框中的内容和语言信息
            writedata = {
                "current_url": self.current_url_var.get(),
                "current_scale": self.current_scale_var.get(),
                "save_path": self.save_path_var.get(),
                "interval_var": self.interval_var.get(),
                "water_button": water_button.cget("text"),
                'language': combo_lang.get(),
                '中文': {
                    '窗口名称': '实时地球',
                    '选择图像源': '选择图像源',
                    '风云4A': '风云4A',
                    '风云4B': '风云4B',
                    '选择壁纸比例': '选择壁纸比例',
                    '铺满屏幕': '铺满屏幕',
                    '原始大小': '原始大小',
                    '黄金比例': '黄金比例',
                    '更小尺寸': '更小尺寸',
                    '选择图像保存位置': '选择图像保存位置：',
                    '浏览': '浏览',
                    '图像获取频率': '图像获取频率',
                    '分钟/张': '分钟/张',
                    '开始': '开始',
                    '退出': '退出',
                    '添加时间水印': '添加时间水印',
                    '取消时间水印': '取消时间水印',
                    '设为开机自启': '设为开机自启',
                    '取消开机自启': '取消开机自启',
                    '运行日志': '运行日志',
                    '显示': '显示',
                    '保存提示': '请选择一个文件夹，以保存壁纸 ！',
                    '确定': '确定',
                    '退出提示': '确定要停止程序并退出吗？',
                    '错误': '错误'
                },
                'English': {
                    '窗口名称': 'Current Earth',
                    '选择图像源': 'Select image source',
                    '风云4A': 'FY4A',
                    '风云4B': 'FY4B',
                    '选择壁纸比例': 'Select wallpaper ratio',
                    '铺满屏幕': 'Fill Screen',
                    '原始大小': 'Original Size',
                    '黄金比例': 'Golden Size',
                    '更小尺寸': 'Smaller Size',
                    '选择图像保存位置': 'Select location to save the image:',
                    '浏览': 'Browse',
                    '图像获取频率': 'Image capture frequency',
                    '分钟/张': 'Min/PCS',
                    '开始': 'Start',
                    '退出': 'Quit',
                    '添加时间水印': 'Add time watermark',
                    '取消时间水印': 'Cancel time watermark',
                    '设为开机自启': 'Set auto start at boot',
                    '取消开机自启': 'Cancel auto start at boot',
                    '运行日志': 'Run Log',
                    '显示': 'Display',
                    '保存提示': 'Please select a folder to save wallpapers !',
                    '确定': 'Sure',
                    '退出提示': 'Are you sure you want to stop the program and exit ?',
                    '错误': 'Error'
                }
            }
            # 打开一个文件，用二进制写入模式
            with open(os.path.join(app_path(), "wallpaperdata.pkl"), "wb") as f:
                # 用pickle模块将字典保存到文件中
                pickle.dump(writedata, f)

        # 创建一个函数，用于从一个文件中读取输入框中的内容
        def load():
            # 将字典中的内容设置到输入框中
            self.current_url_var.set(loaddata["current_url"])
            self.current_scale_var.set(loaddata["current_scale"])
            self.save_path_var.set(loaddata["save_path"])
            self.interval_var.set(loaddata["interval_var"])
            water_button.config(text=loaddata["water_button"])

           
        # 定义一个函数，读取开机自启动状态
        def read_auto_start():
            # 获取当前程序的路径和文件名
            exe_path = os.path.abspath(sys.argv[0])
            exe_name = os.path.basename(exe_path)
            # 获取注册表中的Run键
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_ALL_ACCESS)
            try:
                # 尝试读取当前程序的值，如果存在，说明已经设置了开机自启
                value, _ = winreg.QueryValueEx(key, exe_name)
                auto_start_flag = loaddata[lang_var.get()]['取消开机自启']
            except FileNotFoundError:
                # 如果不存在，说明没有设置开机自启
                auto_start_flag = loaddata[lang_var.get()]['设为开机自启']
            return auto_start_flag
        
        # 定义一个函数，用于设置开机自启动
        def set_auto_start():
            # 获取当前程序的路径和文件名
            exe_path = os.path.abspath(sys.argv[0])
            exe_name = os.path.basename(exe_path)
            # 获取注册表中的Run键
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_ALL_ACCESS)
            try:
                # 尝试读取当前程序的值，如果存在，说明已经设置了开机自启动
                value, _ = winreg.QueryValueEx(key, exe_name)
                # 删除当前程序的值，取消开机自启动
                winreg.DeleteValue(key, exe_name)
                # 在按钮上显示设置开机自启动
                button_auto_start.config(text=loaddata[combo_lang.get()]['设为开机自启'])
            except FileNotFoundError:
                # 如果不存在，说明没有设置开机自启动
                # 写入当前程序的值，设置开机自启动，并传入1作为参数
                value = f'"{exe_path}" {1}'
                winreg.SetValueEx(key, exe_name, 0, winreg.REG_SZ, value)
                # 在按钮上显示取消开机自启动
                button_auto_start.config(text=loaddata[combo_lang.get()]['取消开机自启'])
            finally:
                # 关闭注册表键
                winreg.CloseKey(key)

        def watermark():
            text = water_button.cget("text")
            if DesktopBackgroundChanger.water_time == 1:
                if text == loaddata[combo_lang.get()]['添加时间水印'] :
                    DesktopBackgroundChanger.watermark_flag = 0
                elif text == loaddata[combo_lang.get()]['取消时间水印'] :
                    DesktopBackgroundChanger.watermark_flag = 1
            else:
                if text == loaddata[combo_lang.get()]['添加时间水印'] :
                    DesktopBackgroundChanger.watermark_flag = 1
                    water_button.config(text=loaddata[combo_lang.get()]['取消时间水印'])
                elif text == loaddata[combo_lang.get()]['取消时间水印'] :
                    DesktopBackgroundChanger.watermark_flag = 0
                    water_button.config(text=loaddata[combo_lang.get()]['添加时间水印'])

        # 定义一个函数，用于开始程序
        def start():
            if self.save_path_var.get() != "" :
                # 保存输入框中的配置内容
                save()
                # 遍历列表，取消所有正在运行的定时器
                for self.timer in DesktopBackgroundChanger.timers:
                    self.timer.cancel()
                time.sleep(0.01)
                self.set_desktop_background_and_schedule_next_change()
            else:
                # 如果未选择保存路径，则弹出错误提示框
                error_box = tk.Toplevel(self.window)
                error_box.title(loaddata[combo_lang.get()]['错误'])
                error_label = ttk.Label(error_box, text=loaddata[lang_var.get()]['保存提示'])
                error_label.pack()
                ok_button = ttk.Button(error_box, text=loaddata[lang_var.get()]['确定'], command=error_box.destroy)
                ok_button.pack()

        # 定义一个函数，用于停止程序，并关闭gui界面
        def diy_exit():
            # 弹出一个确认框，询问用户是否要退出
            if messagebox.askokcancel(loaddata[lang_var.get()]['退出'], loaddata[lang_var.get()]['退出提示']):
                # 如果用户点击确定：保存输入框中的配置内容、取消定时器线程、关闭托盘图标、销毁主窗口、并结束程序
                save()
                # 遍历列表，取消所有正在运行的定时器
                print('times = ' , DesktopBackgroundChanger.timers)
                for self.timer in DesktopBackgroundChanger.timers:
                    self.timer.cancel()
                icon.stop()
                self.window.destroy()
                print('exit successful')
                sys.exit()

        # 定义一个函数，实现窗口居中
        def center_window(window):
            # 更新窗口的状态
            window.update_idletasks()
            # 获取窗口的宽度和高度
            window_width = window.winfo_width()
            window_height = window.winfo_height()
            # 获取屏幕的宽度和高度
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            # 计算居中的位置
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            # 设置窗口的位置
            window.geometry(f'{window_width}x{window_height}+{x}+{y}')


        # 开始、退出、时间水印、开机自启动按钮
        auto_start_flag = read_auto_start()
        start_button = ttk.Button(self.window, text=loaddata[lang_var.get()]['开始'], command=start)
        exit_button = ttk.Button(self.window, text=loaddata[lang_var.get()]['退出'], command=diy_exit)
        button_auto_start = ttk.Button(self.window, text=auto_start_flag, command=set_auto_start)
        water_button = ttk.Button(self.window, text='时间水印', command=watermark)
        start_button.pack()
        exit_button.pack()
        water_button.pack()
        button_auto_start.pack()
        # 将语言选择下拉框放置
        combo_lang.pack()

        # 在主界面的右侧创建一个日志显示界面
        log_frame = ttk.LabelFrame(self.window, text=loaddata[lang_var.get()]['运行日志'])
        # 创建一个带有垂直滚动条的文本控件
        log_text = st.ScrolledText(log_frame, width=40, height=20)
        # 布置文本控件
        log_text.pack(fill="both", expand="yes")
        # 创建一个 TextRedirector 的实例，传入 log_text 作为参数
        redirector = TextRedirector(log_text)
        # 将 sys.stdout 和 sys.stderr 重定向到 redirector
        sys.stdout = redirector
        sys.stderr = redirector
        # 布置日志框架
        log_frame.pack(side=tk.TOP, fill="both", expand="yes")

        load() # 加载默认配置
        watermark()
        switch_language()
        DesktopBackgroundChanger.water_time = 0
        self.save_path = self.save_path_var.get()

        # 如果快捷方式中传入的参数为 1 ，说明用户设置了开机自启动，自动开始更新图片的主进程
        if DesktopBackgroundChanger.self_start_flag == 1 :
            self.window.after(1000, start)   # 1000毫秒后调用该函数，可以解决打开程序时窗口严重卡顿问题

        # 调用窗口居中函数
        center_window(self.window)

        # 删除 Temp 文件夹中的所有文件夹
        clear_MEI()

        self.window.mainloop()


    def update_image_url(self):
        self.current_image_url = self.image_urls[self.current_url_var.get()]
        if self.current_image_url == IMAGE_URLS['风云4A'] :
            current_url = '风云4A'
        elif self.current_image_url == IMAGE_URLS['风云4B'] :
            current_url = '风云4B'
        return current_url
    
    def scale_flag(self):
        self.current_image_scale = self.scale[self.current_scale_var.get()]
        flag = self.current_image_scale
        return flag

    def set_save_path(self, entry):
        selected_path = filedialog.askdirectory()
        if selected_path:
            self.save_path = selected_path + '\\'
            entry.configure(state='normal')
            entry.delete(0, tk.END)
            entry.insert(0, self.save_path)
            entry.configure(state='readonly')

    # 调用自定义模块，更换桌面壁纸
    def set_desktop_background(self):
        # 获取文件夹中所有文件的路径和修改时间
        folder_path = self.save_path
        files = [(os.path.join(folder_path, file), os.path.getmtime(os.path.join(folder_path, file))) for file in os.listdir(folder_path)]
        # 按照修改时间降序排序
        files.sort(key=lambda x: x[1], reverse=True)
        # 第一个元素，即最新文件的路径
        latest_file_path = files[0][0]
        # 使用os.path.basename()函数，获取最新文件的名称
        latest_file_name = os.path.basename(latest_file_path)
        # 使用os.path.splitext()函数，获取最新文件的名称不含后缀
        latest_file_name_without_extension = os.path.splitext(latest_file_name)[0]
        name_pic = latest_file_name_without_extension
        current_url = self.update_image_url()
        flag = self.scale_flag()
        watermark_flag = DesktopBackgroundChanger.watermark_flag
        auto_wallpaper_V6.changewall(latest_file_path , folder_path , name_pic , current_url , flag , watermark_flag)
        

    def download_image(self):
        # 下载图片并保存到指定文件夹
        print('Time: ' , datetime.now().strftime('%Y%m%d_%H%M%S'))
        print('URL: ' , self.update_image_url())
        print('Image download begin')
        try:
            # 使用本地证书文件
            CERT_PATH = os.path.join(app_path(), "certs", "cacert.pem")
            # CA证书加载检查
            if os.path.exists(CERT_PATH):
               print('CA证书加载成功') 
            if not os.path.exists(CERT_PATH):
                raise FileNotFoundError(f"CA证书不存在: {CERT_PATH}")
            response = requests.get(self.current_image_url, verify=CERT_PATH)
            with open(self.save_path + datetime.now().strftime('%Y%m%d_%H%M%S') + '.jpg', 'wb') as f:
                f.write(response.content)
                print('Image download end')

            # # 统计文件数量并删除最早保存的一张图片
            # files = os.listdir(self.save_path)
            # if len(files) > 48:
            #     oldest_file = min(files, key=lambda x: os.path.getctime(self.save_path+x))
            #     os.remove(self.save_path+oldest_file)

            # 统计文件数量,并删除超过96张的最早保存的图片
            files = os.listdir(self.save_path)
            if len(files) > 95:
                # 对文件名按照创建时间排序，最新的在前面
                files.sort(key=lambda x: os.path.getctime(self.save_path+x), reverse=True)
                # 计算超过96个的文件数量
                excess = len(files) - 95
                # 删除所有超过96个的文件
                for file in files[95:]:
                    os.remove(self.save_path+file)
                # 打印删除了多少个文件
                print(f"Deleted {excess} oldest files from {self.save_path}")
        except requests.exceptions.RequestException as e:
            # 处理图片下载异常或失败
            print('Image download failed')
            return # 跳出当前函数

    def set_desktop_background_and_schedule_next_change(self):
        # 遍历列表，检查每个定时器是否还在运行
        for self.timer in DesktopBackgroundChanger.timers:
            # 如果定时器已经取消或者到期，就从列表中删除它
            if not self.timer.is_alive():
                DesktopBackgroundChanger.timers.remove(self.timer)

        self.download_image()
        self.set_desktop_background()
        DesktopBackgroundChanger.run_times = DesktopBackgroundChanger.run_times + 1
        print('Run_times = ' , DesktopBackgroundChanger.run_times)
        print(end='\n')
        self.timer = threading.Timer(float(self.interval_var.get()) * 60, self.set_desktop_background_and_schedule_next_change)
        self.timer.start()
        DesktopBackgroundChanger.timers.append(self.timer)  #把定时器对象加入到列表中
        
class TextRedirector(io.TextIOBase):
    # 初始化方法，接收一个文本控件作为参数
    def __init__(self, text_widget):
        # 调用父类的初始化方法
        super().__init__()
        # 保存文本控件的引用
        self.text_widget = text_widget

    # 重写 write 方法，接收一个字符串作为参数
    def write(self, s):
        # 尝试将字符串插入到文本控件的末尾
        try:
            self.text_widget.insert(tk.END, s)
            # 更新文本控件
            self.text_widget.update()
            # 将字符串追加到日志文件中
            # with open("log.txt", "a") as f:
            with open(os.path.join(app_path(), "log.txt"), "a") as f:
                f.write(s)
            # 返回字符串的长度
            return len(s)
        # 如果发生 TclError 异常，打印错误信息并返回 0
        except _tkinter.TclError as e:
            # print(e)
            return 0


# T1 = time.perf_counter()  

# T2 =time.perf_counter()
# print('程序运行时间:%s毫秒' % ((T2 - T1)*1000))


if __name__ == '__main__':
    DesktopBackgroundChanger()
