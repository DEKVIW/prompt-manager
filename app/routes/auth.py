from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.forms import LoginForm, RegistrationForm
from app.models.user import User, InviteCode

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next_page = request.args.get('next')
            if next_page is None or not next_page.startswith('/'):
                next_page = url_for('main.index')
            return redirect(next_page)
        flash('邮箱或密码错误', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功退出登录', 'success')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # 验证邀请码
        invite_code = InviteCode.query.filter_by(code=form.invite_code.data, is_used=False).first()
        if not invite_code:
            flash('无效的邀请码', 'danger')
            return render_template('auth/register.html', form=form)
        
        # 创建新用户
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        
        # 如果是第一个用户，设为管理员
        if User.query.count() == 0:
            user.is_admin = True
        
        db.session.add(user)
        
        # 使用邀请码
        invite_code.use(user.id)
        
        db.session.commit()
        flash('注册成功！现在您可以登录了', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form) 