#使用PIL.Image库，处理指定图片，并设置为桌面壁纸

import ctypes
import PIL
from PIL import Image, ImageDraw, ImageFont, ImageGrab, ImageFile
import mss
import datetime
# from io import BytesIO

global screen_width, screen_height, watermark_x, watermark_y, watermark_font
# 创建一个mss对象，获取显示器的分辨率
with mss.mss() as sct:
    # 获取所有显示器的信息
    monitors = sct.monitors
    # 获取第一个显示器的信息
    monitor = monitors[0]
    # 获取第一个显示器的宽度和高度
    screen_width = monitor["width"]
    screen_height = monitor["height"]

# 计算时间水印位置坐标
watermark_font = PIL.ImageFont.truetype("arial.ttf", int(screen_height / 60)) # 根据屏幕高度设置字体大小
text = datetime.datetime.now().strftime("%Y/%m/%d  %H:%M:%S") # 获取当前时间
text_width, text_height = watermark_font.getsize(text) # 获取文字的宽度和高度
margin = int(screen_height / 24) # 设置边距
watermark_x = screen_width - text_width - margin/2 # 计算文字的横坐标
watermark_y = screen_height - text_height - margin # 计算文字的纵坐标


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
def resize_image(imagePath , folder_path , name_pic , current_image_source , flag , watermark_flag):

    print('Wallpaper generate begin')

    # 设置更高的像素限制
    Image.MAX_IMAGE_PIXELS = 700000000  # 7亿像素

    try:
        # 使用PIL模块的Image类打开图片
        image = PIL.Image.open(imagePath)
    except PIL.UnidentifiedImageError as e:
        # 处理图片打开异常或失败
        print('！！Image open failed')
        # 跳出当前函数
        return None
    # 获取图片的原始宽度和高度
    width, height = image.size
    # 获取显示器的分辨率
    #screen_width, screen_height = PIL.ImageGrab.grab().size
    # 计算缩放比例，取宽度和高度中较小的值
    ratio = min(screen_width / width, screen_height / height)
    # 计算新的宽度和高度，保持原始图片的纵横比
    new_width = int(width * ratio)
    new_height = int(height * ratio)

    # 第一种处理图片数据截断的方法（需import ImageFile）：
    #   当遇到数据截断的图片时，PIL会直接break，跳出函数，不报错，进行下一个
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    # # 第二种处理图片数据截断的方法（需from io import BytesIO）：
    # # 读取图片文件为二进制数据
    # with open(imagePath, 'rb') as f:
    #     f = f.read()
    # # 在二进制数据的末尾补上标识符\xff\xd9
    # f = f + b'\xff' + b'\xd9'
    # # 将二进制数据转换为图片对象
    # image = Image.open(BytesIO(f))

    # 使用PIL模块的Image类的resize方法调整图片大小
    # 第一个参数是新的宽度和高度的元组，第二个参数是缩放算法
    resized_image = image.resize((new_width, new_height), PIL.Image.LANCZOS)
    img = resized_image
    # print('Image resized successful')
    
    # 将图片先裁剪为方形，再裁剪为圆形（如果直接裁剪为圆形，很容易因为图片计算过程过程中四舍五入，导致创建的画布大小和图片大小不匹配而报错
    #将图片裁剪为方形
    if current_image_source == '风云4A':
        FY4_s, FY4_x, FY4_y = 2170 * ratio, 15 * ratio, 15 * ratio
    elif current_image_source == '风云4B':
        FY4_s, FY4_x, FY4_y = 10835 * ratio, 65 * ratio, 80 * ratio
    elif current_image_source == 'GOES-East' or current_image_source == 'GOES-West':
        FY4_s, FY4_x, FY4_y = 10800 * ratio, 24 * ratio, 24 * ratio

    box=(FY4_x, FY4_y, FY4_s+FY4_x, FY4_s+FY4_y)
    img = img.crop(box)
    width, height = img.size

    #将图片裁剪为圆形
    mask = Image.new('L', (width, height), 0) # 创建一个透明背景的画布
    draw = ImageDraw.Draw(mask) # 创建一个绘图对象
    draw.ellipse((0, 0, FY4_s, FY4_s), fill=255) # 绘制一个白色的圆形
    img.putalpha(mask) # 将圆形作为透明度掩码
    # print('Image redraw successful')

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


    # 添加时间水印
    if watermark_flag == 1:
        watermark_text = datetime.datetime.now().strftime("%Y/%m/%d  %H:%M:%S") # 获取当前时间
        draw = ImageDraw.Draw(resized_image) # 创建一个绘图对象
        draw.text((watermark_x, watermark_y), watermark_text, "white", watermark_font) # 用绘图对象绘制文字

    resized_image_path = folder_path + "resize_" + name_pic + ".jpg"
    resized_image.save(resized_image_path)
    print('Wallpaper generate successful')
    # 返回调整后的图片路径
    return resized_image_path


# 调用changeBG函数，传入wallpaper变量作为参数
def changewall(image_path , folder_path , name_pic , current_image_source , flag , watermark_flag):
    path = resize_image(image_path , folder_path , name_pic , current_image_source , flag , watermark_flag)
    if path == None :
        return
    changeBG(path)
