# 使用Python官方镜像作为基础，避免Alpine编译问题
FROM python:3.9-slim

# 安装Nginx和其他必要的系统依赖
RUN apt-get update && \
    apt-get install -y nginx curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 创建必要的目录
RUN mkdir -p /app/instance /app/logs /app/instance_init && \
    chmod -R 777 /app/instance /app/logs

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . /app/

# 为Nginx配置静态文件（静态文件现在在 app/static/ 目录下）
RUN mkdir -p /var/www/html/static && \
    cp -r /app/app/static/* /var/www/html/static/ && \
    chmod -R 755 /var/www/html/static

# 配置Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN rm /etc/nginx/sites-enabled/default || true

# 初始化数据库
RUN python init_db.py && \
    cp -r /app/instance/* /app/instance_init/

# 设置环境变量
ENV FLASK_APP=wsgi.py \
    FLASK_DEBUG=False \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 添加启动脚本
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 暴露端口
EXPOSE 80

# 启动命令
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD sh -c "nginx && gunicorn --workers=4 --threads=2 --bind 127.0.0.1:5000 wsgi:app" 