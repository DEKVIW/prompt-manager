#!/bin/bash
set -e

# 数据库目录
INSTANCE_DIR="/app/instance"
INIT_DIR="/app/instance_init"

# 检查数据目录下是否有文件
if [ -z "$(ls -A $INSTANCE_DIR)" ]; then
  echo "数据目录为空，正在从初始化数据复制..."
  cp -r $INIT_DIR/* $INSTANCE_DIR/
  echo "数据库初始化完成！"
else
  echo "检测到现有数据库，跳过初始化"
  echo "执行数据库迁移以更新数据库结构..."
  
  # 执行所有迁移脚本（迁移脚本会检查表是否存在，可安全重复执行）
  if [ -d "/app/migrations" ]; then
    for migration in /app/migrations/*.py; do
      if [ -f "$migration" ]; then
        echo "执行迁移: $(basename $migration)"
        python "$migration" || {
          echo "警告: 迁移脚本 $(basename $migration) 执行失败，但继续启动..."
        }
      fi
    done
    echo "数据库迁移完成！"
  fi
fi

# 确保权限正确
chmod -R 777 $INSTANCE_DIR /app/logs

# 确保上传目录存在（静态文件现在在 app/static/ 目录下）
mkdir -p /app/app/static/img/avatars
chmod -R 777 /app/app/static/img/avatars

# 确保Nginx静态目录存在
mkdir -p /var/www/html/static/img/avatars

# 创建从应用上传目录到Nginx静态目录的软链接
rm -rf /var/www/html/static/img/avatars
ln -sf /app/app/static/img/avatars /var/www/html/static/img/

# 配置Nginx
if [ ! -f "/etc/nginx/sites-enabled/default" ]; then
  mkdir -p /etc/nginx/sites-enabled/
  ln -sf /etc/nginx/conf.d/default.conf /etc/nginx/sites-enabled/default
fi

# 确保Nginx有权限运行
mkdir -p /var/log/nginx
touch /var/log/nginx/access.log /var/log/nginx/error.log
chown -R www-data:www-data /var/log/nginx
chmod -R 755 /var/log/nginx

echo "-------------------------------------"
echo "正在启动Nginx和Gunicorn服务..."
echo "Nginx将处理静态资源并反向代理请求到Flask应用"
echo "-------------------------------------"

# 执行传入的命令（通常是启动Nginx和Gunicorn）
exec "$@" 