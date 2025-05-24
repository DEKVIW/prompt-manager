@echo off
REM Docker快速启动脚本 (Windows版)

echo ===== 提示词管理平台 Docker 启动脚本 =====
echo 该脚本将帮助您使用Docker一键启动提示词管理平台

REM 检查Docker是否已安装
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: Docker未安装。请先安装Docker: https://docs.docker.com/get-docker/
    exit /b 1
)

REM 确定Docker Compose版本
docker compose version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set DOCKER_COMPOSE=docker compose
    echo 使用新版 Docker Compose
) else (
    where docker-compose >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set DOCKER_COMPOSE=docker-compose
        echo 使用传统版 Docker Compose
    ) else (
        echo 错误: Docker Compose未安装
        echo 请安装Docker Desktop或Docker Compose: https://docs.docker.com/compose/install/
        exit /b 1
    )
)

REM 检查.env文件是否存在，不存在则从模板创建
if not exist .env (
    if exist .env.docker (
        echo 正在从.env.docker创建.env文件...
        copy .env.docker .env
        
        REM 生成随机密钥
        for /f "delims=" %%i in ('python -c "import secrets; print(secrets.token_hex(16))"') do set RANDOM_KEY=%%i
        
        REM 创建临时文件替换SECRET_KEY
        type .env | findstr /v "SECRET_KEY" > .env.tmp
        echo SECRET_KEY=%RANDOM_KEY% >> .env.tmp
        move /y .env.tmp .env
        
        echo 已自动生成随机SECRET_KEY
    ) else (
        echo 警告: 找不到.env.docker模板文件，将使用默认配置。
        echo SECRET_KEY=default_key_please_change_me > .env
    )
    echo 已创建.env文件，您可以根据需要编辑它
)

REM 创建数据和日志目录
echo 确保数据目录和日志目录存在...
if not exist data mkdir data
if not exist logs mkdir logs

REM 启动容器
echo 正在构建并启动容器...
%DOCKER_COMPOSE% up --build -d

REM 显示容器状态
echo 容器已启动，状态如下:
%DOCKER_COMPOSE% ps

echo.
echo ===== 启动完成 =====
echo 您现在可以通过以下地址访问提示词管理平台:
echo http://localhost
echo.
echo 管理员默认账号:
echo 邮箱: admin@example.com
echo 密码: admin123
echo 请在首次登录后立即更改此密码！
echo.
echo 如需停止服务，请运行: %DOCKER_COMPOSE% down
echo 如需查看日志，请运行: %DOCKER_COMPOSE% logs -f
echo 数据存储在.\data目录，日志存储在.\logs目录

pause 