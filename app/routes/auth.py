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
        
        current_app.logger.info(f"用户登录尝试，输入: {email}")
        
        if not email:
            error = '请输入邮箱'
            current_app.logger.warning("登录失败：未输入邮箱")
        elif not password:
            error = '请输入密码'
            current_app.logger.warning("登录失败：未输入密码")
        
        if not error:
            user = None
            
            # 1. 优先尝试LDAP认证
            from app.services.ldap_service import authenticate_ldap_user, create_or_update_ldap_user
            current_app.logger.debug("尝试LDAP认证")
            ldap_success, ldap_user_info = authenticate_ldap_user(email, password)
            
            if ldap_success:
                current_app.logger.info("LDAP认证成功")
                # LDAP认证成功，创建或更新本地用户
                user = create_or_update_ldap_user(ldap_user_info)
                current_app.logger.info(f"成功创建或更新本地用户: {user['username']} (ID: {user['id']})")
            else:
                current_app.logger.debug("LDAP认证失败，尝试本地数据库认证")
                # 2. LDAP认证失败，尝试本地数据库认证
                user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
                
                if user:
                    current_app.logger.debug(f"找到本地用户: {user['username']} (ID: {user['id']})")
                    try:
                        if not check_password_hash(user['password_hash'], password):
                            user = None
                            error = '密码错误'
                            current_app.logger.warning("本地认证失败：密码错误")
                        else:
                            current_app.logger.debug("本地认证成功")
                    except Exception as e:
                        current_app.logger.error(f"密码验证过程中出错: {str(e)}")
                        error = '登录过程中出现错误'
                        user = None
                else:
                    error = '用户不存在'
                    current_app.logger.warning("本地认证失败：用户不存在")
            
            if user:
                current_app.logger.debug(f"用户认证成功，检查状态: {user['username']} (ID: {user['id']})")
                if user['is_banned']:
                    error = '账号已被禁用，请联系管理员'
                    current_app.logger.warning(f"登录失败：账号已被禁用 - {user['username']}")
                elif not user['is_approved']:
                    error = '账号待审核，请联系管理员'
                    current_app.logger.info(f"登录失败：账号待审核 - {user['username']}")
                else:
                    # 登录成功
                    session.clear()
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['is_admin'] = user['is_admin']
                    if user['avatar_url']:
                        session['avatar_url'] = user['avatar_url']
                    
                    current_app.logger.info(f"登录成功：{user['username']} (ID: {user['id']})")
                    return redirect(url_for('main.index'))
        
        flash(error, 'danger')
        current_app.logger.warning(f"登录失败：{error} - {email}")
    
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
            # 使用user_service中的register_user函数
            from app.services.user_service import register_user
            user_id, register_error = register_user(username, email, password, invite_code)
            
            if register_error:
                flash(register_error, 'danger')
            else:
                flash('注册成功！现在您可以登录了', 'success')
                return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

