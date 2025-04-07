# 提示词管理平台部署指南

本文档提供将提示词管理平台从开发环境迁移到生产环境的详细指南。

## 部署方式

提示词管理平台支持以下几种部署方式:

1. **Docker 部署** - 最简单的部署方式，推荐用于大多数情况
2. **直接部署** - 在服务器上直接运行应用
3. **反向代理部署** - 结合 Nginx/Apache 等 Web 服务器

## Docker 部署 (推荐)

Docker 部署是最简单且推荐的部署方式，它可以帮助您快速启动一个生产就绪的实例。

### 前提条件

- 安装了 Docker 和 Docker Compose 的服务器/VPS
- 基本的 Linux 命令行知识

### 部署步骤

1. 克隆代码库:

```bash
git clone https://github.com/yourusername/prompt-manager.git
cd prompt-manager
```

2. 运行自动部署脚本:

```bash
chmod +x docker-run.sh
./docker-run.sh
```

就是这么简单！脚本会自动完成以下工作:

- 生成安全的随机密钥
- 构建优化的 Docker 镜像
- 创建本地数据目录和日志目录
- 在后台启动服务

3. 访问应用:

应用将在 http://your-server-ip:5000 上运行

### 数据存储位置

应用数据存储在以下目录中:

- `./data` - 数据库和实例文件
- `./logs` - 应用日志

这些目录会自动映射到 Docker 容器内部，确保即使容器被删除，数据也不会丢失。

### 自定义 Docker 部署

如果需要自定义部署，可以编辑以下文件:

- `.env.docker` - 配置环境变量
- `docker-compose.yml` - 修改 Docker Compose 配置
- `Dockerfile` - 调整 Docker 镜像构建过程

### Docker 部署优势

- 简单快捷，几分钟内完成部署
- 应用与系统隔离，避免依赖冲突
- 易于备份与迁移
- 自动处理依赖安装
- 一致的运行环境

### Docker 常用命令

```bash
# 查看容器状态
docker compose ps

# 查看应用日志
docker compose logs -f

# 停止应用
docker compose down

# 重启应用
docker compose restart

# 完全重建并启动
docker compose up --build -d
```

## 优化的 Docker 部署方案

最新版本提供了优化的单容器部署方案，将 Nginx 和 Flask 应用集成到同一容器中，具有多项优势：

### 架构概述

```
┌─────────────────────────────────────┐
│             Docker容器              │
│                                     │
│  ┌─────────┐        ┌────────────┐  │
│  │         │  代理   │            │  │
│  │  Nginx  ├───────►│ Gunicorn/  │  │
│  │         │        │   Flask    │  │
│  └─────┬───┘        └──────┬─────┘  │
│        │                   │        │
│    静态文件              动态请求    │
│        │                   │        │
└────────┼───────────────────┼────────┘
         ▼                   ▼
     ┌───────┐           ┌───────┐
     │ 静态  │           │ 数据库 │
     │ 资源  │           │ 文件   │
     └───────┘           └───────┘
```

### 技术优势

1. **流量优化**：

   - 静态资源请求由 Nginx 直接处理，不会占用 Python 应用资源
   - 配置了 7 天缓存，大幅减少重复请求，提高前端加载速度

2. **资源利用**：

   - Gunicorn 配置了 4 个工作进程和 2 个线程，高效处理动态请求
   - 内部只有 Nginx 暴露到外部网络，增加了安全性

3. **部署简化**：
   - 单一容器减少了配置复杂度和部署错误可能性
   - 一个命令即可完成所有部署步骤

### 部署方法

1. 确保安装了 Docker 和 Docker Compose
2. 在项目根目录运行：
   ```bash
   docker-compose up -d --build
   ```
3. 应用将在 http://localhost 可用

### 维护与管理

- **查看日志**:

  ```bash
  docker-compose logs
  ```

- **重启服务**:

  ```bash
  docker-compose restart
  ```

- **停止服务**:
  ```bash
  docker-compose down
  ```

## Docker Hub 快速部署

### 使用预构建镜像

我们提供了预构建的 Docker 镜像，可以直接从 Docker Hub 拉取使用：

