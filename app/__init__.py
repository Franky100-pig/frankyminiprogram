from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from config import config


db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)

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

    # CORS
    from flask_cors import CORS
    CORS(app, supports_credentials=True)

    # 根路径 - 服务信息
    @app.route('/')
    def index():
        return {
            'service': 'campus-wall-api',
            'status': 'running',
            'database': 'sqlite'
        }

    # 健康检查
    @app.route('/health')
    def health():
        return {'status': 'ok'}

    return app
