import random
import string
import os
import sys
from app import app, db
from app.models.user import User, InviteCode
from app.models.prompt import Prompt, Tag
from werkzeug.security import generate_password_hash

def generate_invite_code(length=8):
    """生成随机邀请码"""
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    code = ''.join(random.choice(chars) for _ in range(length))
    return code

def init_db():
    """初始化数据库"""
    try:
        with app.app_context():
            # 确保数据库文件所在目录存在
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if db_uri.startswith('sqlite:///'):
                db_path = os.path.dirname(db_uri.replace('sqlite:///', ''))
                if db_path and not os.path.exists(db_path):
                    os.makedirs(db_path)
            
            print("创建数据库表...")
            db.create_all()
            
            # 检查是否已有管理员
            admin = User.query.filter_by(is_admin=True).first()
            if admin is None:
                print("创建管理员账号...")
                # 创建管理员账号
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()  # 先提交以获取admin的ID
                
                print("生成邀请码...")
                # 为管理员创建一些邀请码
                for _ in range(5):
                    code = generate_invite_code()
                    invite = InviteCode(code=code, creator_id=admin.id)
                    db.session.add(invite)
                
                db.session.commit()
                print(f"管理员账号已创建: admin@example.com (密码: admin123)")
                print("已生成5个邀请码")
            else:
                print("数据库已初始化，管理员账号已存在")
        
        return True
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = init_db()
    sys.exit(0 if success else 1) 