```bash
# 拉取镜像
docker pull yilan666/prompt-manager:1.0

# 创建本地数据目录
mkdir -p data logs

# 运行容器
docker run -d \
  --name prompt-manager \
  -p 80:80 \
  -v $(pwd)/data:/app/instance \
  -v $(pwd)/logs:/app/logs \
  -e SECRET_KEY=your_secret_key_here \
  yilan666/prompt-manager:1.0
```

Windows PowerShell 中使用：

```powershell
# 拉取镜像
docker pull yilan666/prompt-manager:1.0

# 创建本地数据目录
mkdir -p data,logs

# 运行容器
docker run -d `
  --name prompt-manager `
  -p 80:80 `
  -v ${PWD}/data:/app/instance `
  -v ${PWD}/logs:/app/logs `
  -e SECRET_KEY=your_secret_key_here `
  yilan666/prompt-manager:1.0
```

### 使用 docker-compose

```yaml
version: "3.8"

services:
  prompt-manager:
    image: yilan666/prompt-manager:1.0
    container_name: prompt-manager
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./data:/app/instance
      - ./logs:/app/logs
    environment:
      - SECRET_KEY=${SECRET_KEY:-change_this_to_a_random_string}
      - FLASK_DEBUG=false
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

将上述内容保存为`docker-compose.yml`文件，然后运行：

```bash
docker-compose up -d
```

应用将在 http://localhost 可用。

## 直接部署

### 准备工作

#### 系统要求

- Python 3.6 或更高版本
- pip (Python 包管理器)
- 建议使用虚拟环境

#### 安全注意事项

在生产环境中部署应用前，请确保：

1. 更改默认的管理员密码
2. 配置强密钥
3. 设置适当的文件权限
4. 考虑使用 HTTPS 确保通信安全

### 部署步骤

#### 1. 获取代码

```bash
git clone https://github.com/yourusername/prompt-manager.git
cd prompt-manager
```

#### 2. 设置虚拟环境

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/MacOS
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量

创建一个名为`.env`的文件，设置以下环境变量：

```
SECRET_KEY=your_strong_secret_key_here
FLASK_DEBUG=False
```

为了安全起见，建议使用随机生成的强密钥，可以使用 Python 生成：

```python
import secrets
print(secrets.token_hex(16))
```

#### 5. 初始化数据库

```bash
python simple_db.py
```

#### 6. 使用 Gunicorn 启动服务

Gunicorn 是一个生产级别的 WSGI 服务器，推荐用于生产环境：

```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

参数说明：

- `-w 4`: 使用 4 个工作进程
- `-b 0.0.0.0:5000`: 绑定到所有网络接口的 5000 端口
- `wsgi:app`: 使用 wsgi.py 中的 app 对象

## 使用反向代理服务器

在生产环境中，建议在应用服务器前面设置 Nginx 或 Apache 作为反向代理，处理静态文件并提供 SSL 终端。

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your_domain.com;

    # 重定向HTTP到HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your_domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # SSL配置...

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/your/app/static;
        expires 30d;
    }
}
```

### 使用进程管理器

在生产环境中，建议使用进程管理器（如 Supervisor）来确保应用始终运行，并在崩溃时自动重启。

#### Supervisor 配置示例

创建配置文件 `/etc/supervisor/conf.d/prompt-manager.conf`:

```
[program:prompt-manager]
command=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 wsgi:app
directory=/path/to/prompt-manager
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/prompt-manager/error.log
stdout_logfile=/var/log/prompt-manager/access.log
```

然后重新加载 Supervisor 配置：

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start prompt-manager
```

## 维护与监控

- 定期备份数据库文件
- 监控服务器日志
- 考虑设置通知系统报告错误

## 更新应用

更新应用时的建议步骤：

1. 备份数据库
2. 获取最新代码
3. 安装新依赖
4. 迁移数据库（如果需要）
5. 重启应用

```bash
# 备份数据库
cp instance/prompts.db instance/prompts.db.backup

# 获取最新代码
git pull

# 更新依赖
pip install -r requirements.txt

# 重启应用
sudo supervisorctl restart prompt-manager
```

如果使用 Docker 部署，更新应用非常简单：

```bash
# 拉取最新代码
git pull

# 重建并重启容器
docker compose up --build -d
```

## 故障排除

- 检查日志文件了解错误详情
- 验证环境变量是否正确设置
- 确认文件权限正确
- 检查网络配置和防火墙设置
