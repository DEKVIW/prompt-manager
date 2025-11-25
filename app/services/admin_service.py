"""
管理员业务逻辑
"""
from app.database import get_db
import random
import string


def generate_invite_code(creator_id):
    """生成单个邀请码"""
    code = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
    db = get_db()
    db.execute(
        'INSERT INTO invite_codes (code, creator_id) VALUES (?, ?)',
        (code, creator_id)
    )
    db.commit()
    return code


def generate_invite_codes(creator_id, quantity):
    """批量生成邀请码"""
    codes = []
    db = get_db()
    
    for _ in range(quantity):
        code = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
        db.execute(
            'INSERT INTO invite_codes (code, creator_id) VALUES (?, ?)',
            (code, creator_id)
        )
        codes.append(code)
    
    db.commit()
    return codes


def get_all_invite_codes():
    """获取所有邀请码"""
    db = get_db()
    invite_codes = db.execute(
        'SELECT ic.*, u1.username as creator_username, u2.username as used_by_username '
        'FROM invite_codes ic '
        'LEFT JOIN users u1 ON ic.creator_id = u1.id '
        'LEFT JOIN users u2 ON ic.used_by = u2.id '
        'ORDER BY ic.created_at DESC'
    ).fetchall()
    
    return [dict(row) for row in invite_codes]


def delete_invite_codes(code_ids):
    """删除邀请码"""
    db = get_db()
    
    if not code_ids:
        return 0
    
    try:
        placeholders = ','.join(['?'] * len(code_ids))
        query = f'DELETE FROM invite_codes WHERE code IN ({placeholders})'
        result = db.execute(query, code_ids)
        deleted_count = result.rowcount
        db.commit()
        return deleted_count
    except Exception as e:
        db.rollback()
        raise Exception(f'删除邀请码时出错: {str(e)}')


def get_all_users():
    """获取所有用户"""
    db = get_db()
    users = db.execute('SELECT * FROM users ORDER BY id').fetchall()
    return [dict(row) for row in users]


def ban_user(user_id, is_banned):
    """封禁/解封用户"""
    db = get_db()
    
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        raise ValueError('用户不存在')
    
    if user['is_admin']:
        raise PermissionError('不能封禁管理员账号')
    
    # 检查字段是否存在
    columns = [column[1] for column in db.execute('PRAGMA table_info(users)').fetchall()]
    if 'is_banned' not in columns:
        db.execute('ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT 0')
    
    db.execute('UPDATE users SET is_banned = ? WHERE id = ?', (is_banned, user_id))
    db.commit()
    
    return dict(user)


def delete_user(user_id):
    """删除用户"""
    db = get_db()
    
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        raise ValueError('用户不存在')
    
    if user['is_admin']:
        raise PermissionError('不能删除管理员账号')
    
    try:
        # 删除用户创建的提示词
        prompts = db.execute('SELECT id FROM prompts WHERE user_id = ?', (user_id,)).fetchall()
        for prompt in prompts:
            db.execute('DELETE FROM tags_prompts WHERE prompt_id = ?', (prompt['id'],))
        
        db.execute('DELETE FROM prompts WHERE user_id = ?', (user_id,))
        db.execute('UPDATE invite_codes SET used_by = NULL WHERE used_by = ?', (user_id,))
        db.execute('DELETE FROM favorites WHERE user_id = ?', (user_id,))
        db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        db.commit()
        
        return dict(user)
    except Exception as e:
        db.rollback()
        raise Exception(f'删除用户时出错: {str(e)}')

