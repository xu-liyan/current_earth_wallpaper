'''
1、启动程序之后，从网址“http://img.nsmc.org.cn/CLOUDIMAGE/FY4A/MTCC/FY4A_DISK.JPG”或
“http://img.nsmc.org.cn/CLOUDIMAGE/FY4B/AGRI/GCLR/FY4B_DISK_GCLR.JPG”获取图片，并保存到指定文件夹，图片名称以获取图片的具体日期和时间命名
2、可以自行选择从哪个网址获取图片
3、每隔xx分钟获取一张图片，并根据当前显示屏分辨率，将图片设置为桌面背景
4、文件夹图片最大保存数量为96张，超过之后从最旧的文件开始依次删除，最终保留96张图片
5、GUI窗口关闭后，程序最小化到托盘运行
'''
#增加图片缩放和裁剪处理，更换壁纸设置方式

import os
import ctypes
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
import auto_wallpaper_V2

# 设置下载图片的网址
IMAGE_URLS = {
    'FY4A': 'http://img.nsmc.org.cn/CLOUDIMAGE/FY4A/MTCC/FY4A_DISK.JPG',
    'FY4B': 'http://img.nsmc.org.cn/CLOUDIMAGE/FY4B/AGRI/GCLR/FY4B_DISK_GCLR.JPG',
}

# 设置壁纸缩放比例
scale = {
    '铺满屏幕': 0 ,
    '原始大小': 1 ,
    '黄金比例': 2 ,
    '更小尺寸': 3 ,
}

