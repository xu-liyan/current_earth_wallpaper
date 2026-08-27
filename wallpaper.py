import ctypes
import datetime
import os

import mss
import PIL
from PIL import Image, ImageDraw, ImageFont, ImageFile

# 处理大图与截断图的全局开关（与原版一致）
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = 700000000   # 7 亿像素，10848x10848 的 GOES 图需要

SPI_SETDESKWALLPAPER = 20

# 壁纸比例：配置值 → 缩放策略编号
SCALE_MODES = {
    '铺满屏幕': 0,
    '原始大小': 1,
    '黄金比例': 2,
    '更小尺寸': 3,
}


def get_screen_size():
    """实时读取显示器分辨率（每次生成壁纸时调用，支持运行中更换显示器）"""
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        return monitor['width'], monitor['height']


def set_wallpaper(image_path):
    """调用 Windows API 设置桌面壁纸"""
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)


def _text_size(font, text):
    """计算文字宽高；Pillow 10+ 已移除 getsize，改用 getbbox"""
    box = font.getbbox(text)
    return box[2] - box[0], box[3] - box[1]


def generate_wallpaper(image_path, folder_path, name_pic, source, flag, watermark_on, log):
    """把整盘卫星图重绘为圆形地球壁纸，返回壁纸文件路径；图片打开失败返回 None

    处理流程：等比缩放 → 裁出地球正方形 → 圆形蒙版 → 按比例二次缩放
    → 居中贴到黑色全屏画布 → 可选时间水印
    """
    log('Wallpaper generate begin')
    try:
        image = Image.open(image_path)
    except PIL.UnidentifiedImageError:
        log('!!Image open failed')
        return None

    screen_width, screen_height = get_screen_size()

    # 第一步：等比缩放到屏幕分辨率（取宽高较小的缩放比，保持纵横比）
    width, height = image.size
    ratio = min(screen_width / width, screen_height / height)
    img = image.resize((int(width * ratio), int(height * ratio)), PIL.Image.LANCZOS)

    # 第二步：按图源参数裁出地球所在的正方形（坐标随第一步的缩放比等比换算）
    s = source.crop_size * ratio
    x = source.crop_x * ratio
    y = source.crop_y * ratio
    img = img.crop((x, y, s + x, s + y))
    w, h = img.size

    # 第三步：圆形蒙版抠出地球（先方形后圆形，避免四舍五入导致画布尺寸不匹配）
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, s, s), fill=255)
    img.putalpha(mask)

    # 第四步：按所选比例二次缩放
    if flag == 0:
        ratio = screen_height / img.height            # 铺满屏幕
    elif flag == 1:
        ratio = 1                                      # 原始大小
    elif flag == 2:
        ratio = screen_height / img.height * 0.618     # 黄金比例
    elif flag == 3:
        ratio = screen_height / img.height * 0.45       # 更小尺寸
    img = img.resize((int(img.width * ratio), int(img.height * ratio)), PIL.Image.LANCZOS)

    # 第五步：居中贴到黑色全屏画布（RGBA 无法存为 jpg，必须转 RGB）
    bk_image = Image.new('RGB', (screen_width, screen_height), (0, 0, 0))
    sw, sh = bk_image.size
    ew, eh = img.size
    bk_image.paste(img, (int((sw - ew) / 2), int((sh - eh) / 2)), mask=img)

    # 第六步：右下角时间水印
    if watermark_on:
        text = datetime.datetime.now().strftime('%Y/%m/%d  %H:%M:%S')
        font = ImageFont.truetype('arial.ttf', int(screen_height / 60))
        text_width, text_height = _text_size(font, text)
        margin = int(screen_height / 24)
        ImageDraw.Draw(bk_image).text(
            (screen_width - text_width - margin / 2,
             screen_height - text_height - margin),
            text, 'white', font)

    out_path = os.path.join(folder_path, f'resize_{name_pic}.jpg')
    bk_image.save(out_path)
    log('Wallpaper generate successful')
    return out_path


def change_wallpaper(image_path, folder_path, name_pic, source, flag, watermark_on, log):
    """生成并设置壁纸；返回是否成功"""
    path = generate_wallpaper(image_path, folder_path, name_pic,
                              source, flag, watermark_on, log)
    if path is None:
        return False
    set_wallpaper(path)
    log('Wallpaper set successful')
    return True
