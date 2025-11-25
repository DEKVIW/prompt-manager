"""
认证相关路由
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db
from flask import current_app
import datetime

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        error = None
        db = get_db()
        
        if not email:
            error = '请输入邮箱'
        elif not password:
            error = '请输入密码'
        
        if not error:
            user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            
            if not user:
                error = '用户不存在'
            elif user['is_banned']:
                error = '账号已被禁用，请联系管理员'
            else:
                try:
                    if check_password_hash(user['password_hash'], password):
                        session.clear()
                        session['user_id'] = user['id']
                        session['username'] = user['username']
                        session['is_admin'] = user['is_admin']
                        if user['avatar_url']:
                            session['avatar_url'] = user['avatar_url']
                        
                        return redirect(url_for('main.index'))
                    else:
                        error = '密码错误'
                except Exception as e:
                    current_app.logger.error(f"密码验证过程中出错: {str(e)}")
                    error = '登录过程中出现错误'
        
        flash(error, 'danger')
    
    now = datetime.datetime.now()
    return render_template('auth/login.html', now=now)


@bp.route('/logout')
def logout():
    """用户登出"""
    session.clear()
    flash('您已成功退出登录', 'success')
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        invite_code = request.form['invite_code']
        
        db = get_db()
        error = None
        
        if not username or not email or not password or not password2 or not invite_code:
            error = '所有字段都是必填的'
        elif password != password2:
            error = '两次输入的密码不匹配'
        elif len(password) < 8:
            error = '密码长度必须至少为8个字符'
        
        if not error:
            if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
                error = '用户名已被使用'
            elif db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
                error = '邮箱已被注册'
        
        if not error:
            invite = db.execute('SELECT * FROM invite_codes WHERE code = ? AND is_used = 0', 
                              (invite_code,)).fetchone()
            if not invite:
                error = '无效的邀请码'
        
        if error:
            flash(error, 'danger')
        else:
            is_admin = db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count'] == 0
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            
            try:
                db.execute(
                    'INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                    (username, email, password_hash, is_admin)
                )
                user_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                
                db.execute(
                    'UPDATE invite_codes SET is_used = 1, used_at = CURRENT_TIMESTAMP, used_by = ? WHERE code = ?',
                    (user_id, invite_code)
                )
                
                db.commit()
                flash('注册成功！现在您可以登录了', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.rollback()
                current_app.logger.error(f"注册用户时出错: {str(e)}")
                flash('注册过程中出现错误', 'danger')
    
    return render_template('auth/register.html')

