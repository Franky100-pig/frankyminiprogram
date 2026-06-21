"""
认证模块 - 微信授权登录

登录流程（微信官方文档）:
1. 小程序前端调用 wx.login() 获取临时登录凭证 code
2. 前端将 code 发送到后端 POST /api/auth/wx-login
3. 后端调用微信 auth.code2Session 接口换取 openid + session_key
4. 后端根据 openid 查找或创建用户，返回 JWT token

参考文档:
- https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/login.html
- https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/user-login/code2Session.html
"""
import datetime
import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')


def wx_code2session(code):
    """
    调用微信 auth.code2Session 接口
    接口: GET https://api.weixin.qq.com/sns/jscode2session
    参数: appid, secret, js_code, grant_type=authorization_code
    返回: {openid, session_key, unionid?}
    """
    from config import Config
    url = Config.WECHAT_CODE2SESSION_URL
    params = {
        'appid': Config.WECHAT_APPID,
        'secret': Config.WECHAT_SECRET,
        'js_code': code,
        'grant_type': 'authorization_code'
    }
    resp = requests.get(url, params=params, timeout=10)
    return resp.json()


@bp.route('/wx-login', methods=['POST'])
def wx_login():
    """
    微信小程序登录接口
    请求体: {
        "code": "wx.login()获取的临时凭证",
        "nickname": "用户昵称",
        "avatar_url": "头像URL",
        "gender": 0,
        "school": "学校"
    }
    返回: {
        "access_token": "JWT token",
        "user": {用户信息}
    }

    开发模式: WECHAT_APPID 以 wx_test_ 开头时，跳过微信API，直接用 code 作为 openid
    """
    data = request.get_json()
    code = data.get('code')
    if not code:
        return jsonify({'code': 400, 'message': 'missing code parameter'}), 400

    from config import Config

    # 开发模式：AppID 是测试占位值时，直接用 code 作为 openid
    if Config.WECHAT_APPID.startswith('wx_test_'):
        openid = 'dev_openid_' + code
        unionid = ''
    else:
        # 正式模式：调用微信 code2Session 接口
        wx_result = wx_code2session(code)
        if 'errcode' in wx_result and wx_result['errcode'] != 0:
            return jsonify({
                'code': 500,
                'message': 'wechat login failed: %s' % wx_result.get('errmsg', '')
            }), 500
        openid = wx_result.get('openid')
        unionid = wx_result.get('unionid', '')
        if not openid:
            return jsonify({'code': 500, 'message': 'wechat login failed: no openid'}), 500

    # 查找或创建用户
    user = User.query.filter_by(openid=openid).first()
    if not user:
        user = User(
            openid=openid,
            unionid=unionid,
            nickname=data.get('nickname', '') or 'campus_user',
            avatar_url=data.get('avatar_url', ''),
            gender=data.get('gender', 0),
            school=data.get('school', ''),
        )
        db.session.add(user)
        db.session.commit()

    # 更新用户信息（昵称头像可能变化）
    if data.get('nickname'):
        user.nickname = data['nickname']
    if data.get('avatar_url'):
        user.avatar_url = data['avatar_url']
    user.last_active_at = datetime.datetime.utcnow()
    db.session.commit()

    # 生成 JWT token
    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        'code': 200,
        'message': 'login success',
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
        return jsonify({'code': 404, 'message': 'user not found'}), 404

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


@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户信息（昵称、学校、联系方式等）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'message': 'user not found'}), 404

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
    return jsonify({'code': 200, 'message': 'update success'})
