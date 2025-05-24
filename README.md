# 提示词管理平台

一个用于创建、管理和共享 AI 提示词的平台，支持多用户协作、版本控制和分类管理。

![提示词管理平台](static/img/screenshot.png)

## 功能特性

- **提示词管理**：创建、编辑、删除和分享 AI 提示词
- **用户系统**：支持用户注册和登录，需要邀请码
- **标签分类**：通过标签组织和分类提示词
- **收藏功能**：收藏常用提示词便于快速访问
- **公开与私有**：设置提示词为公开或私有模式
- **搜索功能**：按标题、描述和标签搜索提示词
- **响应式设计**：适配电脑、平板和手机等各种设备屏幕
- **管理员面板**：管理用户和邀请码

## 技术栈

- **后端**：Flask (Python)
- **前端**：Bootstrap 5, JavaScript
- **数据库**：SQLite (可扩展到其他数据库)
- **容器化**：Docker 与 Nginx 集成

## Docker 部署

本应用提供了优化的 Docker 部署方案，集成了 Nginx 和 Flask 应用到单一容器中:

### 一键部署

* 创建docker-compose.yml文件

```bash
# 从Docker Hub拉取镜像
version: "3"

services:
  prompt-manager:
    image: yilan666/prompt-manager:1.1.2
    ports:
      - "8080:80"
    user: root
    volumes:
      - ./data:/app/instance
      - ./logs:/app/logs
      - ./uploads:/app/static/img/avatars
    environment:
      - SECRET_KEY=              #加密密钥
      - FLASK_DEBUG=false
    restart: unless-stopped
    networks:
      - prompt-network

networks:
  prompt-network:
    driver: bridge
```

执行：

```shell
docker-compose up -d
```

### 自构建镜像

1. 拉取代码

   ```sh
   git clone https://github.com/DEKVIW/prompt-manager.git
   ```

2. 执行

   ```sh
   docker-compose up -d --build
   ```

**注意：**

1. docker-compose 中随机生成一串密钥补充填写在`- SECRET_KEY=`后面；
2. 如果使用`image: yilan666/prompt-manager:1.1`这个镜像部署后的登陆密码是`aaaaaaaa`

### 优化特性

- **单容器设计**: Nginx 和 Flask 应用在单一容器中运行，简化部署和管理
- **静态资源优化**: 所有静态文件由 Nginx 直接提供服务，配置了 7 天缓存
- **高效请求处理**:
  - 静态资源请求不经过 Python 应用
  - 动态请求被代理到内部 Gunicorn 服务器
- **资源利用优化**:
  - Gunicorn 配置了 4 个工作进程和 2 个线程
  - 只暴露 80 端口，内部 5000 端口不对外开放

### 数据持久化

应用数据自动保存在以下本地目录:

- `./data`: 数据库文件
- `./logs`: 应用日志
- `./uploads`:头像图片

### 访问应用

部署完成后，通过浏览器访问:

```
http://ip:8080
```

## 本地开发环境设置

### 前提条件

- Python 3.6+
- pip (Python 包管理器)

### 安装步骤

1. 克隆仓库:

   ```bash
   git clone https://github.com/yourusername/prompt-manager.git
   cd prompt-manager
   ```

2. 创建并激活虚拟环境:

   ```bash
   # 在Linux/macOS上
   python -m venv venv
   source venv/bin/activate

   # 在Windows上
   python -m venv venv
   venv\Scripts\activate
   ```

3. 安装依赖:

   ```bash
   pip install -r requirements.txt
   ```

4. 初始化数据库:

   ```bash
   python simple_db.py
   ```

5. 启动应用:

   ```bash
   python simple_app.py
   ```

6. 访问应用:
   打开浏览器访问 `http://127.0.0.1:5000`

### 使用便捷脚本

项目提供了便捷脚本简化安装和启动过程:

- 在 Linux/macOS 上:

  ```bash
  chmod +x install.sh
  ./install.sh
  ./start.sh
  ```

- 在 Windows 上:
  ```bash
  install.bat
  start.bat
  ```

## 项目结构

```
prompt-manager/
├── app/                  # 应用模块（未来扩展用）
├── data/                 # 数据目录（Docker持久化）
├── instance/             # 实例数据（SQLite数据库）
├── logs/                 # 日志文件
├── static/               # 静态资源（CSS, JS, 图片）
├── templates/            # HTML模板
├── docker-compose.yml    # Docker部署配置
├── Dockerfile            # Docker镜像构建配置
├── nginx.conf            # Nginx配置
├── requirements.txt      # Python依赖
├── simple_app.py         # 主应用程序
├── wsgi.py               # WSGI入口
└── README.md             # 项目说明
```

## 默认账户

- **管理员账户**:
  - 邮箱: admin@example.com
  - 密码: admin123

**重要**: 首次登录后请立即修改默认密码!

## 贡献指南

欢迎贡献代码、报告问题或提出功能建议！请遵循以下步骤:

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情参见 [LICENSE](LICENSE) 文件

## 联系方式

如有问题或建议，请[创建 Issue](https://github.com/yourusername/prompt-manager/issues)或联系项目维护者。
