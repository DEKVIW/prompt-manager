"""
扩展初始化
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Response


def init_extensions(app):
    """初始化所有扩展"""
    setup_logging(app)
    setup_security_headers(app)
    setup_context_processors(app)


def setup_logging(app):
    """配置日志"""
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 在生产环境下，添加文件处理程序
    if not debug_mode:
        # 确保日志目录存在
        logs_dir = app.config['LOG_DIR']
        os.makedirs(logs_dir, exist_ok=True)
        
        # 创建rotating file handler
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, app.config['LOG_FILE']),
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        app.logger.addHandler(file_handler)
    
    app.logger.info(f"应用启动于{'调试' if debug_mode else '生产'}模式")


def setup_security_headers(app):
    """配置安全响应头"""
    @app.after_request
    def add_security_headers(response: Response):
        # CORS配置
        if app.config['ENABLE_CORS']:
            response.headers['Access-Control-Allow-Origin'] = app.config['CORS_ORIGIN']
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        # 基本安全头
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HTTPS安全头
        if app.config['HTTPS_ENABLED']:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


def setup_context_processors(app):
    """配置上下文处理器"""
    import datetime
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.now()}

