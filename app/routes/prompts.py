import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.forms import PromptForm
from app.models.prompt import Prompt, Tag

prompts = Blueprint('prompts', __name__)

def save_image(file):
    """保存上传的图片文件"""
    if not file:
        return None
    
    filename = secure_filename(file.filename)
    # 生成唯一文件名
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    # 确保上传目录存在
    upload_folder = os.path.join(current_app.static_folder, 'img', 'covers')
    os.makedirs(upload_folder, exist_ok=True)
    # 保存文件
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    # 返回相对路径
    return f'/static/img/covers/{unique_filename}'

@prompts.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = PromptForm()
    if form.validate_on_submit():
        # 处理封面图片
        cover_image_path = save_image(form.cover_image.data) if form.cover_image.data else None
        
        # 创建新提示词
        prompt = Prompt(
            title=form.title.data,
            content=form.content.data,
            description=form.description.data,
            version=form.version.data,
            cover_image=cover_image_path,
            user_id=current_user.id,
            is_public=form.is_public.data
        )
        
        # 处理标签
        if form.tags.data:
            tags_list = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
            for tag_name in tags_list:
                prompt.add_tag(tag_name)
        
        db.session.add(prompt)
        db.session.commit()
        
        flash('提示词创建成功！', 'success')
        return redirect(url_for('prompts.view', id=prompt.id))
    
    return render_template('prompts/create.html', form=form)

@prompts.route('/<int:id>')
def view(id):
    prompt = Prompt.query.get_or_404(id)
    
    # 检查权限：私有提示词只能被创建者查看
    if not prompt.is_public and (not current_user.is_authenticated or prompt.user_id != current_user.id):
        abort(403)
    
    # 增加查看次数
    prompt.increment_view()
    db.session.commit()
    
    return render_template('prompts/view.html', prompt=prompt)

@prompts.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    prompt = Prompt.query.get_or_404(id)
    
    # 检查权限：只有创建者可以编辑
    if prompt.user_id != current_user.id:
        abort(403)
    
    form = PromptForm()
    
    if form.validate_on_submit():
        # 更新提示词信息
        prompt.title = form.title.data
        prompt.content = form.content.data
        prompt.description = form.description.data
        prompt.version = form.version.data
        prompt.is_public = form.is_public.data
        
        # 处理封面图片
        if form.cover_image.data:
            prompt.cover_image = save_image(form.cover_image.data)
        
        # 处理标签
        # 先清除所有现有标签
        for tag in prompt.tags.all():
            prompt.tags.remove(tag)
            
        # 添加新标签
        if form.tags.data:
            tags_list = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
            for tag_name in tags_list:
                prompt.add_tag(tag_name)
        
        db.session.commit()
        flash('提示词更新成功！', 'success')
        return redirect(url_for('prompts.view', id=prompt.id))
    
    # 表单预填充
    form.title.data = prompt.title
    form.content.data = prompt.content
    form.description.data = prompt.description
    form.version.data = prompt.version
    form.is_public.data = prompt.is_public
    
    # 填充标签
    tags = [tag.name for tag in prompt.tags.all()]
    form.tags.data = ', '.join(tags)
    
    return render_template('prompts/edit.html', form=form, prompt=prompt)

@prompts.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    prompt = Prompt.query.get_or_404(id)
    
    # 检查权限：只有创建者可以删除
    if prompt.user_id != current_user.id:
        abort(403)
    
    # 删除关联的封面图片
    if prompt.cover_image:
        try:
            # 从URL中提取文件路径
            file_path = os.path.join(current_app.static_folder, prompt.cover_image.lstrip('/static/'))
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            current_app.logger.error(f"删除图片失败: {e}")
    
    db.session.delete(prompt)
    db.session.commit()
    
    flash('提示词已成功删除', 'success')
    return redirect(url_for('main.index'))

@prompts.route('/<int:id>/share')
@login_required
def share(id):
    prompt = Prompt.query.get_or_404(id)
    
    # 检查权限
    if prompt.user_id != current_user.id and not prompt.is_public:
        abort(403)
    
    # 增加分享计数
    prompt.increment_share()
    db.session.commit()
    
    # 返回分享链接
    share_url = url_for('prompts.view', id=prompt.id, _external=True)
    return jsonify({'success': True, 'url': share_url})

@prompts.route('/my-prompts')
@login_required
def my_prompts():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # 获取当前用户的所有提示词
    query = Prompt.query.filter_by(user_id=current_user.id).order_by(Prompt.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page)
    prompts = pagination.items
    
    return render_template('prompts/my_prompts.html', 
                           prompts=prompts, 
                           pagination=pagination) 