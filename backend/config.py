"""应用配置 - 集中管理路径/端口/语言/调试"""
import os
from pathlib import Path


class Config:
    """基础配置"""
    # 路径
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / 'data'
    DATA_FILE = DATA_DIR / 'extracted_data.json'
    I18N_FILE = DATA_DIR / 'i18n_data.json'
    HISTORY_DB = DATA_DIR / 'history.db'
    FORMULAS_FILE = DATA_DIR / 'formulas.json'

    # 服务
    HOST = os.environ.get('MECH_HOST', '127.0.0.1')
    PORT = int(os.environ.get('MECH_PORT', '9091'))
    DEBUG = os.environ.get('MECH_DEBUG', '0') == '1'

    # i18n
    DEFAULT_LANG = os.environ.get('MECH_LANG', 'zh')
    SUPPORTED_LANGS = ('zh', 'en', 'ja')

    # JSON
    JSON_AS_ASCII = False  # 保留中文


class TestConfig(Config):
    """测试配置"""
    TESTING = True
    DEBUG = True
