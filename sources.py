import re
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ImageSource:
    """一个卫星图像源的全部元数据

    name       源标识，同时作为配置值和翻译 key
    home_url   直链（风云4B）或列表页地址（GOES）
    direct     True 表示 home_url 就是图片直链，无需解析
    crop_*     地球在原图中的裁剪区域（原图像素，随缩放比等比换算后使用）
    """
    name: str
    home_url: str
    direct: bool
    crop_size: int
    crop_x: int
    crop_y: int


# 新增一个图源只需在这里加一个条目，UI 单选按钮和裁剪逻辑自动生效
SOURCES = {
    '风云4B': ImageSource(
        name='风云4B',
        home_url='http://img.nsmc.org.cn/CLOUDIMAGE/FY4B/AGRI/GCLR/FY4B_DISK_GCLR.JPG',
        direct=True,
        crop_size=10835, crop_x=65, crop_y=80,
    ),
    'GOES-East': ImageSource(
        name='GOES-East',
        home_url='https://www.star.nesdis.noaa.gov/goes/fulldisk.php?sat=G19',
        direct=False,
        crop_size=10800, crop_x=24, crop_y=24,
    ),
    'GOES-West': ImageSource(
        name='GOES-West',
        home_url='https://www.star.nesdis.noaa.gov/goes/fulldisk.php?sat=G18',
        direct=False,
        crop_size=10800, crop_x=24, crop_y=24,
    ),
}

_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
    'Referer': 'https://www.star.nesdis.noaa.gov/goes/',
}


def get_image_url(source, cert_path, timeout=15):
    """返回该源当前最新的整盘图下载地址；失败抛异常，由调用方决定重试"""
    if source.direct:
        return source.home_url

    response = requests.get(source.home_url, verify=cert_path,
                            headers=_HEADERS, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    # 10848 分辨率约 20MB；21696 超过 40MB，下载太慢，已放弃
    pattern = re.compile(r'GEOCOLOR-10848x10848.jpg', re.IGNORECASE)
    for link in soup.find_all('a'):
        href = link.get('href', '')
        if pattern.search(href):
            full_url = urljoin(source.home_url, href)
            if not urlparse(full_url).query:
                full_url += f'?t={int(time.time())}'   # 加时间戳避免缓存
            return full_url
    raise RuntimeError("No links containing 'GEOCOLOR-10848x10848.jpg' were found")
