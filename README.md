# 校园墙小程序 - 后端服务

基于 Flask 的校园墙微信小程序后端 API 服务。

## 功能模块

- 用户认证（微信登录 / 本地测试账号）
- 帖子发布、分类、搜索
- 评论与回复（楼中楼）
- 点赞系统
- 关键词自动审查
- 管理员审核后台 API
- 用户等级与经验系统

## 技术栈

- Python 3.13 + Flask
- Flask-SQLAlchemy（ORM）
- Flask-JWT-Extended（认证）
- SQLite（开发）/ MySQL（生产）

## 快速启动

```bash
pip install -r requirements.txt
python init_db.py   # 初始化数据库
python run.py       # 启动服务，默认 5001 端口
```

## 环境变量（.env）

```
DATABASE_TYPE=sqlite
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
FLASK_ENV=development
```

## 目录结构

```
backend/
├── api/           # 各模块蓝图（auth/posts/comments/users/admin）
├── app/           # Flask app 工厂、模型定义
├── services/      # 业务逻辑（关键词过滤等）
├── config.py      # 配置类
├── init_db.py     # 数据库初始化脚本
└── run.py         # 启动入口
```
