"""
文件上传处理
"""
import os
import uuid
from flask import current_app


def save_avatar(file):
    """保存头像图片"""
    if not file or not file.filename:
        return None
    
    # 检查文件格式
    if '.' not in file.filename:
        return None
    
    # 获取文件扩展名
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'gif']:
        return None
    
    # 生成随机文件名
    random_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], random_name)
    
    # 保存文件
    file.save(save_path)
    
    # 返回相对URL路径
    return f"/static/img/avatars/{random_name}"

