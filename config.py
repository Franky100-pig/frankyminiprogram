import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')

    # 数据库 - 纯 SQLite，无需安装任何数据库
    db_path = os.getenv('SQLITE_PATH', 'campus_wall.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-prod')
    JWT_ACCESS_TOKEN_EXPIRES = 30 * 24 * 3600  # 30天

    # 微信小程序配置
    WECHAT_APPID = os.getenv('WECHAT_APPID', 'wx_test_appid')
    WECHAT_SECRET = os.getenv('WECHAT_SECRET', 'test_secret')
    WECHAT_CODE2SESSION_URL = 'https://api.weixin.qq.com/sns/jscode2session'

    # 文件上传
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

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
