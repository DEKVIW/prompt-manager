import os
import sqlite3
import random
import string
import sys
from werkzeug.security import generate_password_hash

def generate_random_code(length=8):
    """生成随机邀请码"""
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def init_db():
    print("开始初始化数据库...")
    
    # 创建数据库目录
    db_path = "instance"
    print(f"创建数据库目录: {db_path}")
    if not os.path.exists(db_path):
        os.makedirs(db_path)
        print(f"目录已创建")
    else:
        print(f"目录已存在")
    
    db_file = os.path.join(db_path, "prompts.db")
    print(f"数据库文件路径: {db_file}")
    
    # 如果数据库已存在，先询问是否删除
    db_exists = os.path.exists(db_file)
    if db_exists:
        print(f"数据库文件已存在。跳过初始化过程。")
        return True
    
    print("创建新数据库...")
    
    try:
        # 创建数据库连接
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        print("创建表...")
        
        # 创建用户表
        cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            is_banned BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建邀请码表
        cursor.execute('''
        CREATE TABLE invite_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            is_used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used_at TIMESTAMP,
            creator_id INTEGER,
            used_by INTEGER,
            FOREIGN KEY (creator_id) REFERENCES users (id),
            FOREIGN KEY (used_by) REFERENCES users (id)
        )
        ''')
        
        # 创建标签表
        cursor.execute('''
        CREATE TABLE tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建提示词表
        cursor.execute('''
        CREATE TABLE prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            description TEXT,
            version TEXT,
            cover_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            is_public BOOLEAN DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            share_count INTEGER DEFAULT 0,
            _metadata TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # 创建标签-提示词关联表
        cursor.execute('''
        CREATE TABLE tags_prompts (
            tag_id INTEGER NOT NULL,
            prompt_id INTEGER NOT NULL,
            PRIMARY KEY (tag_id, prompt_id),
            FOREIGN KEY (tag_id) REFERENCES tags (id),
            FOREIGN KEY (prompt_id) REFERENCES prompts (id)
        )
        ''')
        
        print("创建管理员账号...")
        
        # 创建管理员账号，使用 werkzeug.security 生成密码哈希
        admin_password = 'admin123'
        admin_password_hash = generate_password_hash(admin_password, method='pbkdf2:sha256')
        cursor.execute('''
        INSERT INTO users (username, email, password_hash, is_admin)
        VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin@example.com', admin_password_hash, 1))
        
        # 获取管理员ID
        admin_id = cursor.lastrowid
        
        print("生成邀请码...")
        
        # 创建邀请码
        invite_codes = []
        for _ in range(5):
            code = generate_random_code()
            invite_codes.append(code)
            cursor.execute('''
            INSERT INTO invite_codes (code, creator_id)
            VALUES (?, ?)
            ''', (code, admin_id))
        
        # 提交事务
        conn.commit()
        
        # 关闭连接
        conn.close()
        
        print("\n数据库初始化成功!")
        print("管理员账号: admin@example.com")
        print("密码: admin123")
        print("已生成以下邀请码:")
        for i, code in enumerate(invite_codes, 1):
            print(f"邀请码 {i}: {code}")
        
        return True
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1) 