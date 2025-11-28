import sqlite3
import os

def migrate_db():
    print("开始迁移数据库...")
    
    # 获取数据库路径
    db_path = "instance"
    db_file = os.path.join(db_path, "prompts.db")
    
    if not os.path.exists(db_file):
        print(f"数据库文件不存在: {db_file}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        print("检查users表是否已包含is_approved字段...")
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "is_approved" not in columns:
            print("添加is_approved字段到users表...")
            # 添加is_approved字段，默认值为0
            cursor.execute('''
            ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 0
            ''')
            
            # 将现有管理员用户设置为已审核
            cursor.execute('''
            UPDATE users SET is_approved = 1 WHERE is_admin = 1
            ''')
            
            print("字段添加成功，并将管理员用户设置为已审核")
        else:
            print("is_approved字段已存在，跳过迁移")
        
        # 提交事务
        conn.commit()
        
        # 关闭连接
        conn.close()
        
        print("数据库迁移成功!")
        return True
    except Exception as e:
        print(f"数据库迁移出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_db()
    exit(0 if success else 1)
