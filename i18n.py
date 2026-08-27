# 多语言翻译表：全程序唯一的文案来源
# 配置值（如图源名、比例名）直接以中文 key 标识，翻译时用 tr(lang, key) 取显示名

TRANSLATIONS = {
    '中文': {
        '窗口名称': '实时地球',
        '选择图像源': '选择图像源',
        '风云4B': '风云4B',
        'GOES-East': 'GOES-East',
        'GOES-West': 'GOES-West',
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
        '频率提示': '图像获取频率需为正数（分钟）！',
        '确定': '确定',
        '退出提示': '确定要停止程序并退出吗？',
        '错误': '错误',
        '自启开启提示': '已成功设置开机自启！',
        '自启取消提示': '已取消开机自启！',
        '自启失败提示': '开机自启设置失败，请重试！',
    },
    'English': {
        '窗口名称': 'Current Earth',
        '选择图像源': 'Select image source',
        '风云4B': 'FY4B',
        'GOES-East': 'GOES-East',
        'GOES-West': 'GOES-West',
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
        '频率提示': 'Image capture frequency must be a positive number (minutes) !',
        '确定': 'Sure',
        '退出提示': 'Are you sure you want to stop the program and exit ?',
        '错误': 'Error',
        '自启开启提示': 'Auto start at boot has been set successfully !',
        '自启取消提示': 'Auto start at boot has been cancelled !',
        '自启失败提示': 'Failed to set auto start at boot, please retry !',
    },
}

DEFAULT_LANGUAGE = '中文'
LANGUAGES = ('中文', 'English')


def tr(lang, key):
    """取当前语言的文案；语言或 key 不存在时退回默认语言，再退回 key 本身"""
    table = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE])
    return table.get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))
