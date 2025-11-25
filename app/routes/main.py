"""
主页面路由
"""
from flask import Blueprint, render_template
from app.database import get_db
from app.utils.helpers import format_datetime
import datetime

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """首页"""
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
        prompt_count_result = db.execute('SELECT COUNT(*) as count FROM prompts').fetchone()
        prompt_count = prompt_count_result['count'] if prompt_count_result else 0
        
        user_count_result = db.execute('SELECT COUNT(*) as count FROM users').fetchone()
        user_count = user_count_result['count'] if user_count_result else 0
        
        view_count_result = db.execute('SELECT COALESCE(SUM(view_count), 0) as total_views FROM prompts').fetchone()
        view_count = view_count_result['total_views'] if view_count_result else 0
        
        db.commit()
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error fetching data: {e}")
    
    now = datetime.datetime.now()
    return render_template('index.html', 
                          popular_prompts=popular_prompts, 
                          popular_tags=popular_tags, 
                          prompt_count=prompt_count,
                          user_count=user_count,
                          view_count=view_count,
                          now=now)


@bp.route('/health')
def health_check():
    """健康检查端点，用于容器监控"""
    from flask import jsonify
    try:
        db = get_db()
        db.execute('SELECT 1').fetchone()
        return jsonify({"status": "healthy", "db_connection": "ok"}), 200
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"健康检查失败: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

