"""
提示词业务逻辑
"""
from app.database import get_db
from app.services.tag_service import link_tags_to_prompt
from app.utils.helpers import format_datetime


def create_prompt(user_id, title, content, description, version, is_public, tag_names):
    """创建提示词"""
    db = get_db()
    
    # 插入提示词
    db.execute(
        'INSERT INTO prompts (title, content, description, version, user_id, is_public) VALUES (?, ?, ?, ?, ?, ?)',
        (title, content, description, version, user_id, is_public)
    )
    prompt_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    
    # 处理标签
    link_tags_to_prompt(db, prompt_id, tag_names)
    
    db.commit()
    return prompt_id


def update_prompt(prompt_id, user_id, title, content, description, version, is_public, tag_names):
    """更新提示词"""
    db = get_db()
    
    # 检查权限
    prompt = db.execute('SELECT user_id FROM prompts WHERE id = ?', (prompt_id,)).fetchone()
    if not prompt or prompt['user_id'] != user_id:
        raise PermissionError('您没有权限编辑此提示词')
    
    # 更新提示词
    db.execute(
        'UPDATE prompts SET title = ?, content = ?, description = ?, version = ?, is_public = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (title, content, description, version, is_public, prompt_id)
    )
    
    # 删除旧标签关联
    db.execute('DELETE FROM tags_prompts WHERE prompt_id = ?', (prompt_id,))
    
    # 添加新标签
    link_tags_to_prompt(db, prompt_id, tag_names)
    
    db.commit()


def delete_prompt(prompt_id, user_id, is_admin=False):
    """删除提示词"""
    db = get_db()
    
    prompt = db.execute('SELECT * FROM prompts WHERE id = ?', (prompt_id,)).fetchone()
    if not prompt:
        raise ValueError('提示词不存在')
    
    # 检查权限
    if not is_admin and prompt['user_id'] != user_id:
        raise PermissionError('您没有权限删除此提示词')
    
    # 删除标签关联
    db.execute('DELETE FROM tags_prompts WHERE prompt_id = ?', (prompt_id,))
    
    # 删除收藏关联
    db.execute('DELETE FROM favorites WHERE prompt_id = ?', (prompt_id,))
    
    # 删除提示词
    db.execute('DELETE FROM prompts WHERE id = ?', (prompt_id,))
    
    db.commit()


def get_prompt_by_id(prompt_id, user_id=None):
    """根据ID获取提示词"""
    db = get_db()
    prompt = db.execute(
        'SELECT p.*, u.username, u.avatar_url FROM prompts p JOIN users u ON p.user_id = u.id WHERE p.id = ?',
        (prompt_id,)
    ).fetchone()
    
    if not prompt:
        return None
    
    prompt = dict(prompt)
    
    # 格式化日期时间
    if 'created_at' in prompt and prompt['created_at']:
        prompt['created_at'] = format_datetime(prompt['created_at'])
    if 'updated_at' in prompt and prompt['updated_at']:
        prompt['updated_at'] = format_datetime(prompt['updated_at'])
    
    # 检查权限
    if not prompt['is_public'] and (not user_id or user_id != prompt['user_id']):
        return None
    
    # 获取标签
    tags = db.execute(
        'SELECT t.* FROM tags t JOIN tags_prompts tp ON t.id = tp.tag_id WHERE tp.prompt_id = ?',
        (prompt_id,)
    ).fetchall()
    prompt['tags'] = tags
    
    # 更新浏览计数
    db.execute('UPDATE prompts SET view_count = view_count + 1 WHERE id = ?', (prompt_id,))
    db.commit()
    
    return prompt


def get_user_prompts(user_id, page=1, per_page=9):
    """获取用户的提示词列表"""
    db = get_db()
    
    # 计算总数
    total_count = db.execute(
        'SELECT COUNT(*) as count FROM prompts WHERE user_id = ?',
        (user_id,)
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
        (user_id, per_page, (page - 1) * per_page)
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
    
    return {
        'prompts': prompts,
        'current_page': page,
        'total_pages': total_pages,
        'total_count': total_count
    }


def get_public_prompts(page=1, per_page=9, search_query=None, tag_filter=None):
    """获取公开提示词列表"""
    db = get_db()
    
    # 构建查询
    query = 'SELECT p.*, u.username, u.avatar_url FROM prompts p JOIN users u ON p.user_id = u.id WHERE p.is_public = 1'
    params = []
    
    if search_query:
        query += ' AND (p.title LIKE ? OR p.description LIKE ?)'
        search_pattern = f'%{search_query}%'
        params.extend([search_pattern, search_pattern])
    
    if tag_filter:
        query += ' AND p.id IN (SELECT tp.prompt_id FROM tags_prompts tp JOIN tags t ON tp.tag_id = t.id WHERE t.name = ?)'
        params.append(tag_filter)
    
    # 计算总数
    count_query = query.replace('SELECT p.*, u.username, u.avatar_url', 'SELECT COUNT(*) as count')
    total_count = db.execute(count_query, params).fetchone()['count']
    
    # 计算总页数
    total_pages = (total_count + per_page - 1) // per_page
    
    # 确保page在有效范围内
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # 添加排序和分页
    query += ' ORDER BY p.view_count DESC, p.created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])
    
    # 获取提示词数据
    prompt_rows = db.execute(query, params).fetchall()
    
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
    
    return {
        'prompts': prompts,
        'current_page': page,
        'total_pages': total_pages,
        'total_count': total_count
    }


def is_favorited(user_id, prompt_id):
    """检查用户是否已收藏提示词"""
    if not user_id:
        return False
    
    db = get_db()
    favorite = db.execute(
        'SELECT * FROM favorites WHERE user_id = ? AND prompt_id = ?',
        (user_id, prompt_id)
    ).fetchone()
    
    return favorite is not None


def toggle_favorite(user_id, prompt_id):
    """切换收藏状态"""
    db = get_db()
    
    favorite = db.execute(
        'SELECT * FROM favorites WHERE user_id = ? AND prompt_id = ?',
        (user_id, prompt_id)
    ).fetchone()
    
    if favorite:
        # 取消收藏
        db.execute('DELETE FROM favorites WHERE user_id = ? AND prompt_id = ?', (user_id, prompt_id))
        is_favorited = False
    else:
        # 添加收藏
        db.execute('INSERT INTO favorites (user_id, prompt_id) VALUES (?, ?)', (user_id, prompt_id))
        is_favorited = True
    
    db.commit()
    return is_favorited

