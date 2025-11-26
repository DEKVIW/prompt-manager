"""
路由模块
"""
from app.routes import main, auth, prompts, admin, user, ai


def register_blueprints(app):
    """注册所有蓝图"""
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(prompts.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(ai.bp)

