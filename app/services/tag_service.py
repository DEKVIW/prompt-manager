"""
标签业务逻辑
"""
import re
from app.database import get_db


def process_tags(tag_names):
    """处理标签名称列表，返回去重后的标签列表"""
    if not tag_names:
        return []
    
    all_tags = []
    for tag_field in tag_names:
        if tag_field.strip():
            # 支持多种分隔符：逗号、分号、空格、井号、斜杠、竖线、换行等
            separators = r'[,;，；、\s\n#\/\|·\-_\+\*~`]+'
            split_tags = re.split(separators, tag_field)
            all_tags.extend([tag.strip() for tag in split_tags if tag.strip()])
    
    # 去重
    return list(set(all_tags))


def link_tags_to_prompt(db, prompt_id, tag_names):
    """将标签关联到提示词"""
    if not tag_names:
        return
    
    unique_tags = process_tags(tag_names)
    
    for tag_name in unique_tags:
        # 检查标签是否存在
        tag = db.execute('SELECT id FROM tags WHERE name = ?', (tag_name,)).fetchone()
        if not tag:
            # 创建新标签
            db.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
            tag_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        else:
            tag_id = tag['id']
        
        # 关联标签和提示词
        db.execute('INSERT INTO tags_prompts (tag_id, prompt_id) VALUES (?, ?)', (tag_id, prompt_id))

