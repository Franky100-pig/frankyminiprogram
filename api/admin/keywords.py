from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Keyword
from services.keyword_filter import refresh_cache, async_refresh

bp = Blueprint('admin_keywords', __name__, url_prefix='/admin/keywords')


def admin_required(fn):
    from functools import wraps
    from app.models import User
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or user.role < 1:
            return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
        return fn(*args, **kwargs)
    return wrapper


@bp.route('/', methods=['GET'])
@jwt_required()
@admin_required
def get_keywords():
    """获取关键词列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    category = request.args.get('category', '')

    query = Keyword.query
    if category:
        query = query.filter_by(category=category)
    query = query.order_by(Keyword.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    result = [{
        'id': k.id,
        'keyword': k.keyword,
        'category': k.category,
        'level': k.level,
        'is_active': k.is_active,
        'created_at': k.created_at.isoformat() if k.created_at else '',
    } for k in pagination.items]

    return jsonify({'code': 200, 'data': {'keywords': result, 'total': pagination.total}})


@bp.route('/', methods=['POST'])
@jwt_required()
@admin_required
def add_keyword():
    """添加关键词"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    category = data.get('category', 'default')
    level = data.get('level', 1)  # 1警告 2拒绝

    if not keyword:
        return jsonify({'code': 400, 'message': '关键词不能为空'}), 400

    existing = Keyword.query.filter_by(keyword=keyword).first()
    if existing:
        return jsonify({'code': 400, 'message': '关键词已存在'}), 400

    kw = Keyword(keyword=keyword, category=category, level=level, created_by=user_id)
    db.session.add(kw)
    db.session.commit()

    # 刷新缓存
    async_refresh()

    return jsonify({'code': 200, 'message': '添加成功'})


@bp.route('/<int:kw_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_keyword(kw_id):
    """删除关键词"""
    kw = Keyword.query.get(kw_id)
    if not kw:
        return jsonify({'code': 404, 'message': '关键词不存在'}), 404

    db.session.delete(kw)
    db.session.commit()

    # 刷新缓存
    async_refresh()

    return jsonify({'code': 200, 'message': '删除成功'})


@bp.route('/batch', methods=['POST'])
@jwt_required()
@admin_required
def batch_add_keywords():
    """批量添加关键词(一行一个)"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    keywords_text = data.get('keywords', '')  # 换行分隔
    category = data.get('category', 'default')
    level = data.get('level', 1)

    lines = [l.strip() for l in keywords_text.split('\n') if l.strip()]
    added = 0
    for line in lines:
        existing = Keyword.query.filter_by(keyword=line).first()
        if not existing:
            kw = Keyword(keyword=line, category=category, level=level, created_by=user_id)
            db.session.add(kw)
            added += 1
    db.session.commit()

    if added > 0:
        async_refresh()

    return jsonify({'code': 200, 'message': f'成功添加 {added} 个关键词'})
