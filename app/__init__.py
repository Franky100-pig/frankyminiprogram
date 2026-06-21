from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from config import config


db = SQLAlchemy()
jwt = JWTManager()
redis_client = None


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)

    # Redis连接（可选，本地开发可禁用）
    global redis_client
    if app.config.get('REDIS_ENABLED', False):
        from redis import Redis
        redis_client = Redis.from_url(app.config['REDIS_URL'], decode_responses=True)
    else:
        redis_client = None  # 使用内存替代

    # 注册蓝图
    from api.auth import bp as auth_bp
    from api.posts import bp as posts_bp
    from api.comments import bp as comments_bp
    from api.users import bp as users_bp
    from api.upload import bp as upload_bp
    from api.admin.review import bp as admin_review_bp
    from api.admin.keywords import bp as admin_keywords_bp
    from api.admin.stats import bp as admin_stats_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(posts_bp, url_prefix='/api/posts')
    app.register_blueprint(comments_bp, url_prefix='/api/comments')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(admin_review_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_keywords_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_stats_bp, url_prefix='/api/admin')

    # CORS - 允许小程序本地调试
    from flask_cors import CORS
    CORS(app, supports_credentials=True)

    # 健康检查
    @app.route('/health')
    def health():
        return {'status': 'ok', 'db': str(db.engine.url)[:20]}

    return app
