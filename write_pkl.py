import os
import pickle

def save():
            # 创建一个字典，存放输入框中的内容
            writedata = {
                "current_url": '风云4A',
                "current_scale": '黄金比例',
                "save_path": '',
                "interval_var": '30',
                "water_button": '添加时间水印',
                'language': '中文',
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
            with open("wallpaperdata.pkl", "wb") as f:
                # 用pickle模块将字典保存到文件中
                pickle.dump(writedata, f)

save()