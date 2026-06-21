from datetime import datetime
from app import db
import json
from werkzeug.security import generate_password_hash, check_password_hash as _check_password_hash


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.String(64), unique=True, nullable=True)
    unionid = db.Column(db.String(64), nullable=True)
    username = db.Column(db.String(64), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    nickname = db.Column(db.String(64), default='')
    avatar_url = db.Column(db.String(512), default='')
    gender = db.Column(db.Integer, default=0)
    school = db.Column(db.String(64), default='')
    contact_info = db.Column(db.String(128), default='')
    show_contact = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    exp = db.Column(db.Integer, default=0)
    post_count = db.Column(db.Integer, default=0)
    like_received_count = db.Column(db.Integer, default=0)
    comment_received_count = db.Column(db.Integer, default=0)
    role = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=1)
    last_active_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='commenter', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return _check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    icon = db.Column(db.String(64), default='')
    color = db.Column(db.String(16), default='#378ADD')
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Integer, default=1)
    description = db.Column(db.String(128), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship('Post', backref='category', lazy='dynamic')


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    title = db.Column(db.String(128), default='')
    content = db.Column(db.Text, nullable=False)
    images = db.Column(db.Text, nullable=True)  # JSON array string
    video_url = db.Column(db.String(512), default='')
    is_anonymous = db.Column(db.Integer, default=0)
    is_top = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=0)  # 0待审 1通过 2拒绝 3下架
    review_reason = db.Column(db.String(256), default='')
    reviewed_by = db.Column(db.Integer, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, current_user_id=None):
        images_list = json.loads(self.images) if self.images else []
        author = User.query.get(self.user_id)
        cat = Category.query.get(self.category_id)
        is_liked = False
        if current_user_id:
            is_liked = Like.query.filter_by(user_id=current_user_id, target_type=1, target_id=self.id).first() is not None

        return {
            'id': self.id,
            'user_id': self.user_id if not self.is_anonymous else None,
            'nickname': '' if self.is_anonymous else (author.nickname if author else '未知用户'),
            'avatar_url': '' if self.is_anonymous else (author.avatar_url if author else ''),
            'is_anonymous': self.is_anonymous,
            'category_id': self.category_id,
            'category_name': cat.name if cat else '',
            'category_color': cat.color if cat else '#378ADD',
            'title': self.title,
            'content': self.content,
            'images': images_list,
            'video_url': self.video_url,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'view_count': self.view_count,
            'is_top': self.is_top,
            'status': self.status,
            'is_liked': is_liked,
            'created_at': self.created_at.isoformat() if self.created_at else '',
        }


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    reply_to_user_id = db.Column(db.Integer, nullable=True)
    content = db.Column(db.Text, nullable=False)
    like_count = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), cascade='all, delete-orphan')


class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_type = db.Column(db.Integer, nullable=False)  # 1帖子 2评论
    target_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'target_type', 'target_id', name='uk_user_target'),
    )


class Keyword(db.Model):
    __tablename__ = 'keywords'
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(128), unique=True, nullable=False)
    category = db.Column(db.String(32), default='default')
    level = db.Column(db.Integer, default=1)  # 1警告 2拒绝
    is_active = db.Column(db.Integer, default=1)
    created_by = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReviewLog(db.Model):
    __tablename__ = 'review_logs'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=True)
    comment_id = db.Column(db.Integer, nullable=True)
    review_type = db.Column(db.Integer, nullable=False)  # 1自动 2人工
    result = db.Column(db.Integer, nullable=False)  # 1通过 2拒绝
    reason = db.Column(db.String(512), default='')
    reviewer_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LevelConfig(db.Model):
    __tablename__ = 'level_config'
    level = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(32), nullable=False)
    min_exp = db.Column(db.Integer, nullable=False)
    max_exp = db.Column(db.Integer, nullable=False)
    icon = db.Column(db.String(256), default='')


class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(256), default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.String(512), default='')
    target_id = db.Column(db.Integer, nullable=True)
    is_read = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
