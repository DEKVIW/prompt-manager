#!/bin/bash
# Docker快速启动脚本

set -e

# 脚本头部提示
echo "===== 提示词管理平台 Docker 启动脚本 ====="
echo "该脚本将帮助您使用Docker一键启动提示词管理平台"

# 检查Docker和Docker Compose是否已安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装。请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查Docker Compose版本
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    echo "使用新版 Docker Compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo "使用传统版 Docker Compose"
else
    echo "错误: Docker Compose未安装。请安装Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# 检查.env文件是否存在，不存在则从模板创建
if [ ! -f ".env" ]; then
    if [ -f ".env.docker" ]; then
        echo "正在从.env.docker创建.env文件..."
        cp .env.docker .env
        
        # 生成随机密钥
        RANDOM_KEY=$(python3 -c "import secrets; print(secrets.token_hex(16))" 2>/dev/null || openssl rand -hex 16)
        
        # 替换SECRET_KEY
        sed -i "s/change_this_to_a_random_string/$RANDOM_KEY/" .env
        echo "已自动生成随机SECRET_KEY"
    else
        echo "警告: 找不到.env.docker模板文件，将使用默认配置。"
        echo "SECRET_KEY=`openssl rand -hex 16`" > .env
    fi
    echo "已创建.env文件，您可以根据需要编辑它"
fi

# 创建数据和日志目录
echo "确保数据目录和日志目录存在..."
mkdir -p data logs
chmod 777 data logs

# 启动容器
echo "正在构建并启动容器..."
$DOCKER_COMPOSE up --build -d

# 显示容器状态
echo "容器已启动，状态如下:"
$DOCKER_COMPOSE ps

echo ""
echo "===== 启动完成 ====="
echo "您现在可以通过以下地址访问提示词管理平台:"
echo "http://localhost"
echo ""
echo "管理员默认账号:"
echo "邮箱: admin@example.com"
echo "密码: admin123"
echo "请在首次登录后立即更改此密码！"
echo ""
echo "如需停止服务，请运行: $DOCKER_COMPOSE down"
echo "如需查看日志，请运行: $DOCKER_COMPOSE logs -f"
echo "数据存储在./data目录，日志存储在./logs目录" 