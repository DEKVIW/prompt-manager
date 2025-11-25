"""
WSGI入口文件，用于生产环境部署
"""
import os
import sys

# 添加当前目录到路径，确保可以导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 检查是否处于生产环境
if os.environ.get('FLASK_DEBUG', 'False').lower() == 'true':
    print("警告：当前以调试模式运行WSGI应用。在生产环境中应禁用调试模式。")

# 导入应用
from app import create_app

app = create_app()

# 仅用于直接运行此文件时
if __name__ == "__main__":
    app.run() 