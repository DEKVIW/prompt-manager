import os
import sqlite3
import datetime
import random
import string
import uuid
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, redirect, url_for, flash, request, session, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载.env文件中的环境变量
    print("已加载环境变量")
except ImportError:
    print("警告: python-dotenv 未安装，环境变量将从系统获取")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')  # 从环境变量获取密钥
app.config['DATABASE'] = os.path.join('instance', 'prompts.db')

# 配置日志
def setup_logging():
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # 配置根日志记录器
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 在生产环境下，添加文件处理程序
    if not debug_mode:
        # 确保日志目录存在
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        # 创建rotating file handler，保留10个日志文件，每个文件最大10MB
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'app.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        # 添加到应用日志记录器
        app.logger.addHandler(file_handler)
    
    # 输出日志配置信息
    app.logger.info(f"应用启动于{'调试' if debug_mode else '生产'}模式")
    return debug_mode

# 设置日志
debug_mode = setup_logging()

# 添加响应头允许跨域访问
@app.after_request
def add_cors_headers(response):
    # 检查是否启用CORS，默认为生产环境禁用
    if os.environ.get('ENABLE_CORS', 'False').lower() == 'true':
        response.headers['Access-Control-Allow-Origin'] = os.environ.get('CORS_ORIGIN', '*')
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    # 添加基本安全头
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # 如果启用了HTTPS，添加严格传输安全头
    if os.environ.get('HTTPS_ENABLED', 'False').lower() == 'true':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

def get_db():
    # 确保img目录存在
    avatars_dir = os.path.join('static', 'img', 'avatars')
    if not os.path.exists(avatars_dir):
        os.makedirs(avatars_dir)
        
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        
        # 检查users表中是否有avatar_url字段
        cursor = db.cursor()
        result = cursor.execute("PRAGMA table_info(users)").fetchall()
        has_avatar_field = any(row[1] == 'avatar_url' for row in result)
        
        if not has_avatar_field:
            try:
                # 添加头像字段到users表
                cursor.execute('ALTER TABLE users ADD COLUMN avatar_url TEXT')
                db.commit()
                print("已添加avatar_url字段到users表")
            except sqlite3.Error as e:
                print(f"添加avatar_url字段时出错: {e}")
                pass
                
    return db

