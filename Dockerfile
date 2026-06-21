FROM python:3.13-slim

WORKDIR /app

# 复制依赖文件并安装（纯SQLite，无需MySQL/Redis系统依赖）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 环境变量
ENV FLASK_ENV=production
ENV SQLITE_PATH=/app/campus_wall.db
ENV JWT_SECRET_KEY=change-me-in-production
ENV SECRET_KEY=change-me-in-production
ENV PYTHONUNBUFFERED=1

# 暴露80端口（云托管标准端口）
EXPOSE 80

# 初始化数据库
RUN python init_db.py

# gunicorn 启动，监听80端口
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:80", "run:app"]
