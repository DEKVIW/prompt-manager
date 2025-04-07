#!/bin/bash
# 提示词管理平台安装脚本
# 用于在Linux环境中快速设置生产环境

set -e  # 遇到错误立即退出

echo "===== 提示词管理平台安装脚本 ====="

# 检查Python版本
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo "错误: 未找到Python。请安装Python 3.6或更高版本。"
    exit 1
fi

echo "使用Python: $($PYTHON_CMD --version)"

# 创建虚拟环境
echo "创建虚拟环境..."
$PYTHON_CMD -m venv venv
source venv/bin/activate

# 安装依赖
echo "安装依赖项..."
pip install --upgrade pip
pip install -r requirements.txt

# 设置环境变量
if [ ! -f ".env" ]; then
    echo "创建环境变量文件..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        
        # 生成随机密钥
        RANDOM_KEY=$($PYTHON_CMD -c "import secrets; print(secrets.token_hex(16))")
        # 替换SECRET_KEY
        sed -i "s/your_strong_secret_key_here/$RANDOM_KEY/" .env
        echo "已生成随机SECRET_KEY"
    else
        echo "警告: 未找到.env.example文件。"
    fi
fi

# 初始化数据库
echo "初始化数据库..."
$PYTHON_CMD simple_db.py

# 设置权限
echo "设置文件权限..."
chmod +x start.sh

echo "===== 安装完成 ====="
echo "现在可以使用以下命令启动应用:"
echo "./start.sh prod"
echo ""
echo "默认管理员账号:"
echo "邮箱: admin@example.com"
echo "密码: admin123"
echo "请在首次登录后立即更改此密码！" 