from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Post, Category, User, Like, ReviewLog, Notification, LevelConfig
from services.keyword_filter import check_post_content, async_refresh
from datetime import datetime
import json

bp = Blueprint('posts', __name__, url_prefix='')


@bp.route('/categories', methods=['GET'])
def get_categories():
    """获取所有分区列表"""
    from app.models import Category
    cats = Category.query.filter_by(is_active=1).order_by(Category.sort_order.asc()).all()
    return jsonify([{'id': c.id, 'name': c.name, 'icon': c.icon} for c in cats])


def add_exp(user, amount):
    """为用户增加经验值，并检查升级"""
    user.exp += amount
    # 查询等级配置
    next_level = LevelConfig.query.filter(
        LevelConfig.min_exp <= user.exp
    ).order_by(LevelConfig.min_exp.desc()).first()
    if next_level and next_level.level > user.level:
        user.level = next_level.level
        # 发送升级通知
        notif = Notification(
            user_id=user.id,
            type=99,  # 系统通知：升级
            title='恭喜升级',
            content=f'你已升级到 {next_level.title}(Lv.{next_level.level})！',
            target_id=None
        )
        db.session.add(notif)
    db.session.commit()


@bp.route('/search', methods=['GET'])
def search_posts():
    """搜索帖子"""
    keyword = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    if not keyword:
        return jsonify({'msg': '请输入搜索关键词'}), 400

    query = Post.query.filter(Post.status == 1)
    # 搜索标题和内容
    search_filter = (Post.title.contains(keyword) | Post.content.contains(keyword))
    query = query.filter(search_filter)

    if category_id:
        query = query.filter(Post.category_id == category_id)

    query = query.order_by(Post.is_top.desc(), Post.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    current_user_id = None
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        verify_jwt_in_request(optional=True)
        current_user_id = int(get_jwt_identity()) if get_jwt_identity() else None
    except:
        pass

    result = [p.to_dict(current_user_id=current_user_id) for p in pagination.items]

    return jsonify({
        'posts': result,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'has_more': pagination.has_next,
        'keyword': keyword,
    })


@bp.route('/', methods=['GET'])
def get_posts():
    """
    获取帖子列表
    参数: category_id, page, per_page, orderby( latest/hot)
    """
    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    order_by = request.args.get('order_by', 'latest')

    from app.models import Post
    query = Post.query.filter(Post.status == 1)  # 只查已通过的

    if category_id:
        query = query.filter(Post.category_id == category_id)

    if order_by == 'hot':
        query = query.order_by(Post.like_count.desc(), Post.created_at.desc())
    else:
        query = query.order_by(Post.is_top.desc(), Post.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    posts = pagination.items

    # 获取当前用户(可选登录)
    current_user_id = None
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        verify_jwt_in_request(optional=True)
        current_user_id = int(get_jwt_identity()) if get_jwt_identity() else None
    except:
        pass

    result = [p.to_dict(current_user_id=current_user_id) for p in posts]

    return jsonify({
        'posts': result,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'has_more': pagination.has_next
    })


@bp.route('/<int:post_id>', methods=['GET'])
def get_post_detail(post_id):
    """获取帖子详情"""
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'msg': '帖子不存在'}), 404

    # 增加浏览数
    post.view_count += 1
    db.session.commit()

    current_user_id = None
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        verify_jwt_in_request(optional=True)
        current_user_id = int(get_jwt_identity()) if get_jwt_identity() else None
    except:
        pass

    return jsonify(post.to_dict(current_user_id=current_user_id))


@bp.route('/', methods=['POST'])
@jwt_required()
def create_post():
    """发布帖子"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.status == 0:
        return jsonify({'msg': '用户已被禁用'}), 403

    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    category_id = int(data.get('category_id', 0))
    images = data.get('images', [])  # 图片URL数组
    video_url = data.get('video_url', '')
    is_anonymous = data.get('is_anonymous', 0)

    if not content:
        return jsonify({'msg': '帖子内容不能为空'}), 400
    if not category_id:
        return jsonify({'msg': '请选择分区'}), 400

    # 验证分类是否存在
    cat = Category.query.get(category_id)
    if not cat or cat.is_active == 0:
        return jsonify({'msg': '分区不存在或已禁用'}), 400

    # 关键词自动审查
    from config import Config
    if Config.KEYWORD_FILTER_ENABLED:
        check_result = check_post_content(title, content)
        if not check_result['passed']:
            action = check_result['action']
            hits = check_result['hits']
            hit_keywords = [h['keyword'] for h in hits]

            post = Post(
                user_id=user_id,
                category_id=category_id,
                title=title,
                content=content,
                images=json.dumps(images, ensure_ascii=False) if images else None,
                video_url=video_url,
                is_anonymous=is_anonymous,
                status=0 if action == 'review' else 2,  # 0待审 2拒绝
                review_reason=f"命中敏感词: {', '.join(hit_keywords)}" if action == 'reject' else '需人工审核(命中警告词)'
            )
            db.session.add(post)
            db.session.commit()

            # 记录审核日志
            log = ReviewLog(post_id=post.id, review_type=1, result=2, reason=f"命中关键词: {hit_keywords}")
            db.session.add(log)
            db.session.commit()

            if action == 'reject':
                return jsonify({'msg': '帖子包含不当内容，已自动拒绝', 'status': 2, 'reason': post.review_reason})
            else:
                return jsonify({'msg': '帖子已进入人工审核队列', 'status': 0})

    # 通过关键词审查 → 直接发布
    post = Post(
        user_id=user_id,
        category_id=category_id,
        title=title,
        content=content,
        images=json.dumps(images, ensure_ascii=False) if images else None,
        video_url=video_url,
        is_anonymous=is_anonymous,
        status=1  # 直接通过
    )
    db.session.add(post)

    # 更新用户发帖数 & 加经验
    user.post_count += 1
    add_exp(user, 10)

    db.session.commit()

    # 记录审核日志(自动通过)
    log = ReviewLog(post_id=post.id, review_type=1, result=1, reason='自动审核通过')
    db.session.add(log)
    db.session.commit()

    return jsonify({'msg': '发布成功', 'post_id': post.id, 'status': 1})


@bp.route('/<int:post_id>/like', methods=['POST'])
@jwt_required()
def toggle_like_post(post_id):
    """点赞/取消点赞帖子"""
    user_id = int(get_jwt_identity())
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'msg': '帖子不存在'}), 404

    existing = Like.query.filter_by(user_id=user_id, target_type=1, target_id=post_id).first()
    if existing:
        # 取消点赞
        db.session.delete(existing)
        post.like_count = max(0, post.like_count - 1)
        db.session.commit()
        return jsonify({'is_liked': False})
    else:
        # 添加点赞
        like = Like(user_id=user_id, target_type=1, target_id=post_id)
        db.session.add(like)
        post.like_count += 1
        db.session.commit()

        # 给帖子作者加经验
        author = User.query.get(post.user_id)
        if author and author.id != user_id:
            add_exp(author, 2)
            # 发送通知
            notif = Notification(
                user_id=post.user_id,
                type=1,  # 点赞通知
                title='收到点赞',
                content=f'{user.nickname} 赞了你的帖子',
                target_id=post_id
            )
            db.session.add(notif)
            db.session.commit()

        return jsonify({'is_liked': True})
