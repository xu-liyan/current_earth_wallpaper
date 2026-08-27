import json
import os
import pickle
from dataclasses import asdict, dataclass, fields

from utils import app_path

CONFIG_FILE = 'wallpaper_config.json'   # 新配置：JSON，人工可读可改
OLD_PKL_FILE = 'wallpaperdata.pkl'      # 旧版配置：自动迁移后不再使用

VALID_SOURCES = ('风云4B', 'GOES-East', 'GOES-West')
VALID_SCALES = ('铺满屏幕', '原始大小', '黄金比例', '更小尺寸')
VALID_LANGUAGES = ('中文', 'English')

# 水印按钮显示“取消时间水印”时，说明水印当前处于开启状态
_WATERMARK_ON_TEXTS = ('取消时间水印', 'Cancel time watermark')


@dataclass
class AppConfig:
    """应用的全部可持久化状态（界面上的每次修改即时同步到这里）"""
    image_source: str = '风云4B'
    scale_mode: str = '黄金比例'
    save_path: str = ''
    interval_minutes: int = 30
    watermark_on: bool = False
    language: str = '中文'


def _config_file():
    return os.path.join(app_path(), CONFIG_FILE)


def _field_names():
    return {f.name for f in fields(AppConfig)}


def _sanitize(cfg):
    """把配置值收敛到合法范围：配置文件损坏或手改出错时不阻断启动"""
    if cfg.image_source not in VALID_SOURCES:
        cfg.image_source = VALID_SOURCES[0]
    if cfg.scale_mode not in VALID_SCALES:
        cfg.scale_mode = '黄金比例'
    if cfg.language not in VALID_LANGUAGES:
        cfg.language = '中文'
    if not isinstance(cfg.interval_minutes, (int, float)) or cfg.interval_minutes <= 0:
        cfg.interval_minutes = 30
    cfg.interval_minutes = int(cfg.interval_minutes)
    cfg.save_path = str(cfg.save_path or '')
    cfg.watermark_on = bool(cfg.watermark_on)
    return cfg


def _migrate_from_pkl():
    """从旧版 pickle 配置迁移（老用户覆盖 exe 后首次运行时自动执行）

    旧配置里的水印状态存在按钮文字里，这里按文字反推回布尔值。
    """
    pkl_path = os.path.join(app_path(), OLD_PKL_FILE)
    if not os.path.exists(pkl_path):
        return None
    try:
        with open(pkl_path, 'rb') as f:
            data = pickle.load(f)
        try:
            interval = int(float(data.get('interval_var', '30')))
        except (TypeError, ValueError):
            interval = 30
        return AppConfig(
            image_source=data.get('current_url', '风云4B'),
            scale_mode=data.get('current_scale', '黄金比例'),
            save_path=data.get('save_path', ''),
            interval_minutes=interval,
            watermark_on=data.get('water_button', '') in _WATERMARK_ON_TEXTS,
            language=data.get('language', '中文'),
        )
    except Exception:
        # 旧配置损坏时直接用默认值，不让程序起不来
        return None


def load():
    """读取配置：JSON → 旧 pkl 迁移 → 默认值，任何异常都不阻断启动"""
    cfg = None
    if os.path.exists(_config_file()):
        try:
            with open(_config_file(), 'r', encoding='utf-8') as f:
                data = json.load(f)
            cfg = AppConfig(**{k: v for k, v in data.items() if k in _field_names()})
        except Exception:
            cfg = None
    if cfg is None:
        cfg = _migrate_from_pkl() or AppConfig()
    return _sanitize(cfg)


def save(cfg):
    """保存配置到 JSON；失败时静默（不影响主流程）"""
    try:
        with open(_config_file(), 'w', encoding='utf-8') as f:
            json.dump(asdict(cfg), f, ensure_ascii=False, indent=2)
    except OSError:
        pass
