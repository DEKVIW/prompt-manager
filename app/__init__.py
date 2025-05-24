import os
import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化应用
app = Flask(__name__)

# 配置应用
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///prompts.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# 添加上下文处理器提供当前年份
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

# 导入模型
from app.models.user import User, InviteCode
from app.models.prompt import Prompt, Tag

# 注册蓝图
from app.routes.auth import auth as auth_blueprint
from app.routes.main import main as main_blueprint
from app.routes.prompts import prompts as prompts_blueprint
from app.routes.admin import admin as admin_blueprint

app.register_blueprint(auth_blueprint)
app.register_blueprint(main_blueprint)
app.register_blueprint(prompts_blueprint)
app.register_blueprint(admin_blueprint)

def create_app():
    return app 