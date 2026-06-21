FROM python:3.13-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量（默认值，部署时通过环境变量覆盖）
ENV FLASK_ENV=production
ENV DB_TYPE=sqlite
ENV SQLITE_PATH=/app/campus_wall.db
ENV JWT_SECRET_KEY=change-me-in-production
ENV SECRET_KEY=change-me-in-production
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 5001

# 使用 gunicorn 启动（需要先安装 gunicorn）
# 在 requirements.txt 中添加 gunicorn，或者在这里安装
RUN pip install --no-cache-dir gunicorn

# 初始化数据库（SQLite 时自动创建，MySQL 需先手动建库）
RUN if [ "$DB_TYPE" = "sqlite" ]; then python init_db.py; fi

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5001", "run:app"]