class DesktopBackgroundChanger:
    def __init__(self, interval=30*60): #默认30 min 拉取一次图片
        self.interval = interval
        self.timer = None
        self.image_urls = IMAGE_URLS
        self.current_image_url = self.image_urls['FY4A']
        self.scale = scale
        self.current_image_scale = self.scale['黄金比例']
        self.save_path = ''
        self.create_gui()


    def create_gui(self):
        # 实现关闭窗口后，程序隐藏到托盘运行
        # 定义退出函数，关闭托盘图标和tk窗口
        def quit_window(icon: pystray.Icon):
            icon.stop()
            self.window.destroy()
            # 结束程序
            sys.exit()

        # 定义显示函数，恢复tk窗口
        def show_window():
            self.window.deiconify()

        # 定义托盘图标的右键菜单，可以添加更多的选项和回调函数
        menu = (
            MenuItem('显示', show_window, default=True),
            MenuItem('退出', quit_window),
        )

        # 定义附加文件的路径
        def get_resource_path(relative_path):
            # 获取附加文件的绝对路径
            try:
                # PyInstaller 创建一个临时文件夹并将路径存储在 _MEIPASS 中
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")

            return os.path.join(base_path, relative_path)

        # 加载图标文件，可以使用自己的图标
        image = Image.open(get_resource_path('tmp.ico'))

        # 创建托盘图标对象，设置图标、名称和菜单
        icon = pystray.Icon("icon", image, "实时地球", menu)

        self.window = tk.Tk()
        self.window.title('实时地球')
        # 定义窗口图标
        self.window.iconbitmap(get_resource_path('tmp.ico'))

        # 开启一个守护线程来运行托盘图标，防止阻塞tk的事件循环
        threading.Thread(target=icon.run, daemon=True).start()

        # 创建关闭按钮的处理
        self.window.protocol('WM_DELETE_WINDOW', lambda: self.window.withdraw())

        # 定义一个函数，用于停止程序，并关闭gui界面
        def exit():
            # 弹出一个确认框，询问用户是否要退出
            if messagebox.askokcancel("退出", "确定要停止程序并退出吗？"):
                # 如果用户点击确定，就销毁主窗口，并结束程序
                icon.stop()
                self.window.destroy()
                # 结束程序
                sys.exit()

        # 图像源选项
        source_frame = ttk.LabelFrame(self.window, text='选择图像源：')

        self.current_url_var = tk.StringVar(value='FY4A')
        for url_key in self.image_urls.keys():
            ttk.Radiobutton(source_frame, text=url_key, value=url_key, variable=self.current_url_var, command=self.update_image_url).pack(anchor=tk.W)

        source_frame.pack(fill=tk.X, padx=10, pady=10)

        # 壁纸缩放比例选项
        scale_frame = ttk.LabelFrame(self.window, text='选择壁纸比例：')

        self.current_scale_var = tk.StringVar(value='黄金比例')
        for scale_key in self.scale.keys():
            ttk.Radiobutton(scale_frame, text=scale_key, value=scale_key, variable=self.current_scale_var, command=self.scale_flag).pack(anchor=tk.W)

        scale_frame.pack(fill=tk.X, padx=10, pady=10)

        # 文件夹选择器
        folder_frame = ttk.Frame(self.window)
        folder_label = ttk.Label(folder_frame, text='选择图像保存位置：')
        folder_label.pack(side=tk.LEFT)
        folder_entry = ttk.Entry(folder_frame, state='readonly')
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        folder_entry.insert(0, 'Select folder')
        folder_button = ttk.Button(folder_frame, text='浏览', command=lambda: self.set_save_path(folder_entry))
        folder_button.pack(side=tk.RIGHT)
        folder_frame.pack(fill=tk.X, padx=10, pady=10)
        self.save_path_var = folder_entry

        # 时间间隔设置
        interval_frame = ttk.Frame(self.window)
        interval_label = ttk.Label(interval_frame, text='图像获取频率')
        interval_label.pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value='30')   #默认30 min 拉取一次图片
        interval_entry = ttk.Entry(interval_frame, width=5, textvariable=self.interval_var)
        interval_entry.pack(side=tk.LEFT, padx=(0, 5))
        interval_unit = ttk.Label(interval_frame, text='分钟/张')
        interval_unit.pack(side=tk.LEFT)
        interval_frame.pack(anchor=tk.W, padx=10, pady=10)

        # 开始和退出按钮
        start_button = ttk.Button(self.window, text='开始', command=self.start)
        exit_button = ttk.Button(self.window, text='退出', command=exit)
        start_button.pack()
        exit_button.pack()

        self.window.mainloop()

    def update_image_url(self):
        self.current_image_url = self.image_urls[self.current_url_var.get()]
        if self.current_image_url == IMAGE_URLS['FY4A'] :
            current_url = 'FY4A'
        elif self.current_image_url == IMAGE_URLS['FY4B'] :
            current_url = 'FY4B'
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
        auto_wallpaper_V2.changewall(latest_file_path , folder_path , name_pic , current_url , flag)
        

    def download_image(self):
        # 下载图片并保存到指定文件夹
        print('url = ' , self.update_image_url())
        print('download begin')
        response = requests.get(self.current_image_url)
        with open(self.save_path + datetime.now().strftime('%Y%m%d_%H%M%S') + '.jpg', 'wb') as f:
            f.write(response.content)
            #time.sleep(5)
            print('download end')

        # # 统计文件数量并删除最早保存的一张图片
        # files = os.listdir(self.save_path)
        # if len(files) > 48:
        #     oldest_file = min(files, key=lambda x: os.path.getctime(self.save_path+x))
        #     os.remove(self.save_path+oldest_file)

        # 统计文件数量,并删除超过48张的最早保存的图片
        files = os.listdir(self.save_path)
        if len(files) > 95:
            # 对文件名按照创建时间排序，最新的在前面
            files.sort(key=lambda x: os.path.getctime(self.save_path+x), reverse=True)
            # 计算超过48个的文件数量
            excess = len(files) - 95
            # 删除所有超过48个的文件
            for file in files[95:]:
                os.remove(self.save_path+file)
            # 打印删除了多少个文件
            print(f"Deleted {excess} oldest files from {self.save_path}")

    def set_desktop_background_and_schedule_next_change(self):
        self.download_image()
        self.set_desktop_background()
        self.timer = threading.Timer(float(self.interval_var.get()) * 60, self.set_desktop_background_and_schedule_next_change)
        self.timer.start()

    def start(self):
        if self.save_path:
            # 启动定时器
            self.set_desktop_background_and_schedule_next_change()
        else:
            # 如果未选择保存路径，则弹出错误提示框
            error_box = tk.Toplevel(self.window)
            error_box.title('Error')
            error_label = ttk.Label(error_box, text='请选择一个文件夹，以保存壁纸 ！')
            error_label.pack()
            ok_button = ttk.Button(error_box, text='确定', command=error_box.destroy)
            ok_button.pack()


# T1 = time.perf_counter()  

# T2 =time.perf_counter()
# print('程序运行时间:%s毫秒' % ((T2 - T1)*1000))


if __name__ == '__main__':
    DesktopBackgroundChanger()
