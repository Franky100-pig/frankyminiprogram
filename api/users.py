from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Post, Like, LevelConfig, Notification
from datetime import datetime

bp = Blueprint('users', __name__, url_prefix='')


@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前登录用户的个人资料"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'message': '\u7528\u6237\u4e0d\u5b58\u5728'}), 404

    return jsonify({'code': 200, 'data': {
        'id': user.id,
        'nickname': user.nickname,
        'avatar_url': user.avatar_url,
        'school': user.school,
        'level': user.level,
        'exp': user.exp,
        'post_count': user.post_count,
        'like_received_count': user.like_received_count,
        'comment_received_count': user.comment_received_count,
        'role': user.role,
        'show_contact': user.show_contact,
        'contact_info': user.contact_info if user.show_contact else '',
        'gender': user.gender,
    }})


@bp.route('/<int:user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    """获取用户发布的帖子"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Post.query.filter_by(user_id=user_id, status=1).order_by(Post.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    current_user_id = None
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        current_user_id = int(identity) if identity else None
    except:
        pass

    result = [p.to_dict(current_user_id=current_user_id) for p in pagination.items]
    return jsonify({'code': 200, 'data': {'posts': result, 'has_more': pagination.has_next}})


@bp.route('/<int:user_id>/likes', methods=['GET'])
@jwt_required()
def get_user_likes(user_id):
    """获取用户点赞的帖子(仅自己可看)"""
    current_user_id = int(get_jwt_identity())
    if current_user_id != user_id:
        return jsonify({'code': 403, 'message': '\u65e0\u6743\u67e5\u770b'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = db.session.query(Post).join(Like, Like.target_id == Post.id).filter(
        Like.user_id == user_id,
        Like.target_type == 1,
        Post.status == 1
    ).order_by(Like.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    has_more = (page * per_page) < total

    result = [p.to_dict(current_user_id=user_id) for p in items]
    return jsonify({'code': 200, 'data': {'posts': result, 'has_more': has_more}})


@bp.route('/level-config', methods=['GET'])
def get_level_config():
    """获取等级配置"""
    configs = LevelConfig.query.order_by(LevelConfig.level.asc()).all()
    result = [{'level': c.level, 'min_exp': c.min_exp, 'title': c.title, 'icon': c.icon} for c in configs]
    return jsonify({'code': 200, 'data': {'levels': result}})


@bp.route('/me/statistics', methods=['GET'])
@jwt_required()
def get_my_statistics():
    """获取我的数据统计"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    level_config = LevelConfig.query.filter_by(level=user.level).first()
    next_level = LevelConfig.query.filter(LevelConfig.level > user.level).order_by(LevelConfig.level.asc()).first()

    return jsonify({'code': 200, 'data': {
        'post_count': user.post_count,
        'like_received_count': user.like_received_count,
        'comment_received_count': user.comment_received_count,
        'exp': user.exp,
        'level': user.level,
        'level_title': level_config.title if level_config else '',
        'next_level_exp': next_level.min_exp if next_level else None,
        'next_level_title': next_level.title if next_level else '',
    }})
