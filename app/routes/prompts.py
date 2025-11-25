"""
提示词相关路由
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from app.database import get_db
from app.utils.decorators import login_required
from app.utils.helpers import format_datetime
from app.services.tag_service import link_tags_to_prompt
from flask import current_app

bp = Blueprint('prompts', __name__)


def ensure_favorites_table():
    """确保收藏表存在"""
    db = get_db()
    db.execute('''
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        prompt_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (prompt_id) REFERENCES prompts (id),
        UNIQUE(user_id, prompt_id)
    )
    ''')
    db.commit()


@bp.route('/create-prompt', methods=['GET', 'POST'])
@bp.route('/prompts/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建提示词"""
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        description = request.form['description']
        is_public = 'is_public' in request.form
        tag_names = request.form.getlist('tags')
        
        error = None
        
        if not title:
            error = '标题不能为空'
        elif not content:
            error = '内容不能为空'
        
        if error:
            flash(error, 'danger')
        else:
            db = get_db()
            
            # 插入提示词
            db.execute(
                'INSERT INTO prompts (title, content, description, version, user_id, is_public) VALUES (?, ?, ?, ?, ?, ?)',
                (title, content, description, request.form.get('version', '1.0'), session['user_id'], is_public)
            )
            prompt_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            # 处理标签
            link_tags_to_prompt(db, prompt_id, tag_names)
            
            db.commit()
            flash('提示词创建成功', 'success')
            return redirect(url_for('prompts.my_prompts'))
    
    # 获取所有标签，用于标签选择器
    db = get_db()
    tags = db.execute('SELECT name FROM tags ORDER BY name').fetchall()
    
    return render_template('prompts/create.html', tags=tags)


