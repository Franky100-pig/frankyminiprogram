import requests
import time
import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db, redis_client
from app.models import User, SystemConfig
import json

bp = Blueprint('auth', __name__, url_prefix='/auth')


def wx_code2session(code):
    """调用微信code2Session接口"""
    from config import Config
    url = Config.WECHAT_CODE2SESSION_URL
    params = {
        'appid': Config.WECHAT_APPID,
        'secret': Config.WECHAT_SECRET,
        'js_code': code,
        'grant_type': 'authorization_code'
    }
    resp = requests.get(url, params=params, timeout=10)
    return resp.json()  # {openid, session_key, unionid}


@bp.route('/wx-login', methods=['POST'])
def wx_login():
    """
    微信小程序登录接口
    请求体: {code: 'xxx', nickname: 'xxx', avatar_url: 'xxx', gender: 0, school: 'xxx'}
    本地开发模式下(WECHAT_APPID=wx_test_appid)会自动绕过微信验证
    """
    data = request.get_json()
    code = data.get('code')
    if not code:
        return jsonify({'code': 400, 'message': '缺少code参数'}), 400

    from config import Config

    # 开发模式：AppID是测试占位值时，直接用code作为openid，不调微信API
    if Config.WECHAT_APPID.startswith('wx_test_') or Config.WECHAT_APPID == 'wx_test_appid':
        openid = 'dev_openid_' + code
        unionid = ''
    else:
        # 正式模式：调用微信code2Session接口
        wx_result = wx_code2session(code)
        if 'errcode' in wx_result:
            return jsonify({'code': 500, 'message': '微信登录失败: %s' % wx_result.get('errmsg')}), 500
        openid = wx_result.get('openid')
        unionid = wx_result.get('unionid', '')

    # 查找或创建用户
    user = User.query.filter_by(openid=openid).first()
    if not user:
        user = User(
            openid=openid,
            unionid=unionid,
            nickname=data.get('nickname', '校园同学'),
            avatar_url=data.get('avatar_url', ''),
            gender=data.get('gender', 0),
            school=data.get('school', ''),
        )
        db.session.add(user)
        db.session.commit()

    # 更新用户信息(昵称头像可能变化)
    user.nickname = data.get('nickname', user.nickname)
    user.avatar_url = data.get('avatar_url', user.avatar_url)
    user.last_active_at = datetime.datetime.utcnow()
    db.session.commit()

    # 生成JWT token
    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'access_token': access_token,
            'user': {
                'id': user.id,
                'nickname': user.nickname,
                'avatar_url': user.avatar_url,
                'school': user.school,
                'level': user.level,
                'exp': user.exp,
                'post_count': user.post_count,
                'role': user.role,
                'show_contact': user.show_contact,
                'contact_info': user.contact_info if user.show_contact else '',
            }
        }
    })


@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前登录用户信息"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    return jsonify({
        'code': 200,
        'data': {
            'id': user.id,
            'nickname': user.nickname,
            'avatar_url': user.avatar_url,
            'gender': user.gender,
            'school': user.school,
            'level': user.level,
            'exp': user.exp,
            'post_count': user.post_count,
            'like_received_count': user.like_received_count,
            'comment_received_count': user.comment_received_count,
            'show_contact': user.show_contact,
            'contact_info': user.contact_info if user.show_contact else '',
            'role': user.role,
            'created_at': user.created_at.isoformat() if user.created_at else '',
        }
    })


@bp.route('/signup', methods=['POST'])
def signup():
    """用户名密码注册（本地测试用）"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    nickname = data.get('nickname', '校园同学')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400
    if len(password) < 4:
        return jsonify({'code': 400, 'message': '密码至少4位'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'code': 400, 'message': '用户名已存在'}), 400

    from werkzeug.security import generate_password_hash
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        nickname=nickname,
        school=data.get('school', ''),
    )
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'code': 201,
        'message': '注册成功',
        'data': {
            'access_token': access_token,
            'user': {
                'id': user.id,
                'nickname': user.nickname,
                'avatar_url': user.avatar_url,
                'school': user.school,
                'level': user.level,
                'exp': user.exp,
            }
        }
    }), 201


@bp.route('/signin', methods=['POST'])
def signin():
    """用户名密码登录（本地测试用）"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'access_token': access_token,
            'user': {
                'id': user.id,
                'nickname': user.nickname,
                'avatar_url': user.avatar_url,
                'school': user.school,
                'level': user.level,
                'exp': user.exp,
            }
        }
    })


@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户信息(昵称、学校、联系方式等)"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    data = request.get_json()
    if 'nickname' in data:
        user.nickname = data['nickname']
    if 'school' in data:
        user.school = data['school']
    if 'show_contact' in data:
        user.show_contact = int(data['show_contact'])
    if 'contact_info' in data:
        user.contact_info = data['contact_info']
    if 'gender' in data:
        user.gender = int(data['gender'])

    db.session.commit()
    return jsonify({'code': 200, 'message': '更新成功'})
