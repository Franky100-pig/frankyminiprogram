"""
校园墙小程序后端 - 唯一启动入口
- 本地开发: python run.py
- Docker/云托管: gunicorn -w 2 -b 0.0.0.0:80 run:app
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
