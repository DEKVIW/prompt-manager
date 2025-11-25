"""
应用工厂函数
"""
from flask import Flask
from app.config import Config
from app.extensions import init_extensions
from app.routes import register_blueprints
from app.database import init_db_connection


def create_app(config_class=Config):
    """创建并配置Flask应用"""
    # 模板和静态文件现在在 app/ 目录下
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/static'
    )
    app.config.from_object(config_class)
    
    # 初始化扩展
    init_extensions(app)
    
    # 初始化数据库连接
    init_db_connection(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 初始化数据库表（在应用上下文中）
    with app.app_context():
        from app.routes.prompts import ensure_favorites_table
        ensure_favorites_table()
    
    return app

