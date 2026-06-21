from flask import Blueprint, request, jsonify, render_template, redirect, session, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Post, User, Category, Keyword, ReviewLog, Notification
from datetime import datetime

bp = Blueprint('admin_review', __name__, url_prefix='/admin')


def admin_required(fn):
    """管理员权限装饰器"""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or user.role < 1:
            return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
        return fn(*args, **kwargs)
    return wrapper


@bp.route('/posts/pending', methods=['GET'])
@jwt_required()
@admin_required
def get_pending_posts():
    """获取待审核帖子列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Post.query.filter(Post.status == 0).order_by(Post.created_at.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    result = []
    for p in pagination.items:
        author = User.query.get(p.user_id)
        cat = Category.query.get(p.category_id)
        result.append({
            'id': p.id,
            'nickname': author.nickname if author else '未知',
            'category_name': cat.name if cat else '',
            'title': p.title,
            'content': p.content[:200],
            'status': p.status,
            'created_at': p.created_at.isoformat() if p.created_at else '',
        })

    return jsonify({'code': 200, 'data': {'posts': result, 'total': pagination.total, 'has_more': pagination.has_next}})


@bp.route('/posts/<int:post_id>/review', methods=['PUT'])
@jwt_required()
@admin_required
def review_post(post_id):
    """审核帖子(通过/拒绝)"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    action = data.get('action')  # 'approve' or 'reject'
    reason = data.get('reason', '')

    post = Post.query.get(post_id)
    if not post:
        return jsonify({'code': 404, 'message': '帖子不存在'}), 404

    if action == 'approve':
        post.status = 1
        post.reviewed_by = user_id
        post.reviewed_at = datetime.utcnow()

        # 给用户加经验
        author = User.query.get(post.user_id)
        if author:
            from api.posts import add_exp
            add_exp(author, 10)
    elif action == 'reject':
        post.status = 2
        post.review_reason = reason
        post.reviewed_by = user_id
        post.reviewed_at = datetime.utcnow()
    else:
        return jsonify({'code': 400, 'message': '无效操作'}), 400

    # 记录审核日志
    log = ReviewLog(post_id=post.id, review_type=2, result=1 if action == 'approve' else 2, reason=reason, reviewer_id=user_id)
    db.session.add(log)

    # 发送通知
    notif_title = '帖子审核通过' if action == 'approve' else '帖子审核未通过'
    notif_content = '你的帖子已通过审核' if action == 'approve' else f'你的帖子未通过审核: {reason}'
    notif = Notification(user_id=post.user_id, type=4, title=notif_title, content=notif_content, target_id=post.id)
    db.session.add(notif)

    db.session.commit()
    return jsonify({'code': 200, 'message': '审核完成'})


@bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_dashboard_stats():
    """管理后台数据概览"""
    total_users = User.query.count()
    total_posts = Post.query.count()
    pending_posts = Post.query.filter_by(status=0).count()
    today_posts = Post.query.filter(Post.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)).count()

    return jsonify({'code': 200, 'data': {
        'total_users': total_users,
        'total_posts': total_posts,
        'pending_posts': pending_posts,
        'today_posts': today_posts,
    }})
