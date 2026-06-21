"""
管理员统计接口
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Post, Comment, Keyword
from sqlalchemy import func

bp = Blueprint('admin_stats', __name__)


@bp.route('/stats/overview', methods=['GET'])
@jwt_required()
def overview():
    """数据概览"""
    user_count = User.query.count()
    post_count = Post.query.count()
    pending_count = Post.query.filter_by(status='pending').count()
    comment_count = Comment.query.count()

    return jsonify({
        'user_count': user_count,
        'post_count': post_count,
        'pending_count': pending_count,
        'comment_count': comment_count
    }), 200
