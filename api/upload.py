"""
文件上传接口（本地开发版）
生产环境建议使用腾讯云COS
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User

bp = Blueprint('upload', __name__)


@bp.route('/image', methods=['POST'])
@jwt_required()
def upload_image():
    """上传图片（本地开发用，正式环境请使用COS）"""
    if 'file' not in request.files:
        return jsonify({'error': '未找到文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    # 简单保存（实际应使用COS）
    import os
    upload_dir = 'uploads/images'
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{get_jwt_identity()}_{int(__import__('time').time())}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    return jsonify({
        'url': f'/uploads/images/{filename}',
        'message': '上传成功（本地模式）'
    }), 200
