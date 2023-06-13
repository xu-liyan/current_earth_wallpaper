#使用PIL.Image库，处理指定图片，并设置为桌面壁纸


import ctypes
import PIL
from PIL import Image, ImageDraw, ImageGrab
import mss

global screen_width, screen_height
# 创建一个mss对象，获取显示器的分辨率
with mss.mss() as sct:
    # 获取所有显示器的信息
    monitors = sct.monitors
    # 获取第一个显示器的信息
    monitor = monitors[0]
    # 获取第一个显示器的宽度和高度
    screen_width = monitor["width"]
    screen_height = monitor["height"]

# 定义一个更改壁纸的函数，接受一个图片路径作为参数
def changeBG(imagePath):
    # 设置一个常量，表示更改壁纸的操作
    SPI_SETDESKWALLPAPER = 20
    # 调用ctypes模块的windll属性，使用SystemParametersInfoW函数更改壁纸
    # 第一个参数是操作码，第二个参数是保留值，第三个参数是图片路径，第四个参数是更新选项
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, imagePath, 3)
    print('Wallpaper set successful')
    # 返回None
    return None


# 定义一个处理图片的函数，接受一个图片路径作为参数
def resize_image(imagePath , folder_path , name_pic , current_url , flag):
    # 使用PIL模块的Image类打开图片
    image = PIL.Image.open(imagePath)
    # 获取图片的原始宽度和高度
    width, height = image.size
    # 获取显示器的分辨率
    #screen_width, screen_height = PIL.ImageGrab.grab().size
    # 计算缩放比例，取宽度和高度中较小的值
    ratio = min(screen_width / width, screen_height / height)
    # 计算新的宽度和高度，保持原始图片的纵横比
    new_width = int(width * ratio)
    new_height = int(height * ratio)
    # 使用PIL模块的Image类的resize方法调整图片大小
    # 第一个参数是新的宽度和高度的元组，第二个参数是缩放算法
    resized_image = image.resize((new_width, new_height), PIL.Image.LANCZOS)
    img = resized_image
    print('Image resized successful')

    # 将图片先裁剪为方形，再裁剪为圆形（如果直接裁剪为圆形，很容易因为图片计算过程过程中四舍五入，导致创建的画布大小和图片大小不匹配而报错
    #将图片裁剪为方形
    if current_url == 'FY4A':
        FY4_s, FY4_x, FY4_y = 2170 * ratio, 15 * ratio, 15 * ratio
    elif current_url == 'FY4B':
        FY4_s, FY4_x, FY4_y = 10835 * ratio, 65 * ratio, 80 * ratio

    box=(FY4_x, FY4_y, FY4_s+FY4_x, FY4_s+FY4_y)
    img = img.crop(box)
    width, height = img.size

    #将图片裁剪为圆形
    mask = Image.new('L', (width, height), 0) # 创建一个透明背景的画布
    draw = ImageDraw.Draw(mask) # 创建一个绘图对象
    draw.ellipse((0, 0, FY4_s, FY4_s), fill=255) # 绘制一个白色的圆形
    img.putalpha(mask) # 将圆形作为透明度掩码
    print('Image redraw successful')

    #设置缩放比
    if flag == 0:
        ratio = screen_height / img.height          #原始图片缩放至屏幕分辨率，裁剪后调整至屏幕高度大小 ‘铺满屏幕’
    elif flag == 1:
        ratio = 1                                   #原始图片缩放至屏幕分辨率，裁剪后的 ‘原始大小’
    elif flag == 2:
        ratio = screen_height / img.height * 0.618  #原始图片缩放至屏幕分辨率，裁剪后调整至屏幕高度的 ‘0.618黄金比’
    elif flag == 3:
        ratio = screen_height / img.height * 0.45   #原始图片缩放至屏幕分辨率，裁剪后调整至屏幕高度的 ‘0.45倍’
    
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

    resized_image_path = folder_path + "resize_" + name_pic + ".jpg"
    resized_image.save(resized_image_path)
    print('Wallpaper generate successful')
    # 返回调整后的图片路径
    return resized_image_path


# 调用changeBG函数，传入wallpaper变量作为参数
def changewall(image_path , folder_path , name_pic , current_url , flag):
    path = resize_image(image_path , folder_path , name_pic , current_url , flag)
    changeBG(path)
