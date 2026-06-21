import os
from dotenv import load_dotenv

load_dotenv()


def get_database_uri():
    """根据环境变量选择数据库类型，默认使用SQLite"""
    db_type = os.getenv('DB_TYPE', 'sqlite')  # sqlite 或 mysql
    
    if db_type == 'mysql':
        return os.getenv(
            'DATABASE_URL',
            'mysql+pymysql://root:password@localhost:3306/campus_wall?charset=utf8mb4'
        )
    else:
        # SQLite - 适合本地开发，无需安装数据库
        db_path = os.getenv('SQLITE_PATH', 'campus_wall.db')
        return f'sqlite:///{db_path}'


class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')

    # 数据库 - 支持 SQLite 和 MySQL 自动切换
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-prod')
    JWT_ACCESS_TOKEN_EXPIRES = 30 * 24 * 3600  # 30天

    # 微信小程序 (测试用占位值，上线前必须替换)
    WECHAT_APPID = os.getenv('WECHAT_APPID', 'wx_test_appid')
    WECHAT_SECRET = os.getenv('WECHAT_SECRET', 'test_secret')
    WECHAT_CODE2SESSION_URL = 'https://api.weixin.qq.com/sns/jscode2session'

    # 文件上传
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

    # 腾讯云COS (可选，本地开发可跳过)
    COS_SECRET_ID = os.getenv('COS_SECRET_ID', '')
    COS_SECRET_KEY = os.getenv('COS_SECRET_KEY', '')
    COS_REGION = os.getenv('COS_REGION', 'ap-guangzhou')
    COS_BUCKET = os.getenv('COS_BUCKET', '')
    COS_DOMAIN = os.getenv('COS_DOMAIN', '')  # CDN域名

    # Redis (本地开发可禁用)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_ENABLED = os.getenv('REDIS_ENABLED', '0') == '1'

    # 关键词过滤
    KEYWORD_FILTER_ENABLED = os.getenv('KEYWORD_FILTER_ENABLED', '1') == '1'

    # 小程序配置
    POSTS_PER_DAY = int(os.getenv('POSTS_PER_DAY', '10'))


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
