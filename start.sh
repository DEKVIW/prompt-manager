#!/bin/bash

# 提示词管理平台启动脚本
# 用法: ./start.sh [dev|prod]

MODE=${1:-dev}
echo "正在准备以 $MODE 模式启动应用..."

# 确保虚拟环境激活（如果存在）
if [ -d "venv" ]; then
  echo "激活虚拟环境..."
  source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
fi

# 如果环境变量文件不存在，创建从示例文件
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    echo "正在从.env.example创建.env文件..."
    cp .env.example .env
    echo "请注意：建议编辑.env文件并设置强SECRET_KEY！"
  else
    echo "警告：找不到.env.example文件，将使用默认配置。"
  fi
fi

# 安装依赖（如果需要）
if [ "$MODE" = "prod" ]; then
  echo "检查依赖..."
  pip install -r requirements.txt --quiet
fi

# 根据模式启动应用
if [ "$MODE" = "dev" ]; then
  # 开发模式：使用Flask内置服务器
  echo "以开发模式启动..."
  export FLASK_DEBUG=True
  export FLASK_APP=simple_app.py
  python -m flask run --host=0.0.0.0
elif [ "$MODE" = "prod" ]; then
  # 生产模式：使用Gunicorn
  echo "以生产模式启动..."
  export FLASK_DEBUG=False
  
  # 检查gunicorn是否已安装
  if ! command -v gunicorn &> /dev/null; then
    echo "错误：找不到gunicorn。请先安装：pip install gunicorn"
    exit 1
  fi
  
  # 使用gunicorn启动
  echo "启动gunicorn WSGI服务器..."
  gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
else
  echo "错误：未知模式 '$MODE'。请使用 'dev' 或 'prod'。"
  exit 1
fi 