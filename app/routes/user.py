"""
用户相关路由
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db
from app.utils.decorators import login_required
from app.utils.helpers import format_datetime
from app.utils.file_upload import save_avatar
from app.utils.encryption import encrypt_string, decrypt_string
from app.services.ai.factory import AIClientFactory
from flask import current_app
import datetime

bp = Blueprint('user', __name__)


@bp.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    """用户个人资料"""
    db = get_db()
    
    try:
        # 获取用户信息
        user_row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user_row:
            flash('用户不存在', 'danger')
            return redirect(url_for('main.index'))
        
        profile_user = dict(user_row)
        
        # 只获取用户收藏的提示词
        prompt_rows = db.execute('''
            SELECT p.*, u.username, f.created_at as favorited_at 
            FROM favorites f
            JOIN prompts p ON f.prompt_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
        ''', (user_id,)).fetchall()
        
        prompts = [dict(row) for row in prompt_rows] if prompt_rows else []
        
        # 获取用户提示词浏览量总数
        views_count_result = db.execute('''
            SELECT COALESCE(SUM(view_count), 0) as total_views 
            FROM prompts 
            WHERE user_id = ?
        ''', (user_id,)).fetchone()
        views_count = views_count_result['total_views'] if views_count_result else 0
        
        # 获取用户收藏的提示词数量
        likes_count_result = db.execute('''
            SELECT COUNT(*) as count FROM favorites WHERE user_id = ?
        ''', (user_id,)).fetchone()
        likes_count = likes_count_result['count'] if likes_count_result else 0
        
        # 获取用户创建的提示词数量
        prompts_count_result = db.execute('''
            SELECT COUNT(*) as count FROM prompts WHERE user_id = ?
        ''', (user_id,)).fetchone()
        prompts_count = prompts_count_result['count'] if prompts_count_result else 0
        
        # 为每个提示词加载标签
        for prompt in prompts:
            try:
                tags = db.execute('''
                    SELECT t.name 
                    FROM tags t 
                    JOIN tags_prompts tp ON t.id = tp.tag_id 
                    WHERE tp.prompt_id = ?
                ''', (prompt['id'],)).fetchall()
                prompt['tags'] = [tag['name'] for tag in tags] if tags else []
                
                # 格式化日期时间
                if 'created_at' in prompt and prompt['created_at']:
                    prompt['created_at'] = format_datetime(prompt['created_at'])
                if 'updated_at' in prompt and prompt['updated_at']:
                    prompt['updated_at'] = format_datetime(prompt['updated_at'])
                if 'favorited_at' in prompt and prompt['favorited_at']:
                    prompt['favorited_at'] = format_datetime(prompt['favorited_at'])
                
                if 'view_count' not in prompt or prompt['view_count'] is None:
                    prompt['view_count'] = 0
            except Exception as e:
                current_app.logger.error(f"处理提示词数据出错: {str(e)}, 提示词ID: {prompt.get('id', 'unknown')}")
                continue
        
        # 处理profile_user的created_at
        if 'created_at' in profile_user and profile_user['created_at']:
            profile_user['created_at'] = format_datetime(profile_user['created_at'])
        
        return render_template('user/profile.html', 
                            profile_user=profile_user, 
                            prompts=prompts, 
                            views_count=views_count,
                            likes_count=likes_count, 
                            prompts_count=prompts_count,
                            now=datetime.datetime.now())
                            
    except Exception as e:
        current_app.logger.error(f"个人资料页面错误: {str(e)}")
        flash('加载个人资料时出错', 'danger')
        return redirect(url_for('main.index'))


@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑个人资料"""
    user_id = session['user_id']
    db = get_db()
    
    user_row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user_row:
        flash('用户不存在', 'danger')
        return redirect(url_for('main.index'))
    
    user = dict(user_row)
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        avatar_file = request.files.get('avatar')
        
        error = None
        if not username:
            error = '用户名不能为空'
        elif not email or '@' not in email:
            error = '请输入有效的邮箱地址'
        
        if not error:
            existing_user = db.execute(
                'SELECT * FROM users WHERE (username = ? OR email = ?) AND id != ?',
                (username, email, user_id)
            ).fetchone()
            
            if existing_user:
                if existing_user['username'] == username:
                    error = f'用户名 {username} 已被使用'
                else:
                    error = f'邮箱 {email} 已被使用'
        
        if not error and new_password:
            if not check_password_hash(user['password_hash'], current_password):
                error = '当前密码不正确'
            elif len(new_password) < 8:
                error = '新密码长度至少为8个字符'
            elif new_password != confirm_password:
                error = '新密码和确认密码不匹配'
        
        if error:
            flash(error, 'danger')
        else:
            try:
                avatar_url = None
                if avatar_file and avatar_file.filename:
                    avatar_url = save_avatar(avatar_file)
                
                if avatar_url:
                    db.execute(
                        'UPDATE users SET username = ?, email = ?, avatar_url = ? WHERE id = ?',
                        (username, email, avatar_url, user_id)
                    )
                    session['avatar_url'] = avatar_url
                else:
                    db.execute(
                        'UPDATE users SET username = ?, email = ? WHERE id = ?',
                        (username, email, user_id)
                    )
                
                if new_password:
                    hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
                    db.execute(
                        'UPDATE users SET password_hash = ? WHERE id = ?',
                        (hashed_password, user_id)
                    )
                
                db.commit()
                flash('个人资料已更新', 'success')
                session['username'] = username
                
                return redirect(url_for('user.profile', user_id=user_id))
            except Exception as e:
                db.rollback()
                current_app.logger.error(f'更新个人资料失败: {str(e)}')
                flash(f'更新失败: {str(e)}', 'danger')
    
    now = datetime.datetime.now()
    return render_template('user/edit_profile.html', user=user, now=now)


