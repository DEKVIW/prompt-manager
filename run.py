"""
开发环境运行入口
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0')

