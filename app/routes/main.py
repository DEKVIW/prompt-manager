from flask import Blueprint, render_template, request, current_app
from flask_login import login_required, current_user
from app.models.prompt import Prompt, Tag
from sqlalchemy import or_

main = Blueprint('main', __name__)

@main.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 12  # 每页显示12个提示词卡片
    
    # 如果用户已登录，显示他们的提示词和公开的提示词
    if current_user.is_authenticated:
        query = Prompt.query.filter(
            or_(
                Prompt.user_id == current_user.id,
                Prompt.is_public == True
            )
        )
    # 否则只显示公开的提示词
    else:
        query = Prompt.query.filter_by(is_public=True)
    
    # 排序：最新创建的在前
    query = query.order_by(Prompt.created_at.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    prompts = pagination.items
    
    # 获取所有标签供搜索使用
    tags = Tag.query.all()
    
    return render_template('index.html', 
                           prompts=prompts, 
                           pagination=pagination,
                           tags=tags)

@main.route('/search')
def search():
    query = request.args.get('q', '')
    tag = request.args.get('tag', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # 构建搜索查询
    search_query = Prompt.query
    
    # 如果未登录，只显示公开的提示词
    if not current_user.is_authenticated:
        search_query = search_query.filter_by(is_public=True)
    else:
        # 如果已登录，显示用户自己的和公开的提示词
        search_query = search_query.filter(
            or_(
                Prompt.user_id == current_user.id,
                Prompt.is_public == True
            )
        )
    
    # 按标签筛选
    if tag:
        search_query = search_query.join(Prompt.tags).filter(Tag.name == tag)
    
    # 按关键词搜索
    if query:
        search_terms = f"%{query}%"
        search_query = search_query.filter(
            or_(
                Prompt.title.ilike(search_terms),
                Prompt.content.ilike(search_terms),
                Prompt.description.ilike(search_terms),
                Prompt._metadata.ilike(search_terms)
            )
        )
    
    # 排序和分页
    search_query = search_query.order_by(Prompt.created_at.desc())
    pagination = search_query.paginate(page=page, per_page=per_page)
    results = pagination.items
    
    # 获取所有标签供搜索使用
    tags = Tag.query.all()
    
    return render_template('search.html', 
                           results=results, 
                           query=query,
                           tag=tag,
                           tags=tags,
                           pagination=pagination) 