@bp.route('/ai-settings', methods=['GET', 'POST'])
@login_required
def ai_settings():
    """AI 设置页面"""
    user_id = session['user_id']
    db = get_db()
    
    # 获取现有配置
    config = db.execute(
        'SELECT * FROM ai_configs WHERE user_id = ?',
        (user_id,)
    ).fetchone()
    
    if request.method == 'POST':
        provider = request.form.get('provider', 'openai')
        api_key = request.form.get('api_key', '').strip()
        base_url = request.form.get('base_url', '').strip() or None
        model = request.form.get('model', 'gpt-3.5-turbo')
        temperature = float(request.form.get('temperature', 0.7))
        max_tokens = int(request.form.get('max_tokens', 500))
        enabled = 'enabled' in request.form
        
        error = None
        
        # 处理 API Key：
        # - 如果已有配置且用户未输入新 key（留空），则保留原 key
        # - 如果用户输入了新 key，则加密保存新 key
        # - 如果是新配置，必须提供 API Key
        if config:
            # 已有配置：留空则保留原 key，有输入则更新
            if not api_key or api_key.strip() == '':
                # 用户未输入新 key，保留原有的加密 key
                encrypted_api_key = config['api_key']
            else:
                # 用户输入了新的 key，加密并保存
                encrypted_api_key = encrypt_string(api_key)
        else:
            # 新配置，必须提供 API Key
            if not api_key or api_key.strip() == '':
                error = 'API Key 不能为空'
            else:
                encrypted_api_key = encrypt_string(api_key)
        
        # 验证其他字段
        if not error and provider == 'custom' and not base_url:
            error = '自定义 API 必须提供基础 URL'
        elif title_max_length < 5 or title_max_length > 100:
            error = '标题最大字数应在 5-100 之间'
        elif description_max_length < 10 or description_max_length > 500:
            error = '描述最大字数应在 10-500 之间'
        elif tag_count < 1 or tag_count > 20:
            error = '标签总数应在 1-20 之间'
        elif tag_two_char_count < 0 or tag_four_char_count < 0:
            error = '标签个数不能为负数'
        elif tag_two_char_count + tag_four_char_count > tag_count:
            error = '两字标签和四字标签的总数不能超过标签总数'
        
        if error:
            flash(error, 'danger')
        else:
            try:
                # encrypted_api_key 已在上面处理
                if config:
                    # 更新现有配置（不再更新生成规则配置字段）
                    db.execute('''
                        UPDATE ai_configs SET
                            provider = ?, api_key = ?, base_url = ?, model = ?,
                            temperature = ?, max_tokens = ?, enabled = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (
                        provider, encrypted_api_key, base_url, model,
                        temperature, max_tokens, enabled,
                        user_id
                    ))
                else:
                    # 创建新配置（使用默认值）
                    db.execute('''
                        INSERT INTO ai_configs (
                            user_id, provider, api_key, base_url, model,
                            temperature, max_tokens, enabled
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id, provider, encrypted_api_key, base_url, model,
                        temperature, max_tokens, enabled
                    ))
                
                db.commit()
                flash('AI 设置已保存', 'success')
                return redirect(url_for('user.ai_settings'))
                
            except Exception as e:
                db.rollback()
                current_app.logger.error(f'保存 AI 设置失败: {str(e)}')
                flash(f'保存失败: {str(e)}', 'danger')
    
    # 准备显示数据（解密 API Key 用于显示，但只显示部分）
    config_dict = dict(config) if config else None
    if config_dict and config_dict.get('api_key'):
        try:
            decrypted_key = decrypt_string(config_dict['api_key'])
            # 只显示前4位和后4位，中间用*代替
            if len(decrypted_key) > 8:
                config_dict['api_key_display'] = decrypted_key[:4] + '*' * (len(decrypted_key) - 8) + decrypted_key[-4:]
            else:
                config_dict['api_key_display'] = '*' * len(decrypted_key)
        except Exception:
            config_dict['api_key_display'] = '已配置（无法显示）'
    
    return render_template('user/ai_settings.html', config=config_dict)

