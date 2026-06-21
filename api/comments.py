from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Comment, Post, User, Like, Notification
from services.keyword_filter import check_text
from datetime import datetime

bp = Blueprint('comments', __name__, url_prefix='')


@bp.route('/', methods=['POST'])
@jwt_required()
def create_comment():
    """发表评论"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.status == 0:
        return jsonify({'msg': '用户已被禁用'}), 403

    data = request.get_json()
    post_id = int(data.get('post_id', 0))
    content = data.get('content', '').strip()
    parent_id = int(data.get('parent_id', 0)) if data.get('parent_id') else None
    reply_to_user_id = int(data.get('reply_to_user_id', 0)) if data.get('reply_to_user_id') else None

    if not post_id or not content:
        return jsonify({'msg': '参数不完整'}), 400

    post = Post.query.get(post_id)
    if not post or post.status != 1:
        return jsonify({'msg': '帖子不存在或已下架'}), 404

    # 关键词检查(评论内容)
    from config import Config
    status = 1  # 默认通过
    if Config.KEYWORD_FILTER_ENABLED:
        check_result = check_text(content)
        if not check_result['passed']:
            status = 2  # 拒绝
            return jsonify({'msg': '评论包含不当内容', 'status': 2})

    comment = Comment(
        post_id=post_id,
        user_id=user_id,
        parent_id=parent_id,
        reply_to_user_id=reply_to_user_id,
        content=content,
        status=status
    )
    db.session.add(comment)

    # 更新帖子评论数
    post.comment_count += 1

    # 给帖子作者加经验(若评论的不是自己)
    if post.user_id != user_id:
        author = User.query.get(post.user_id)
        if author:
            from api.posts import add_exp
            add_exp(author, 2)  # 收到评论加2经验

    # 通知
    notif = Notification(
        user_id=post.user_id,
        type=2,  # 评论通知
        title='收到评论',
        content=f'{user.nickname}: {content[:50]}',
        target_id=post_id
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({'msg': '评论成功', 'comment_id': comment.id})


@bp.route('/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """获取帖子评论列表(支持楼中楼)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 只查顶层评论
    query = Comment.query.filter_by(post_id=post_id, parent_id=None, status=1)
    query = query.order_by(Comment.created_at.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    current_user_id = None
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        verify_jwt_in_request(optional=True)
        current_user_id = int(get_jwt_identity()) if get_jwt_identity() else None
    except:
        pass

    def comment_to_dict(c):
        is_liked = False
        if current_user_id:
            is_liked = Like.query.filter_by(user_id=current_user_id, target_type=2, target_id=c.id).first() is not None
        author = User.query.get(c.user_id)
        reply_to = User.query.get(c.reply_to_user_id) if c.reply_to_user_id else None
        replies = [comment_to_dict(r) for r in c.replies if r.status == 1]

        return {
            'id': c.id,
            'user_id': c.user_id,
            'nickname': author.nickname if author else '未知用户',
            'avatar_url': author.avatar_url if author else '',
            'content': c.content,
            'like_count': c.like_count,
            'is_liked': is_liked,
            'reply_to_nickname': reply_to.nickname if reply_to else '',
            'created_at': c.created_at.isoformat() if c.created_at else '',
            'replies': replies,
        }

    result = [comment_to_dict(c) for c in pagination.items]
    return jsonify({'comments': result, 'has_more': pagination.has_next})
