"""
管理员相关路由
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.database import get_db
from app.utils.decorators import admin_required
import random
import string
from flask import current_app

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/invite-codes', methods=['GET', 'POST'])
@admin_required
def invite_codes():
    """管理邀请码"""
    db = get_db()
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'generate':
            quantity = int(request.form.get('quantity', 1))
            
            # 生成邀请码
            for _ in range(quantity):
                code = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
                db.execute(
                    'INSERT INTO invite_codes (code, creator_id) VALUES (?, ?)',
                    (code, session['user_id'])
                )
            
            db.commit()
            flash(f'成功生成 {quantity} 个邀请码', 'success')
    
    # 获取所有邀请码
    invite_codes = db.execute(
        'SELECT ic.*, u1.username as creator_username, u2.username as used_by_username '
        'FROM invite_codes ic '
        'LEFT JOIN users u1 ON ic.creator_id = u1.id '
        'LEFT JOIN users u2 ON ic.used_by = u2.id '
        'ORDER BY ic.created_at DESC'
    ).fetchall()
    
    return render_template('admin/invite_codes.html', invite_codes=invite_codes)


@bp.route('/delete-invite-codes', methods=['POST'])
@admin_required
def delete_invite_codes():
    """删除邀请码"""
    db = get_db()
    
    code_ids = request.form.getlist('code_ids')
    
    if code_ids:
        try:
            placeholders = ','.join(['?'] * len(code_ids))
            query = f'DELETE FROM invite_codes WHERE code IN ({placeholders})'
            result = db.execute(query, code_ids)
            deleted_count = result.rowcount
            db.commit()
            flash(f'成功删除 {deleted_count} 个邀请码', 'success')
        except Exception as e:
            db.rollback()
            current_app.logger.error(f"删除邀请码出错: {str(e)}")
            flash(f'删除邀请码时出错: {str(e)}', 'danger')
    else:
        flash('未选择任何邀请码', 'warning')
    
    return redirect(url_for('admin.invite_codes'))


@bp.route('/users')
@admin_required
def users():
    """用户管理"""
    db = get_db()
    users = db.execute(
        'SELECT * FROM users ORDER BY id'
    ).fetchall()
    
    return render_template('admin/users.html', users=users)


@bp.route('/users/ban/<int:id>', methods=['POST'])
@admin_required
def ban_user(id):
    """封禁/解封用户"""
    db = get_db()
    
    user = db.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()
    if not user:
        flash('用户不存在', 'danger')
        return redirect(url_for('admin.users'))
    
    if user['is_admin']:
        flash('不能封禁管理员账号', 'danger')
        return redirect(url_for('admin.users'))
    
    is_banned = request.form.get('is_banned') == '1'
    
    # 检查字段是否存在
    if 'is_banned' not in [column[1] for column in db.execute('PRAGMA table_info(users)').fetchall()]:
        db.execute('ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT 0')
    
    db.execute('UPDATE users SET is_banned = ? WHERE id = ?', (is_banned, id))
    db.commit()
    
    if is_banned:
        flash(f'用户 {user["username"]} 已被封禁', 'success')
    else:
        flash(f'用户 {user["username"]} 已被解封', 'success')
    
    return redirect(url_for('admin.users'))


@bp.route('/users/delete/<int:id>', methods=['POST'])
@admin_required
def delete_user(id):
    """删除用户"""
    db = get_db()
    
    user = db.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()
    if not user:
        flash('用户不存在', 'danger')
        return redirect(url_for('admin.users'))
    
    if user['is_admin']:
        flash('不能删除管理员账号', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        # 删除用户创建的提示词
        prompts = db.execute('SELECT id FROM prompts WHERE user_id = ?', (id,)).fetchall()
        for prompt in prompts:
            db.execute('DELETE FROM tags_prompts WHERE prompt_id = ?', (prompt['id'],))
        
        db.execute('DELETE FROM prompts WHERE user_id = ?', (id,))
        db.execute('UPDATE invite_codes SET used_by = NULL WHERE used_by = ?', (id,))
        db.execute('DELETE FROM users WHERE id = ?', (id,))
        db.commit()
        
        flash(f'用户 {user["username"]} 及其所有内容已被删除', 'success')
    except Exception as e:
        db.rollback()
        current_app.logger.error(f'删除用户时出错: {str(e)}')
        flash(f'删除用户时出错: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users'))

