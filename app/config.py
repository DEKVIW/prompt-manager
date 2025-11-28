"""
应用配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


class Config:
    """基础配置类"""
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')
    BASE_DIR = Path(__file__).parent.parent
    
    # 数据库配置
    DATABASE = str(BASE_DIR / 'instance' / 'prompts.db')
    
    # 日志配置
    LOG_DIR = str(BASE_DIR / 'logs')
    LOG_FILE = 'app.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 10
    
    # 静态文件配置（现在在 app/ 目录下）
    STATIC_FOLDER = str(BASE_DIR / 'app' / 'static')
    UPLOAD_FOLDER = str(BASE_DIR / 'app' / 'static' / 'img' / 'avatars')
    
    # 安全配置
    ENABLE_CORS = os.environ.get('ENABLE_CORS', 'False').lower() == 'true'
    CORS_ORIGIN = os.environ.get('CORS_ORIGIN', '*')
    HTTPS_ENABLED = os.environ.get('HTTPS_ENABLED', 'False').lower() == 'true'
    
    # LDAP配置
    LDAP_ENABLED = os.environ.get('LDAP_ENABLED', 'False').lower() == 'true'
    LDAP_SERVER = os.environ.get('LDAP_SERVER', 'ldap://localhost')
    LDAP_PORT = int(os.environ.get('LDAP_PORT', 389))
    LDAP_BIND_DN = os.environ.get('LDAP_BIND_DN', '')
    LDAP_BIND_PASSWORD = os.environ.get('LDAP_BIND_PASSWORD', '')
    LDAP_USER_SEARCH_BASE = os.environ.get('LDAP_USER_SEARCH_BASE', 'dc=example,dc=com')
    LDAP_USER_SEARCH_FILTER = os.environ.get('LDAP_USER_SEARCH_FILTER', '(uid={})')
    LDAP_USER_ATTR_MAP = {
        'username': 'uid',
        'email': 'mail'
    }

