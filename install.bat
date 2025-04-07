@echo off
REM 提示词管理平台安装脚本 (Windows版)

echo ===== 提示词管理平台安装脚本 =====

REM 检查Python版本
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python。请安装Python 3.6或更高版本。
    exit /b 1
)

echo 使用Python: 
python --version

REM 创建虚拟环境
echo 创建虚拟环境...
python -m venv venv
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖项...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM 设置环境变量
if not exist .env (
    echo 创建环境变量文件...
    if exist .env.example (
        copy .env.example .env
        
        REM 生成随机密钥
        for /f "delims=" %%i in ('python -c "import secrets; print(secrets.token_hex(16))"') do set RANDOM_KEY=%%i
        
        REM 创建临时文件替换SECRET_KEY
        type .env | findstr /v "SECRET_KEY" > .env.tmp
        echo SECRET_KEY=%RANDOM_KEY% >> .env.tmp
        move /y .env.tmp .env
        
        echo 已生成随机SECRET_KEY
    ) else (
        echo 警告: 未找到.env.example文件。
    )
)

REM 初始化数据库
echo 初始化数据库...
python simple_db.py

echo ===== 安装完成 =====
echo 现在可以使用以下命令启动应用:
echo start.bat prod
echo.
echo 默认管理员账号:
echo 邮箱: admin@example.com
echo 密码: admin123
echo 请在首次登录后立即更改此密码！

pause 