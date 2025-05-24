import random
import string
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from app import db
from app.forms import InviteCodeForm
from app.models.user import User, InviteCode

admin = Blueprint('admin', __name__)

def require_admin(f):
    """管理员权限装饰器"""
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

def generate_invite_code(length=8):
    """生成随机邀请码"""
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    code = ''.join(random.choice(chars) for _ in range(length))
    return code

@admin.route('/dashboard')
@login_required
@require_admin
def dashboard():
    # 获取统计数据
    user_count = User.query.count()
    admin_count = User.query.filter_by(is_admin=True).count()
    
    # 未使用的邀请码数
    available_invites = InviteCode.query.filter_by(is_used=False).count()
    
    # 最近注册的用户
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                           user_count=user_count,
                           admin_count=admin_count,
                           available_invites=available_invites,
                           recent_users=recent_users)

@admin.route('/users')
@login_required
@require_admin
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 获取所有用户
    query = User.query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page)
    users = pagination.items
    
    return render_template('admin/users.html', 
                           users=users, 
                           pagination=pagination)

@admin.route('/users/<int:id>/toggle-admin', methods=['POST'])
@login_required
@require_admin
def toggle_admin(id):
    user = User.query.get_or_404(id)
    
    # 不能更改自己的管理员状态
    if user.id == current_user.id:
        flash('不能更改自己的管理员状态', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = '授予' if user.is_admin else '移除'
    flash(f'已{status} {user.username} 的管理员权限', 'success')
    
    return redirect(url_for('admin.users'))

@admin.route('/invite-codes', methods=['GET', 'POST'])
@login_required
@require_admin
def invite_codes():
    form = InviteCodeForm()
    
    if form.validate_on_submit():
        quantity = int(form.quantity.data)
        
        # 生成邀请码
        new_codes = []
        for _ in range(quantity):
            while True:
                code = generate_invite_code()
                # 确保邀请码唯一
                if not InviteCode.query.filter_by(code=code).first():
                    break
            
            invite = InviteCode(code=code, creator_id=current_user.id)
            db.session.add(invite)
            new_codes.append(invite)
        
        db.session.commit()
        flash(f'成功生成 {quantity} 个邀请码', 'success')
    
    # 获取所有邀请码
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 使用联接查询加载用户信息
    query = InviteCode.query
    pagination = query.paginate(page=page, per_page=per_page)
    invite_codes = pagination.items
    
    # 加载每个邀请码的使用者信息
    for code in invite_codes:
        if code.is_used and code.used_by:
            user = User.query.get(code.used_by)
            if user:
                code.used_by_username = user.username
            else:
                code.used_by_username = "未知用户"
        else:
            code.used_by_username = None
    
    return render_template('admin/invite_codes.html', 
                           form=form,
                           invite_codes=invite_codes, 
                           pagination=pagination) 