@app.teardown_appcontext
def close_db(error):
    if 'db' in g:
        g.db.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'danger')
            return redirect(url_for('login'))
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        if not user or not user['is_admin']:
            flash('没有管理员权限', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

def format_datetime(dt):
    """将日期时间格式化为只显示年月日"""
    if isinstance(dt, datetime.datetime) or (isinstance(dt, str) and dt):
        try:
            if isinstance(dt, str):
                dt = datetime.datetime.fromisoformat(dt.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            return dt
    return '未知时间'

@app.route('/')
def index():
    popular_prompts = []
    popular_tags = []
    
    # 统计数据
    prompt_count = 0
    user_count = 0
    view_count = 0
    
    try:
        db = get_db()
        
        # 首先检查并创建prompt_tags表（如果不存在）
        db.execute('''
            CREATE TABLE IF NOT EXISTS prompt_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER,
                tag TEXT,
                FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
            )
        ''')
        
        # 获取热门提示词
        popular_prompts = db.execute('''
            SELECT p.id, p.title, p.description, p.view_count as views, p.is_public, p.created_at, 
                   u.id as user_id, u.username
            FROM prompts p 
            JOIN users u ON p.user_id = u.id
            WHERE p.is_public = 1
            ORDER BY p.view_count DESC LIMIT 6
        ''').fetchall()
        
        # 将 Row 对象转换为可修改的字典
        popular_prompts = [dict(row) for row in popular_prompts]
        
        # 格式化时间
        for prompt in popular_prompts:
            if 'created_at' in prompt and prompt['created_at']:
                prompt['created_at'] = format_datetime(prompt['created_at'])
            if 'updated_at' in prompt and prompt['updated_at']:
                prompt['updated_at'] = format_datetime(prompt['updated_at'])
        
        # 为每个提示词获取标签
        for prompt in popular_prompts:
            prompt_id = prompt['id']
            tags = db.execute('''
                SELECT t.name 
                FROM tags t 
                JOIN tags_prompts tp ON t.id = tp.tag_id 
                WHERE tp.prompt_id = ?
            ''', (prompt_id,)).fetchall()
            
            # 转换标签为列表
            prompt['tags'] = [tag['name'] for tag in tags] if tags else []
        
        # 获取热门标签
        popular_tags = db.execute('''
            SELECT t.name, COUNT(tp.prompt_id) as count 
            FROM tags t
            JOIN tags_prompts tp ON t.id = tp.tag_id
            JOIN prompts p ON tp.prompt_id = p.id
            WHERE p.is_public = 1
            GROUP BY t.name 
            ORDER BY count DESC LIMIT 12
        ''').fetchall()
        
        # 获取真实统计数据
        # 1. 提示词总数
        prompt_count_result = db.execute('SELECT COUNT(*) as count FROM prompts').fetchone()
        prompt_count = prompt_count_result['count'] if prompt_count_result else 0
        
        # 2. 用户总数
        user_count_result = db.execute('SELECT COUNT(*) as count FROM users').fetchone()
        user_count = user_count_result['count'] if user_count_result else 0
        
        # 3. 总浏览量
        view_count_result = db.execute('SELECT COALESCE(SUM(view_count), 0) as total_views FROM prompts').fetchone()
        view_count = view_count_result['total_views'] if view_count_result else 0
        
        db.commit()
    except Exception as e:
        print(f"Error fetching data: {e}")
    
    now = datetime.datetime.now()
    return render_template('index.html', 
                          popular_prompts=popular_prompts, 
                          popular_tags=popular_tags, 
                          prompt_count=prompt_count,
                          user_count=user_count,
                          view_count=view_count,
                          now=now)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # 如果用户已登录，重定向到首页
    if 'user_id' in session:
        return redirect(url_for('index'))
    
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
            
            # 打印登录尝试信息用于调试
            if user:
                print(f"尝试登录用户: {user['username']} ({user['email']}), 密码哈希: {user['password_hash']}")
            else:
                print(f"尝试登录不存在的用户: {email}")
                
            if not user:
                error = '用户不存在'
            elif user['is_banned']:
                error = '账号已被禁用，请联系管理员'
            else:
                try:
                    # 验证密码
                    if check_password_hash(user['password_hash'], password):
                        print(f"密码验证成功")
                        # 保存用户信息到会话
                        session.clear()
                        session['user_id'] = user['id']
                        session['username'] = user['username']
                        session['is_admin'] = user['is_admin']
                        if user['avatar_url']:
                            session['avatar_url'] = user['avatar_url']
                        
                        return redirect(url_for('index'))
                    else:
                        print(f"密码验证失败")
                        error = '密码错误'
                except Exception as e:
                    print(f"密码验证过程中出错: {str(e)}")
                    error = '登录过程中出现错误'
        
        flash(error, 'danger')
    
    now = datetime.datetime.now()
    return render_template('auth/login.html', now=now)

@app.route('/logout')
def logout():
    session.clear()
    flash('您已成功退出登录', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        invite_code = request.form['invite_code']
        
        db = get_db()
        
        # 表单验证
        error = None
        
        if not username or not email or not password or not password2 or not invite_code:
            error = '所有字段都是必填的'
        elif password != password2:
            error = '两次输入的密码不匹配'
        elif len(password) < 8:
            error = '密码长度必须至少为8个字符'
        
        # 检查用户名和邮箱是否已存在
        if not error:
            if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
                error = '用户名已被使用'
            elif db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
                error = '邮箱已被注册'
        
        # 检查邀请码
        if not error:
            invite = db.execute('SELECT * FROM invite_codes WHERE code = ? AND is_used = 0', 
                              (invite_code,)).fetchone()
            if not invite:
                error = '无效的邀请码'
        
        if error:
            flash(error, 'danger')
        else:
            # 创建新用户
            is_admin = db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count'] == 0
            
            # 生成密码哈希值并输出到控制台以便调试
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            print(f"为用户 {username} 生成的密码哈希值: {password_hash}")
            
            try:
                # 插入用户数据
                db.execute(
                    'INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                    (username, email, password_hash, is_admin)
                )
                user_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                
                # 使用邀请码
                db.execute(
                    'UPDATE invite_codes SET is_used = 1, used_at = CURRENT_TIMESTAMP, used_by = ? WHERE code = ?',
                    (user_id, invite_code)
                )
                
                db.commit()
                
                # 验证用户已成功创建
                user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
                if user:
                    print(f"用户创建成功: id={user['id']}, username={user['username']}, email={user['email']}")
                    print(f"存储的密码哈希: {user['password_hash']}")
                else:
                    print(f"警告: 用户ID {user_id} 创建后未找到")
                
                flash('注册成功！现在您可以登录了', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.rollback()
                print(f"注册用户时出错: {str(e)}")
                import traceback
                traceback.print_exc()
                flash('注册过程中出现错误', 'danger')
    
    return render_template('auth/register.html')

@app.route('/admin/invite-codes', methods=['GET', 'POST'])
@admin_required
def admin_invite_codes():
    db = get_db()
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'generate':
            # 生成新邀请码
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

@app.route('/admin/delete-invite-codes', methods=['POST'])
@admin_required
def delete_invite_codes():
    db = get_db()
    
    # 获取选中的邀请码IDs
    code_ids = request.form.getlist('code_ids')
    
    if code_ids:
        try:
            # 使用参数化查询构建IN子句
            placeholders = ','.join(['?'] * len(code_ids))
            query = f'DELETE FROM invite_codes WHERE code IN ({placeholders})'
            result = db.execute(query, code_ids)
            deleted_count = result.rowcount
            db.commit()
            flash(f'成功删除 {deleted_count} 个邀请码', 'success')
        except Exception as e:
            db.rollback()
            print(f"删除邀请码出错: {str(e)}")
            flash(f'删除邀请码时出错: {str(e)}', 'danger')
    else:
        flash('未选择任何邀请码', 'warning')
    
    return redirect(url_for('admin_invite_codes'))

@app.route('/create-prompt', methods=['GET', 'POST'])
@login_required
def create_prompt():
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
            if tag_names:
                for tag_name in tag_names:
                    tag_name = tag_name.strip()
                    if tag_name:
                        # 检查标签是否存在
                        tag = db.execute('SELECT id FROM tags WHERE name = ?', (tag_name,)).fetchone()
                        if not tag:
                            # 创建新标签
                            db.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
                            tag_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                        else:
                            tag_id = tag['id']
                        
                        # 关联标签和提示词
                        db.execute('INSERT INTO tags_prompts (tag_id, prompt_id) VALUES (?, ?)', (tag_id, prompt_id))
            
            db.commit()
            flash('提示词创建成功', 'success')
            return redirect(url_for('my_prompts'))
    
    # 获取所有标签，用于标签选择器
    db = get_db()
    tags = db.execute('SELECT name FROM tags ORDER BY name').fetchall()
    
    return render_template('prompts/create.html', tags=tags)

@app.route('/prompts/create', methods=['GET', 'POST'])
@login_required
def prompts_create():
    # 复用现有的create_prompt函数逻辑
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
            if tag_names:
                for tag_name in tag_names:
                    tag_name = tag_name.strip()
                    if tag_name:
                        # 检查标签是否存在
                        tag = db.execute('SELECT id FROM tags WHERE name = ?', (tag_name,)).fetchone()
                        if not tag:
                            # 创建新标签
                            db.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
                            tag_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                        else:
                            tag_id = tag['id']
                        
                        # 关联标签和提示词
                        db.execute('INSERT INTO tags_prompts (tag_id, prompt_id) VALUES (?, ?)', (tag_id, prompt_id))
            
            db.commit()
            flash('提示词创建成功', 'success')
            return redirect(url_for('my_prompts'))
    
    # 获取所有标签，用于标签选择器
    db = get_db()
    tags = db.execute('SELECT name FROM tags ORDER BY name').fetchall()
    
    return render_template('prompts/create.html', tags=tags)

@app.route('/my-prompts')
@login_required
def my_prompts():
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 9  # 每页显示9条提示词
    
    db = get_db()
    
    # 计算总数以支持分页
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
    
    # 将Row对象转换为可修改的字典列表
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

@app.route('/prompts/<int:id>')
def view_prompt(id):
    db = get_db()
    # 修改SQL查询，包含用户头像
    prompt = db.execute(
        'SELECT p.*, u.username, u.avatar_url FROM prompts p JOIN users u ON p.user_id = u.id WHERE p.id = ?',
        (id,)
    ).fetchone()
    
    if not prompt:
        flash('提示词不存在', 'danger')
        return redirect(url_for('index'))
    
    # 转换为可修改的字典
    prompt = dict(prompt)
    
    # 格式化日期时间
    if 'created_at' in prompt and prompt['created_at']:
        prompt['created_at'] = format_datetime(prompt['created_at'])
    if 'updated_at' in prompt and prompt['updated_at']:
        prompt['updated_at'] = format_datetime(prompt['updated_at'])
    
    # 检查权限
    if not prompt['is_public'] and ('user_id' not in session or session['user_id'] != prompt['user_id']):
        flash('您没有权限查看此提示词', 'danger')
        return redirect(url_for('index'))
    
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

@app.route('/edit-prompt/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_prompt(id):
    db = get_db()
    prompt = db.execute(
        'SELECT * FROM prompts WHERE id = ?',
        (id,)
    ).fetchone()
    
    if not prompt:
        flash('提示词不存在', 'danger')
        return redirect(url_for('index'))
    
    # 检查权限
    if prompt['user_id'] != session['user_id']:
        flash('您没有权限编辑此提示词', 'danger')
        return redirect(url_for('index'))
    
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
            if tag_names:
                for tag_name in tag_names:
                    tag_name = tag_name.strip()
                    if tag_name:
                        # 检查标签是否存在
                        tag = db.execute('SELECT id FROM tags WHERE name = ?', (tag_name,)).fetchone()
                        if not tag:
                            # 创建新标签
                            db.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
                            tag_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                        else:
                            tag_id = tag['id']
                        
                        # 关联标签和提示词
                        db.execute('INSERT INTO tags_prompts (tag_id, prompt_id) VALUES (?, ?)', (tag_id, id))
            
            db.commit()
            flash('提示词更新成功', 'success')
            return redirect(url_for('my_prompts'))
    
    # 获取所有标签，用于标签选择器
    all_tags = db.execute('SELECT name FROM tags ORDER BY name').fetchall()
    
    return render_template('prompts/edit.html', prompt=prompt, current_tags=','.join(current_tag_names), all_tags=all_tags)

@app.route('/prompts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def prompts_edit(id):
    # 复用edit_prompt函数的逻辑
    db = get_db()
    prompt = db.execute(
        'SELECT * FROM prompts WHERE id = ?',
        (id,)
    ).fetchone()
    
    if not prompt:
        flash('提示词不存在', 'danger')
        return redirect(url_for('index'))
    
    # 检查权限
    if prompt['user_id'] != session['user_id']:
        flash('您没有权限编辑此提示词', 'danger')
        return redirect(url_for('index'))
    
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
                (title, content, description, request.form.get('version', '1.0'), is_public, id)
            )
            
            # 删除旧的标签关联
            db.execute('DELETE FROM tags_prompts WHERE prompt_id = ?', (id,))
            
            # 添加新的标签关联
            if tag_names:
                for tag_name in tag_names:
                    tag_name = tag_name.strip()
                    if tag_name:
                        # 检查标签是否存在
                        tag = db.execute('SELECT id FROM tags WHERE name = ?', (tag_name,)).fetchone()
                        if not tag:
                            # 创建新标签
                            db.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
                            tag_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                        else:
                            tag_id = tag['id']
                        
                        # 关联标签和提示词
                        db.execute('INSERT INTO tags_prompts (tag_id, prompt_id) VALUES (?, ?)', (tag_id, id))
            
            db.commit()
            flash('提示词更新成功', 'success')
            return redirect(url_for('my_prompts'))
    
    # 获取所有标签，用于标签选择器
    all_tags = db.execute('SELECT name FROM tags ORDER BY name').fetchall()
    
    return render_template('prompts/edit.html', prompt=prompt, current_tags=','.join(current_tag_names), all_tags=all_tags)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    tag = request.args.get('tag', '')
    
    db = get_db()
    
    if 'user_id' in session:
        user_id = session['user_id']
        if query and tag:
            # 搜索标题、内容和特定标签
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
            # 只搜索标题和内容
            prompts = db.execute(
                'SELECT p.*, u.username FROM prompts p '
                'JOIN users u ON p.user_id = u.id '
                'WHERE (p.is_public = 1 OR p.user_id = ?) '
                'AND (p.title LIKE ? OR p.content LIKE ? OR p.description LIKE ?) '
                'ORDER BY p.created_at DESC',
                (user_id, f'%{query}%', f'%{query}%', f'%{query}%')
            ).fetchall()
        elif tag:
            # 只搜索标签
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
            # 没有搜索条件
            return redirect(url_for('index'))
        
        # 获取所有标签，用于标签过滤（只显示与公开或用户自己的提示词相关的标签）
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
            # 没有搜索条件
            return redirect(url_for('index'))
        
        # 获取所有标签，用于标签过滤（只显示与公开提示词相关的标签）
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
        prompt = dict(prompt_row)  # 转换为可修改的字典
        # 获取该提示词的标签
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

@app.route('/admin/users')
@admin_required
def admin_users():
    db = get_db()
    users = db.execute(
        'SELECT * FROM users ORDER BY id'
    ).fetchall()
    
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/ban/<int:id>', methods=['POST'])
@admin_required
def admin_ban_user(id):
    db = get_db()
    
    # 检查用户是否存在
    user = db.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()
    if not user:
        flash('用户不存在', 'danger')
        return redirect(url_for('admin_users'))
    
    # 检查是否试图封禁管理员
    if user['is_admin']:
        flash('不能封禁管理员账号', 'danger')
        return redirect(url_for('admin_users'))
    
    # 检查当前状态
    is_banned = request.form.get('is_banned') == '1'
    
    # 更新用户状态
    if 'is_banned' not in [column[1] for column in db.execute('PRAGMA table_info(users)').fetchall()]:
        # 添加banned字段到users表
        db.execute('ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT 0')
    
    db.execute('UPDATE users SET is_banned = ? WHERE id = ?', (is_banned, id))
    db.commit()
    
    if is_banned:
        flash(f'用户 {user["username"]} 已被封禁', 'success')
    else:
        flash(f'用户 {user["username"]} 已被解封', 'success')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_user(id):
    db = get_db()
    
    # 检查用户是否存在
    user = db.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()
    if not user:
        flash('用户不存在', 'danger')
        return redirect(url_for('admin_users'))
    
    # 检查是否试图删除管理员
    if user['is_admin']:
        flash('不能删除管理员账号', 'danger')
        return redirect(url_for('admin_users'))
    
    try:
        # 删除用户创建的提示词
        prompts = db.execute('SELECT id FROM prompts WHERE user_id = ?', (id,)).fetchall()
        for prompt in prompts:
            # 删除提示词相关的标签关联
            db.execute('DELETE FROM tags_prompts WHERE prompt_id = ?', (prompt['id'],))
        
        # 删除用户的提示词
        db.execute('DELETE FROM prompts WHERE user_id = ?', (id,))
        
        # 清理邀请码关联
        db.execute('UPDATE invite_codes SET used_by = NULL WHERE used_by = ?', (id,))
        
        # 删除用户
        db.execute('DELETE FROM users WHERE id = ?', (id,))
        db.commit()
        
        flash(f'用户 {user["username"]} 及其所有内容已被删除', 'success')
    except Exception as e:
        db.rollback()
        flash(f'删除用户时出错: {str(e)}', 'danger')
    
    return redirect(url_for('admin_users'))

@app.route('/profile/<int:user_id>')
def profile(user_id):
    # 确保用户已登录
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('login'))
    
    db = get_db()
    
    try:
        # 获取用户信息
        user_row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user_row:
            flash('用户不存在', 'danger')
            return redirect(url_for('index'))
        
        # 将Row对象转换为可修改的字典
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
                
                # 确保view_count字段存在并有默认值
                if 'view_count' not in prompt or prompt['view_count'] is None:
                    prompt['view_count'] = 0
            except Exception as e:
                print(f"处理提示词数据出错: {str(e)}, 提示词ID: {prompt.get('id', 'unknown')}")
                # 继续处理下一个提示词，而不是中断整个循环
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
        print(f"个人资料页面错误: {str(e)}")
        import traceback
        traceback.print_exc()  # 输出完整的错误堆栈跟踪
        flash('加载个人资料时出错', 'danger')
        return redirect(url_for('index'))

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    # 确保用户已登录
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    db = get_db()
    
    # 获取用户信息
    user_row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user_row:
        flash('用户不存在', 'danger')
        return redirect(url_for('index'))
    
    # 将Row对象转换为可修改的字典
    user = dict(user_row)
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 获取上传的头像文件
        avatar_file = request.files.get('avatar')
        
        # 验证表单
        error = None
        if not username:
            error = '用户名不能为空'
        elif not email or '@' not in email:
            error = '请输入有效的邮箱地址'
        
        # 检查用户名和邮箱是否被其他用户使用
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
        
        # 处理密码更改
        if not error and new_password:
            # 验证当前密码
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
                # 处理头像上传
                avatar_url = None
                if avatar_file and avatar_file.filename:
                    avatar_url = save_avatar(avatar_file)
                
                # 更新用户基本信息
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
                
                # 如果有密码更改，也更新密码
                if new_password:
                    hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
                    db.execute(
                        'UPDATE users SET password_hash = ? WHERE id = ?',
                        (hashed_password, user_id)
                    )
                
                db.commit()
                flash('个人资料已更新', 'success')
                session['username'] = username
                
                return redirect(url_for('profile', user_id=user_id))
            except Exception as e:
                db.rollback()
                flash(f'更新失败: {str(e)}', 'danger')
    
    now = datetime.datetime.now()
    return render_template('user/edit_profile.html', user=user, now=now)

@app.route('/prompts/all')
def all_prompts():
    # 获取分页和筛选参数
    page = request.args.get('page', 1, type=int)
    per_page = 12  # 每页显示12条提示词
    tag_filter = request.args.get('tag', '')
    
    db = get_db()
    
    # 根据是否有标签筛选来构建不同的查询
    if tag_filter:
        # 计算符合条件的总数
        total_count = db.execute(
            'SELECT COUNT(DISTINCT p.id) as count FROM prompts p '
            'JOIN tags_prompts tp ON p.id = tp.prompt_id '
            'JOIN tags t ON tp.tag_id = t.id '
            'WHERE p.is_public = 1 AND t.name = ?',
            (tag_filter,)
        ).fetchone()['count']
        
        # 获取提示词数据，包括用户信息
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
        # 计算总数以支持分页
        total_count = db.execute(
            'SELECT COUNT(*) as count FROM prompts WHERE is_public = 1'
        ).fetchone()['count']
        
        # 获取提示词数据，包括用户信息
        prompt_rows = db.execute(
            'SELECT p.*, u.username FROM prompts p '
            'JOIN users u ON p.user_id = u.id '
            'WHERE p.is_public = 1 '
            'ORDER BY p.created_at DESC '
            'LIMIT ? OFFSET ?',
            (per_page, (page - 1) * per_page)
        ).fetchall()
    
    # 计算总页数
    total_pages = (total_count + per_page - 1) // per_page
    
    # 确保page在有效范围内
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # 将Row对象转换为可修改的字典列表
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

# 确保收藏表已存在
def ensure_favorites_table():
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

# 在应用启动时确保收藏表存在
with app.app_context():
    ensure_favorites_table()

@app.route('/prompts/<int:id>/favorite', methods=['POST'])
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
            # 如果已收藏，则取消收藏
            db.execute(
                'DELETE FROM favorites WHERE user_id = ? AND prompt_id = ?',
                (user_id, id)
            )
            is_favorited = False
            action = '取消收藏'
        else:
            # 如果未收藏，则添加收藏
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
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500

# 保存头像图片的函数
def save_avatar(file):
    if not file:
        return None
        
    # 检查文件格式
    filename = file.filename
    if not filename or '.' not in filename:
        return None
        
    # 获取文件扩展名并生成随机文件名
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'gif']:
        return None
        
    random_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join('static', 'img', 'avatars', random_name)
    
    # 保存文件
    file.save(save_path)
    
    # 返回相对URL路径
    return f"/static/img/avatars/{random_name}"

# 添加删除提示词的路由
@app.route('/delete-prompt/<int:id>')
@login_required
def delete_prompt(id):
    db = get_db()
    
    # 获取提示词信息
    prompt = db.execute('SELECT * FROM prompts WHERE id = ?', (id,)).fetchone()
    
    if not prompt:
        flash('提示词不存在', 'danger')
        return redirect(url_for('my_prompts'))
    
    # 检查权限：确保只有提示词的创建者可以删除
    if prompt['user_id'] != session['user_id']:
        flash('您没有权限删除此提示词', 'danger')
        return redirect(url_for('my_prompts'))
    
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
        flash(f'删除提示词时出错: {str(e)}', 'danger')
    
    return redirect(url_for('my_prompts'))

# 添加健康检查端点
@app.route('/health')
def health_check():
    """健康检查端点，用于容器监控"""
    try:
        # 尝试连接数据库
        db = get_db()
        db.execute('SELECT 1').fetchone()
        return jsonify({"status": "healthy", "db_connection": "ok"}), 200
    except Exception as e:
        app.logger.error(f"健康检查失败: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

if __name__ == '__main__':
    # 生产环境下禁用调试模式，但保留监听所有网络接口
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0') 