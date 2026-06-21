"""
数据库初始化脚本 - 使用SQLAlchemy建表，确保与models.py完全一致
"""
import sys
import os

# 把backend目录加入path，确保能import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Category, Keyword, LevelConfig, SystemConfig

app = create_app()

with app.app_context():
    print("开始初始化数据库...")

    # 1. 创建所有表（如果不存在）
    db.create_all()
    print("  ✓ 数据库表已创建（如无则新建）")

    # 2. 插入默认分区
    categories = [
        ('失物招领', '🔍', 1),
        ('借东西', '📦', 2),
        ('竞赛组队', '🏆', 3),
        ('约球', '⚽', 4),
        ('社团通知', '📢', 5),
        ('表白墙', '💕', 6),
        ('吹水闲聊', '💬', 7),
    ]
    for name, icon, sort_order in categories:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(
                name=name, icon=icon, sort_order=sort_order, is_active=1
            ))
    db.session.commit()
    print(f"  ✓ 默认分区已初始化（{Category.query.count()} 个）")

    # 3. 插入等级配置
    levels = [
        (1, '校园新生', 0, 99, '🌱'),
        (2, '活跃达人', 100, 299, '⭐'),
        (3, '热心学长', 300, 599, '🔥'),
        (4, '校园KOL', 600, 999, '👑'),
        (5, '风云人物', 1000, 1999, '🏅'),
        (6, '传奇校草', 2000, 4999, '🎖️'),
        (7, '校园传说', 5000, 9999, '🏆'),
    ]
    for level, name, min_exp, max_exp, icon in levels:
        if not LevelConfig.query.filter_by(level=level).first():
            db.session.add(LevelConfig(
                level=level, title=name,
                min_exp=min_exp, max_exp=max_exp, icon=icon
            ))
    db.session.commit()
    print(f"  ✓ 等级配置已初始化")

    # 4. 插入默认关键词 (level: 1=警告/人工审核, 2=拒绝)
    keywords = [
        ('垃圾', 1, '测试'),
        ('广告', 2, '垃圾信息'),
        ('测试', 1, '测试'),
    ]
    for word, level, category in keywords:
        if not Keyword.query.filter_by(keyword=word).first():
            db.session.add(Keyword(
                keyword=word, level=level, category=category, is_active=1
            ))
    db.session.commit()
    print(f"  ✓ 默认关键词已初始化")

    # 5. 插入系统配置
    settings = [
        ('site_name', '校园墙', '站点名称'),
        ('posts_per_day', '10', '每日发帖限制'),
        ('keyword_filter', '1', '关键词过滤开关(1开0关)'),
    ]
    for key, value, desc in settings:
        existing = SystemConfig.query.filter_by(key=key).first()
        if not existing:
            db.session.add(SystemConfig(key=key, value=value, description=desc))
        else:
            existing.value = value
    db.session.commit()
    print(f"  ✓ 系统配置已初始化")

    print("\n✅ 数据库初始化完成！")
    print(f"   数据库文件: {app.config['SQLALCHEMY_DATABASE_URI']}")
