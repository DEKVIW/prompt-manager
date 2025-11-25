"""
数据库连接和工具函数
"""
import os
import sqlite3
from flask import g, current_app


def get_db():
    """获取数据库连接"""
    # 确保头像目录存在
    avatars_dir = current_app.config.get('UPLOAD_FOLDER')
    if avatars_dir and not os.path.exists(avatars_dir):
        os.makedirs(avatars_dir, exist_ok=True)
    
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        
        # 检查并添加avatar_url字段（如果不存在）
        _ensure_avatar_field(db)
    
    return db


def _ensure_avatar_field(db):
    """确保users表有avatar_url字段"""
    cursor = db.cursor()
    result = cursor.execute("PRAGMA table_info(users)").fetchall()
    has_avatar_field = any(row[1] == 'avatar_url' for row in result)
    
    if not has_avatar_field:
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN avatar_url TEXT')
            db.commit()
            current_app.logger.info("已添加avatar_url字段到users表")
        except sqlite3.Error as e:
            current_app.logger.error(f"添加avatar_url字段时出错: {e}")


def close_db(error):
    """关闭数据库连接"""
    if hasattr(g, '_database'):
        g._database.close()


def init_db_connection(app):
    """初始化数据库连接（注册teardown处理器）"""
    app.teardown_appcontext(close_db)