@bp.route('/my-prompts')
@login_required
def my_prompts():
    """我的提示词列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 9
    
    db = get_db()
    
    # 计算总数
    total_count = db.execute(
        'SELECT COUNT(*) as count FROM prompts WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()['count']
    
    # 计算总页数
    total_pages = (total_count + per_page - 1) // per_page
    
    # 确保page在有效范围内
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # 获取提示词数据
    prompt_rows = db.execute(
        'SELECT p.*, u.username FROM prompts p JOIN users u ON p.user_id = u.id WHERE p.user_id = ? ORDER BY p.created_at DESC LIMIT ? OFFSET ?',
        (session['user_id'], per_page, (page - 1) * per_page)
    ).fetchall()
    
    prompts = [dict(row) for row in prompt_rows]
    
    # 获取所有提示词的标签
    for prompt in prompts:
        tags = db.execute(
            'SELECT t.* FROM tags t '
            'JOIN tags_prompts tp ON t.id = tp.tag_id '
            'WHERE tp.prompt_id = ?',
            (prompt['id'],)
        ).fetchall()
        prompt['tags'] = tags
        
        # 格式化日期时间
        if 'created_at' in prompt and prompt['created_at']:
            prompt['created_at'] = format_datetime(prompt['created_at'])
        if 'updated_at' in prompt and prompt['updated_at']:
            prompt['updated_at'] = format_datetime(prompt['updated_at'])
    
    return render_template(
        'prompts/my_prompts.html', 
        prompts=prompts,
        current_page=page, 
        total_pages=total_pages,
        total_count=total_count
    )


@bp.route('/prompts/<int:id>')
def view(id):
    """查看提示词"""
    db = get_db()
    prompt = db.execute(
        'SELECT p.*, u.username, u.avatar_url FROM prompts p JOIN users u ON p.user_id = u.id WHERE p.id = ?',
        (id,)
    ).fetchone()
    
    if not prompt:
        flash('提示词不存在', 'danger')
        return redirect(url_for('main.index'))
    
    prompt = dict(prompt)
    
    # 格式化日期时间
    if 'created_at' in prompt and prompt['created_at']:
        prompt['created_at'] = format_datetime(prompt['created_at'])
    if 'updated_at' in prompt and prompt['updated_at']:
        prompt['updated_at'] = format_datetime(prompt['updated_at'])
    
    # 检查权限
    if not prompt['is_public'] and ('user_id' not in session or session['user_id'] != prompt['user_id']):
        flash('您没有权限查看此提示词', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取标签
    tags = db.execute(
        'SELECT t.* FROM tags t JOIN tags_prompts tp ON t.id = tp.tag_id WHERE tp.prompt_id = ?',
        (id,)
    ).fetchall()
    
    # 更新浏览计数
    db.execute('UPDATE prompts SET view_count = view_count + 1 WHERE id = ?', (id,))
    db.commit()
    
    # 检查当前用户是否已收藏该提示词
    is_favorited = False
    if 'user_id' in session:
        favorite = db.execute(
            'SELECT * FROM favorites WHERE user_id = ? AND prompt_id = ?',
            (session['user_id'], id)
        ).fetchone()
        is_favorited = favorite is not None
    
    return render_template('prompts/view.html', prompt=prompt, tags=tags, is_favorited=is_favorited)


@bp.route('/edit-prompt/<int:id>', methods=['GET', 'POST'])
@bp.route('/prompts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑提示词"""
    db = get_db()
    prompt = db.execute(
        'SELECT * FROM prompts WHERE id = ?',
        (id,)
    ).fetchone()
    
    if not prompt:
        flash('提示词不存在', 'danger')
        return redirect(url_for('main.index'))
    
    # 检查权限
    if prompt['user_id'] != session['user_id']:
        flash('您没有权限编辑此提示词', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取当前标签
    current_tags = db.execute(
        'SELECT t.name FROM tags t JOIN tags_prompts tp ON t.id = tp.tag_id WHERE tp.prompt_id = ?',
        (id,)
    ).fetchall()
    current_tag_names = [tag['name'] for tag in current_tags]
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        description = request.form['description']
        version = request.form.get('version', '1.0')
        is_public = 'is_public' in request.form
        tag_names = request.form.getlist('tags')
        
        error = None
        
        if not title:
            error = '标题不能为空'
        elif not content:
            error = '内容不能为空'
        
        if error:
            flash(error, 'danger')
        else:
            # 更新提示词
            db.execute(
                'UPDATE prompts SET title = ?, content = ?, description = ?, version = ?, is_public = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (title, content, description, version, is_public, id)
            )
            
            # 删除旧的标签关联
            db.execute('DELETE FROM tags_prompts WHERE prompt_id = ?', (id,))
            
            # 添加新的标签关联
            link_tags_to_prompt(db, id, tag_names)
            
            db.commit()
            flash('提示词更新成功', 'success')
            return redirect(url_for('prompts.my_prompts'))
    
    # 获取所有标签，用于标签选择器
    all_tags = db.execute('SELECT name FROM tags ORDER BY name').fetchall()
    
    return render_template('prompts/edit.html', prompt=prompt, current_tags=','.join(current_tag_names), all_tags=all_tags)


@bp.route('/delete-prompt/<int:id>')
@login_required
def delete(id):
    """删除提示词"""
    db = get_db()
    
    prompt = db.execute('SELECT * FROM prompts WHERE id = ?', (id,)).fetchone()
    
    if not prompt:
        flash('提示词不存在', 'danger')
        return redirect(url_for('prompts.my_prompts'))
    
    # 检查权限
    if prompt['user_id'] != session['user_id']:
        flash('您没有权限删除此提示词', 'danger')
        return redirect(url_for('prompts.my_prompts'))
    
    try:
        # 删除提示词相关的标签关联
        db.execute('DELETE FROM tags_prompts WHERE prompt_id = ?', (id,))
        
        # 删除提示词的收藏记录
        db.execute('DELETE FROM favorites WHERE prompt_id = ?', (id,))
        
        # 删除提示词
        db.execute('DELETE FROM prompts WHERE id = ?', (id,))
        
        db.commit()
        flash('提示词已成功删除', 'success')
    except Exception as e:
        db.rollback()
        current_app.logger.error(f'删除提示词时出错: {str(e)}')
        flash(f'删除提示词时出错: {str(e)}', 'danger')
    
    return redirect(url_for('prompts.my_prompts'))


@bp.route('/prompts/all')
def all_prompts():
    """所有公开提示词"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    tag_filter = request.args.get('tag', '')
    
    db = get_db()
    
    if tag_filter:
        total_count = db.execute(
            'SELECT COUNT(DISTINCT p.id) as count FROM prompts p '
            'JOIN tags_prompts tp ON p.id = tp.prompt_id '
            'JOIN tags t ON tp.tag_id = t.id '
            'WHERE p.is_public = 1 AND t.name = ?',
            (tag_filter,)
        ).fetchone()['count']
        
        prompt_rows = db.execute(
            'SELECT DISTINCT p.*, u.username FROM prompts p '
            'JOIN users u ON p.user_id = u.id '
            'JOIN tags_prompts tp ON p.id = tp.prompt_id '
            'JOIN tags t ON tp.tag_id = t.id '
            'WHERE p.is_public = 1 AND t.name = ? '
            'ORDER BY p.created_at DESC '
            'LIMIT ? OFFSET ?',
            (tag_filter, per_page, (page - 1) * per_page)
        ).fetchall()
    else:
        total_count = db.execute(
            'SELECT COUNT(*) as count FROM prompts WHERE is_public = 1'
        ).fetchone()['count']
        
        prompt_rows = db.execute(
            'SELECT p.*, u.username FROM prompts p '
            'JOIN users u ON p.user_id = u.id '
            'WHERE p.is_public = 1 '
            'ORDER BY p.created_at DESC '
            'LIMIT ? OFFSET ?',
            (per_page, (page - 1) * per_page)
        ).fetchall()
    
    total_pages = (total_count + per_page - 1) // per_page
    
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    prompts = [dict(row) for row in prompt_rows]
    
    # 获取所有提示词的标签
    for prompt in prompts:
        tags = db.execute(
            'SELECT t.* FROM tags t '
            'JOIN tags_prompts tp ON t.id = tp.tag_id '
            'WHERE tp.prompt_id = ?',
            (prompt['id'],)
        ).fetchall()
        prompt['tags'] = tags
        
        # 格式化日期时间
        if 'created_at' in prompt and prompt['created_at']:
            prompt['created_at'] = format_datetime(prompt['created_at'])
        if 'updated_at' in prompt and prompt['updated_at']:
            prompt['updated_at'] = format_datetime(prompt['updated_at'])
    
    # 获取所有标签，用于筛选
    all_tags = db.execute(
        'SELECT t.*, COUNT(tp.prompt_id) as count FROM tags t '
        'JOIN tags_prompts tp ON t.id = tp.tag_id '
        'JOIN prompts p ON tp.prompt_id = p.id '
        'WHERE p.is_public = 1 '
        'GROUP BY t.id '
        'ORDER BY count DESC'
    ).fetchall()
    
    return render_template(
        'prompts/all.html', 
        prompts=prompts,
        tags=all_tags,
        current_page=page, 
        total_pages=total_pages,
        total_count=total_count,
        current_tag=tag_filter
    )


@bp.route('/prompts/<int:id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(id):
    """切换提示词的收藏状态"""
    user_id = session['user_id']
    db = get_db()
    
    # 检查提示词是否存在
    prompt = db.execute('SELECT * FROM prompts WHERE id = ?', (id,)).fetchone()
    if not prompt:
        return jsonify({'success': False, 'message': '提示词不存在'}), 404
    
    # 检查提示词是否为公开提示词或用户自己的提示词
    if not prompt['is_public'] and prompt['user_id'] != user_id:
        return jsonify({'success': False, 'message': '无法收藏私有提示词'}), 403
    
    # 检查是否已收藏
    existing = db.execute(
        'SELECT * FROM favorites WHERE user_id = ? AND prompt_id = ?',
        (user_id, id)
    ).fetchone()
    
    try:
        if existing:
            db.execute(
                'DELETE FROM favorites WHERE user_id = ? AND prompt_id = ?',
                (user_id, id)
            )
            is_favorited = False
            action = '取消收藏'
        else:
            db.execute(
                'INSERT INTO favorites (user_id, prompt_id) VALUES (?, ?)',
                (user_id, id)
            )
            is_favorited = True
            action = '收藏'
        
        db.commit()
        return jsonify({
            'success': True, 
            'is_favorited': is_favorited,
            'message': f'成功{action}提示词'
        })
    except Exception as e:
        db.rollback()
        current_app.logger.error(f'收藏操作失败: {str(e)}')
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500


@bp.route('/search')
def search():
    """搜索提示词"""
    query = request.args.get('q', '')
    tag = request.args.get('tag', '')
    
    db = get_db()
    
    if 'user_id' in session:
        user_id = session['user_id']
        if query and tag:
            prompts = db.execute(
                'SELECT DISTINCT p.*, u.username FROM prompts p '
                'JOIN users u ON p.user_id = u.id '
                'JOIN tags_prompts tp ON p.id = tp.prompt_id '
                'JOIN tags t ON tp.tag_id = t.id '
                'WHERE (p.is_public = 1 OR p.user_id = ?) AND t.name = ? '
                'AND (p.title LIKE ? OR p.content LIKE ? OR p.description LIKE ?) '
                'ORDER BY p.created_at DESC',
                (user_id, tag, f'%{query}%', f'%{query}%', f'%{query}%')
            ).fetchall()
        elif query:
            prompts = db.execute(
                'SELECT p.*, u.username FROM prompts p '
                'JOIN users u ON p.user_id = u.id '
                'WHERE (p.is_public = 1 OR p.user_id = ?) '
                'AND (p.title LIKE ? OR p.content LIKE ? OR p.description LIKE ?) '
                'ORDER BY p.created_at DESC',
                (user_id, f'%{query}%', f'%{query}%', f'%{query}%')
            ).fetchall()
        elif tag:
            prompts = db.execute(
                'SELECT DISTINCT p.*, u.username FROM prompts p '
                'JOIN users u ON p.user_id = u.id '
                'JOIN tags_prompts tp ON p.id = tp.prompt_id '
                'JOIN tags t ON tp.tag_id = t.id '
                'WHERE (p.is_public = 1 OR p.user_id = ?) AND t.name = ? '
                'ORDER BY p.created_at DESC',
                (user_id, tag)
            ).fetchall()
        else:
            return redirect(url_for('main.index'))
        
        tags = db.execute(
            'SELECT DISTINCT t.* FROM tags t '
            'JOIN tags_prompts tp ON t.id = tp.tag_id '
            'JOIN prompts p ON tp.prompt_id = p.id '
            'WHERE p.is_public = 1 OR p.user_id = ? '
            'ORDER BY t.name',
            (user_id,)
        ).fetchall()
    else:
        # 未登录用户只能搜索公开的提示词
        if query and tag:
            prompts = db.execute(
                'SELECT DISTINCT p.*, u.username FROM prompts p '
                'JOIN users u ON p.user_id = u.id '
                'JOIN tags_prompts tp ON p.id = tp.prompt_id '
                'JOIN tags t ON tp.tag_id = t.id '
                'WHERE p.is_public = 1 AND t.name = ? '
                'AND (p.title LIKE ? OR p.content LIKE ? OR p.description LIKE ?) '
                'ORDER BY p.created_at DESC',
                (tag, f'%{query}%', f'%{query}%', f'%{query}%')
            ).fetchall()
        elif query:
            prompts = db.execute(
                'SELECT p.*, u.username FROM prompts p '
                'JOIN users u ON p.user_id = u.id '
                'WHERE p.is_public = 1 '
                'AND (p.title LIKE ? OR p.content LIKE ? OR p.description LIKE ?) '
                'ORDER BY p.created_at DESC',
                (f'%{query}%', f'%{query}%', f'%{query}%')
            ).fetchall()
        elif tag:
            prompts = db.execute(
                'SELECT DISTINCT p.*, u.username FROM prompts p '
                'JOIN users u ON p.user_id = u.id '
                'JOIN tags_prompts tp ON p.id = tp.prompt_id '
                'JOIN tags t ON tp.tag_id = t.id '
                'WHERE p.is_public = 1 AND t.name = ? '
                'ORDER BY p.created_at DESC',
                (tag,)
            ).fetchall()
        else:
            return redirect(url_for('main.index'))
        
        tags = db.execute(
            'SELECT DISTINCT t.* FROM tags t '
            'JOIN tags_prompts tp ON t.id = tp.tag_id '
            'JOIN prompts p ON tp.prompt_id = p.id '
            'WHERE p.is_public = 1 '
            'ORDER BY t.name'
        ).fetchall()
    
    # 为每个prompt添加标签信息
    prompts_with_tags = []
    for prompt_row in prompts:
        prompt = dict(prompt_row)
        prompt_tags = db.execute(
            'SELECT t.* FROM tags t '
            'JOIN tags_prompts tp ON t.id = tp.tag_id '
            'WHERE tp.prompt_id = ?',
            (prompt['id'],)
        ).fetchall()
        prompt['tags'] = prompt_tags
        prompts_with_tags.append(prompt)
    
    prompts = prompts_with_tags
    
    return render_template('search.html', prompts=prompts, tags=tags, query=query, selected_tag=tag)

