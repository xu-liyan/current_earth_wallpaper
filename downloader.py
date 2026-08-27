import os
import re
import time
from datetime import datetime

import requests

from sources import get_image_url

MAX_FILES = 96          # 保存文件夹内最多保留的图片数量（原图 + 壁纸合计）
CHUNK_SIZE = 8192

# 只识别本程序生成的文件：原图 20250101_120000.jpg / 壁纸 resize_20250101_120000.jpg
OWN_FILE_RE = re.compile(r'^(resize_)?\d{8}_\d{6}\.jpg$')

USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')


class DownloadError(Exception):
    """下载失败：由调度器捕获并按重试策略处理"""


def _clean_old_files(save_path, log):
    """只统计并删除本程序生成的图片，按创建时间保留最新的 MAX_FILES 张"""
    own = [f for f in os.listdir(save_path) if OWN_FILE_RE.match(f)]
    if len(own) > MAX_FILES:
        own.sort(key=lambda x: os.path.getctime(os.path.join(save_path, x)), reverse=True)
        excess = len(own) - MAX_FILES
        for name in own[MAX_FILES:]:
            os.remove(os.path.join(save_path, name))
        log(f'Deleted {excess} oldest files from {save_path}')


def download_image(source, save_path, cert_path, log):
    """下载一张最新整盘云图到 save_path，返回保存的文件路径

    任何失败都以 DownloadError 抛出，不在这里决定是否重试（那是调度器的职责）。
    """
    log(f"Time: {datetime.now().strftime('%Y%m%d_%H%M%S')}")
    log(f'Image source: {source.name}')
    log('Image download begin')

    if not os.path.exists(cert_path):
        raise DownloadError(f"CA certificate doesn't exist: {cert_path}")
    log('CA certificate successfully loaded')

    # 取真实下载地址：风云4B 是直链，GOES 需要解析列表页
    if source.direct:
        image_url = source.home_url
    else:
        log('Extract image links begin')
        try:
            image_url = get_image_url(source, cert_path)
        except requests.exceptions.RequestException as e:
            raise DownloadError(f'Network request failed: {e}') from e
        except Exception as e:
            raise DownloadError(f'Error during image link extraction: {e}') from e

    try:
        # 流式下载，支持大文件
        response = requests.get(image_url, verify=cert_path,
                                headers={'User-Agent': USER_AGENT},
                                stream=True, timeout=60)
        if response.status_code != 200:
            raise DownloadError(
                f'Download failed with status code: {response.status_code}')

        total_size = int(response.headers.get('content-length', 0))
        log(f'Image Size: {total_size / (1024 * 1024):.2f} MB')

        start_time = time.time()
        next_threshold = 25      # 每下载 25% 打印一次进度
        downloaded_size = 0
        file_path = os.path.join(
            save_path, datetime.now().strftime('%Y%m%d_%H%M%S') + '.jpg')

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        percent = downloaded_size / total_size * 100
                        if percent >= next_threshold or downloaded_size == total_size:
                            elapsed = time.time() - start_time
                            speed = ((downloaded_size / (1024 * 1024)) / elapsed
                                     if elapsed > 0 else 0)
                            log(f'Download progress: {percent:.1f}% | '
                                f'Speed: {speed:.2f} MB/s')
                            next_threshold = min(100, next_threshold + 25)

        log('Image download successful')
        log(f'Total time consumption: {time.time() - start_time:.2f} s')
    except requests.exceptions.RequestException as e:
        raise DownloadError(f'Error during download: {e}') from e
    except OSError as e:
        raise DownloadError(f'Error during saving: {e}') from e

    _clean_old_files(save_path, log)
    return file_path
