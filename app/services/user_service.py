"""
用户业务逻辑
"""
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db
import os
import uuid
from werkzeug.utils import secure_filename


def authenticate_user(email, password):
    """验证用户登录"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if not user:
        return None, '用户不存在'
    
    if user['is_banned']:
        return None, '账号已被禁用，请联系管理员'
    
    try:
        if check_password_hash(user['password_hash'], password):
            return dict(user), None
        else:
            return None, '密码错误'
    except Exception as e:
        return None, f'登录过程中出现错误: {str(e)}'


def register_user(username, email, password, invite_code):
    """注册新用户"""
    db = get_db()
    
    # 检查用户名和邮箱是否已存在
    if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
        return None, '用户名已被使用'
    
    if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
        return None, '邮箱已被注册'
    
    # 检查邀请码
    invite = db.execute('SELECT * FROM invite_codes WHERE code = ? AND is_used = 0', 
                      (invite_code,)).fetchone()
    if not invite:
        return None, '无效的邀请码'
    
    # 检查是否是第一个用户（自动设为管理员）
    is_admin = db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count'] == 0
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    try:
        db.execute(
            'INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
            (username, email, password_hash, is_admin)
        )
        user_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # 标记邀请码为已使用
        db.execute(
            'UPDATE invite_codes SET is_used = 1, used_at = CURRENT_TIMESTAMP, used_by = ? WHERE code = ?',
            (user_id, invite_code)
        )
        
        db.commit()
        return user_id, None
    except Exception as e:
        db.rollback()
        return None, f'注册过程中出现错误: {str(e)}'


def get_user_by_id(user_id):
    """根据ID获取用户信息"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return dict(user) if user else None


def get_user_profile(user_id):
    """获取用户资料（包含统计信息）"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        return None
    
    user = dict(user)
    
    # 获取统计信息
    user['prompt_count'] = db.execute(
        'SELECT COUNT(*) as count FROM prompts WHERE user_id = ?',
        (user_id,)
    ).fetchone()['count']
    
    user['total_views'] = db.execute(
        'SELECT SUM(view_count) as total FROM prompts WHERE user_id = ?',
        (user_id,)
    ).fetchone()['total'] or 0
    
    return user


def update_user_profile(user_id, username=None, bio=None, avatar_file=None):
    """更新用户资料"""
    db = get_db()
    
    # 检查用户名是否已被其他用户使用
    if username:
        existing = db.execute(
            'SELECT id FROM users WHERE username = ? AND id != ?',
            (username, user_id)
        ).fetchone()
        if existing:
            return False, '用户名已被使用'
    
    # 更新基本信息
    updates = []
    params = []
    
    if username:
        updates.append('username = ?')
        params.append(username)
    
    if bio is not None:
        updates.append('bio = ?')
        params.append(bio)
    
    # 处理头像上传
    if avatar_file and avatar_file.filename:
        avatar_url = save_avatar(avatar_file, user_id)
        if avatar_url:
            updates.append('avatar_url = ?')
            params.append(avatar_url)
    
    if updates:
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        db.execute(query, params)
        db.commit()
    
    return True, None


def save_avatar(file, user_id):
    """保存用户头像"""
    from flask import current_app
    
    if not file or not file.filename:
        return None
    
    # 检查文件扩展名
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    filename = secure_filename(file.filename)
    if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return None
    
    # 生成唯一文件名
    file_ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
    
    # 使用配置中的上传目录
    avatars_dir = current_app.config.get('UPLOAD_FOLDER')
    if not avatars_dir:
        avatars_dir = os.path.join('app', 'static', 'img', 'avatars')
    
    # 确保目录存在
    if not os.path.exists(avatars_dir):
        os.makedirs(avatars_dir, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(avatars_dir, unique_filename)
    file.save(file_path)
    
    # 返回相对路径（用于URL）
    return f"static/img/avatars/{unique_filename}"


def change_password(user_id, old_password, new_password):
    """修改密码"""
    db = get_db()
    user = db.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        return False, '用户不存在'
    
    # 验证旧密码
    if not check_password_hash(user['password_hash'], old_password):
        return False, '原密码错误'
    
    # 更新密码
    new_password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
    db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_password_hash, user_id))
    db.commit()
    
    return True, None

