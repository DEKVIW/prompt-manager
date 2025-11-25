# 提示词管理平台

一个用于创建、管理和共享 AI 提示词的平台，支持多用户协作、版本控制和分类管理。

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

## 本地开发环境设置

### 前提条件

- Python 3.6+
- pip (Python 包管理器)

### 安装步骤

1. 克隆仓库:

   ```bash
   git clone https://github.com/DEKVIW/prompt-manager.git
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
   python init_db.py
   ```

5. 启动应用:

   ```bash
   python run.py
   ```

6. 访问应用:
   打开浏览器访问 `http://127.0.0.1:5000`

## Docker 部署

### 使用 Docker Compose（推荐）

#### 1. 配置环境变量

创建 `.env` 文件（可选，如不创建将使用默认值）：

```env
SECRET_KEY=your-secret-key-here-change-this
FLASK_DEBUG=false
```

#### 2. 构建并启动

```bash
docker-compose up -d
```

#### 3. 查看日志

```bash
docker-compose logs -f
```

#### 4. 停止服务

```bash
docker-compose down
```

#### 5. 访问应用

打开浏览器访问 `http://localhost:5000`

### 手动 Docker 部署

#### 1. 构建镜像

```bash
docker build -t prompt-manager:latest .
```

#### 2. 运行容器

```bash
docker run -d \
  --name prompt-manager \
  -p 5000:80 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/uploads:/app/app/static/img/avatars \
  -e SECRET_KEY=your-secret-key-here \
  prompt-manager:latest
```

### Docker 配置说明

- **端口映射**：容器内部 80 端口映射到主机 5000 端口
- **数据持久化**：
  - `./instance` → `/app/instance` (数据库文件)
  - `./logs` → `/app/logs` (日志文件)
  - `./uploads` → `/app/app/static/img/avatars` (上传的头像)
- **健康检查**：容器包含健康检查端点 `/health`

## 项目结构

```
prompt-manager/
├── app/                  # 应用主包
│   ├── __init__.py      # 应用工厂函数
│   ├── config.py        # 配置文件
│   ├── extensions.py    # 扩展初始化
│   ├── database/        # 数据库层
│   │   └── db.py        # 数据库连接和操作
│   ├── routes/          # 路由层（蓝图）
│   │   ├── __init__.py  # 蓝图注册
│   │   ├── main.py      # 主页面路由
│   │   ├── auth.py      # 认证路由
│   │   ├── prompts.py   # 提示词路由
│   │   ├── admin.py     # 管理路由
│   │   └── user.py      # 用户路由
│   ├── services/        # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── prompt_service.py
│   │   ├── user_service.py
│   │   ├── admin_service.py
│   │   └── tag_service.py
│   ├── utils/           # 工具函数
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   ├── helpers.py
│   │   └── file_upload.py
│   ├── templates/       # HTML模板
│   └── static/          # 静态资源（CSS, JS, 图片）
├── instance/             # 实例数据（SQLite数据库，自动创建）
├── logs/                 # 日志文件（自动创建）
├── requirements.txt      # Python依赖
├── init_db.py           # 数据库初始化脚本
├── run.py               # 开发环境运行入口
├── wsgi.py              # WSGI入口（生产环境）
├── Dockerfile           # Docker 镜像构建文件
├── docker-compose.yml   # Docker Compose 配置
├── docker-entrypoint.sh # Docker 容器启动脚本
├── nginx.conf           # Nginx 配置文件
└── README.md            # 项目说明
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
