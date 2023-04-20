#使用PIL.Image库，处理指定图片，并设置为桌面壁纸


import ctypes
import PIL
from PIL import Image, ImageDraw, ImageGrab, ImageOps
import tempfile
import os
import time

T1 = time.perf_counter()

# 定义一个更改壁纸的函数，接受一个图片路径作为参数
def changeBG(imagePath):
    # 设置一个常量，表示更改壁纸的操作
    SPI_SETDESKWALLPAPER = 20
    # 调用ctypes模块的windll属性，使用SystemParametersInfoW函数更改壁纸
    # 第一个参数是操作码，第二个参数是保留值，第三个参数是图片路径，第四个参数是更新选项
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, imagePath, 3)
    # 返回None
    return None


# 定义一个处理图片的函数，接受一个图片路径作为参数
def resize_image(imagePath , flag = 2):
    # 使用PIL模块的Image类打开图片
    image = PIL.Image.open(imagePath)
    # 获取图片的原始宽度和高度
    width, height = image.size
    # 获取显示器的分辨率
    screen_width, screen_height = PIL.ImageGrab.grab().size
    # 计算缩放比例，取宽度和高度中较小的值
    ratio = min(screen_width / width, screen_height / height)
    # 计算新的宽度和高度，保持原始图片的纵横比
    new_width = int(width * ratio)
    new_height = int(height * ratio)
    # 使用PIL模块的Image类的resize方法调整图片大小
    # 第一个参数是新的宽度和高度的元组，第二个参数是缩放算法
    resized_image = image.resize((new_width, new_height), PIL.Image.LANCZOS)
    img = resized_image

    # 将图片先裁剪为方形，再裁剪为圆形（如果直接裁剪为圆形，很容易因为图片计算过程过程中四舍五入，导致创建的画布大小和图片大小不匹配而报错
    #将图片裁剪为方形
    #FY4B_s, FY4B_x, FY4B_y = 2198, 60, 80
    FY4B_s, FY4B_x, FY4B_y = 10835 * ratio, 65 * ratio, 80 * ratio
    box=(FY4B_x, FY4B_y, FY4B_s+FY4B_x, FY4B_s+FY4B_y)
    img = img.crop(box)
    width, height = img.size
    img.save("C:\\Users\\XXXX\\XXXX.jpg")


    #将图片裁剪为圆形
    mask = Image.new('L', (width, height), 0) # 创建一个透明背景的画布
    draw = ImageDraw.Draw(mask) # 创建一个绘图对象
    draw.ellipse((0, 0, FY4B_s, FY4B_s), fill=255) # 绘制一个白色的圆形
    img.putalpha(mask) # 将圆形作为透明度掩码
    #resized_image = img
    img.save("C:\\Users\\XXXX\\XXXX02.png")

    #设置缩放比
    if flag == 0:
        ratio = screen_height / img.height
    elif flag == 1:
        ratio = 1
    elif flag == 2:
        ratio = screen_height / img.height * 0.618
    elif flag == 3:
        ratio = screen_height / img.height * 0.45
    
    new_width = int(img.width * ratio)
    new_height = int(img.height * ratio)
    resized_image = img.resize((new_width, new_height), PIL.Image.LANCZOS)

    # 扩展壁纸到电脑显示器大小
    # 注意图片模式：RGB为3x8位像素，真彩；RGBA为4x8位像素，带透明蒙版的真彩；RGBA无法保存为jpg格式
    bk_image = Image.new("RGB", (screen_width, screen_height) , (0,0,0))
    sw, sh = bk_image.size
    ew, eh = resized_image.size
    bk_image.paste(resized_image, (int((sw - ew) / 2), int((sh - eh) / 2)), mask = resized_image)
    resized_image = bk_image
    # 返回调整后的图片对象
    return resized_image

# 定义一个变量，存储你想要的壁纸图片的路径
# 可以根据自己的需要修改这个路径
wallpaper = "C:\\Users\\XXXX\\XXXX.jpg"

# 调用resize_image函数，传入image_path变量作为参数
# 得到返回的图片对象，并赋值给resized_image变量
resized_image = resize_image(wallpaper , 2)

resized_image_path = "C:\\Users\\XXXX\\XXXX.jpg"
resized_image.save(resized_image_path)
#time.sleep(1)   #延时1s，等待图片保存成功

# 调用changeBG函数，传入wallpaper变量作为参数
changeBG(resized_image_path)

T2 =time.perf_counter()
print('程序运行时间:%s毫秒' % ((T2 - T1)*1000))
