"""
数据库迁移脚本：添加 ai_configs 表
用于存储用户的 AI 配置信息
"""
import os
import sqlite3
import sys

def migrate():
    """执行数据库迁移"""
    db_path = "instance"
    db_file = os.path.join(db_path, "prompts.db")
    
    if not os.path.exists(db_file):
        print(f"错误：数据库文件不存在: {db_file}")
        print("请先运行 python init_db.py 初始化数据库")
        return False
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 检查表是否已存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='ai_configs'
        """)
        
        if cursor.fetchone():
            print("ai_configs 表已存在，跳过迁移")
            conn.close()
            return True
        
        print("开始创建 ai_configs 表...")
        
        # 创建 ai_configs 表
        cursor.execute('''
        CREATE TABLE ai_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            provider TEXT NOT NULL DEFAULT 'openai',
            api_key TEXT NOT NULL,
            base_url TEXT,
            model TEXT DEFAULT 'gpt-3.5-turbo',
            temperature REAL DEFAULT 0.7,
            max_tokens INTEGER DEFAULT 500,
            enabled BOOLEAN DEFAULT 1,
            title_max_length INTEGER DEFAULT 30,
            description_max_length INTEGER DEFAULT 100,
            tag_count INTEGER DEFAULT 5,
            tag_two_char_count INTEGER DEFAULT 0,
            tag_four_char_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        ''')
        
        # 创建索引
        cursor.execute('''
        CREATE INDEX idx_ai_configs_user_id ON ai_configs(user_id)
        ''')
        
        conn.commit()
        conn.close()
        
        print("✓ ai_configs 表创建成功！")
        return True
        
    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)

