@echo off
REM 提示词管理平台启动脚本 (Windows版)
REM 用法: start.bat [dev|prod]

SET MODE=%1
IF "%MODE%"=="" SET MODE=dev
echo 正在准备以 %MODE% 模式启动应用...

REM 确保虚拟环境激活（如果存在）
IF EXIST venv (
  echo 激活虚拟环境...
  call venv\Scripts\activate.bat
)

REM 如果环境变量文件不存在，创建从示例文件
IF NOT EXIST .env (
  IF EXIST .env.example (
    echo 正在从.env.example创建.env文件...
    copy .env.example .env
    echo 请注意：建议编辑.env文件并设置强SECRET_KEY！
  ) ELSE (
    echo 警告：找不到.env.example文件，将使用默认配置。
  )
)

REM 安装依赖（如果需要）
IF "%MODE%"=="prod" (
  echo 检查依赖...
  pip install -r requirements.txt
)

REM 根据模式启动应用
IF "%MODE%"=="dev" (
  REM 开发模式：使用Flask内置服务器
  echo 以开发模式启动...
  SET FLASK_DEBUG=True
  SET FLASK_APP=simple_app.py
  python -m flask run --host=0.0.0.0
) ELSE IF "%MODE%"=="prod" (
  REM 生产模式：使用Waitress (Windows下的WSGI服务器)
  echo 以生产模式启动...
  SET FLASK_DEBUG=False
  
  REM 检查waitress是否已安装
  pip show waitress >nul 2>&1
  IF %ERRORLEVEL% NEQ 0 (
    echo 错误：找不到waitress。请先安装：pip install waitress
    exit /b 1
  )
  
  REM 使用waitress启动
  echo 启动waitress WSGI服务器...
  python -m waitress --host=0.0.0.0 --port=5000 wsgi:app
) ELSE (
  echo 错误：未知模式 '%MODE%'。请使用 'dev' 或 'prod'。
  exit /b 1
) 