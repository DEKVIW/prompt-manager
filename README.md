# 提示词管理平台

一个用于创建、管理和共享 AI 提示词的平台，支持多用户协作、版本控制和分类管理。

## 功能特性

- **AI 自动填充**：一键生成提示词标题、描述和标签，提升创建效率
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
- **AI 集成**：OpenAI API、自定义 API（兼容 OpenAI 格式）

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

7. 配置 AI 自动填充（可选）:
   - 登录后进入"个人资料" → "AI 设置"
   - 配置您的 OpenAI API Key 或自定义 API
   - 保存后即可在创建提示词时使用 AI 自动填充功能

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

#### 6. 配置 AI 自动填充（可选）

- 登录后进入"个人资料" → "AI 设置"
- 配置您的 OpenAI API Key 或自定义 API
- 保存后即可在创建提示词时使用 AI 自动填充功能

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
│   │   ├── user.py      # 用户路由
│   │   └── ai.py        # AI 相关路由
│   ├── services/        # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── prompt_service.py
│   │   ├── user_service.py
│   │   ├── admin_service.py
│   │   ├── tag_service.py
│   │   └── ai_service.py # AI 服务
│   ├── services/ai/     # AI 客户端
│   │   ├── base_client.py
│   │   ├── openai_client.py
│   │   ├── custom_client.py
│   │   └── factory.py
│   ├── utils/           # 工具函数
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   ├── helpers.py
│   │   ├── file_upload.py
│   │   └── encryption.py # 加密工具（用于 API Key 加密）
│   ├── templates/       # HTML模板
│   └── static/          # 静态资源（CSS, JS, 图片）
├── instance/             # 实例数据（SQLite数据库，自动创建）
├── logs/                 # 日志文件（自动创建）
├── requirements.txt      # Python依赖
├── init_db.py           # 数据库初始化脚本
├── migrations/          # 数据库迁移脚本
│   └── add_ai_configs_table.py
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

## AI 自动填充使用说明

### 配置步骤

1. **获取 API Key**

   - OpenAI: 访问 [OpenAI Platform](https://platform.openai.com/api-keys) 获取 API Key
   - 自定义 API: 使用兼容 OpenAI 格式的 API 服务

2. **配置 API**

   - 登录后，点击右上角用户头像 → "编辑个人资料"
   - 切换到 "AI 设置" 标签页
   - 选择 AI 提供商（OpenAI 或自定义 API）
   - 输入 API Key 和模型名称
   - 可选：配置基础 URL（自定义 API 需要）
   - 点击"测试连接"验证配置是否正确
   - 保存设置

3. **使用自动填充**
   - 创建新提示词时，输入提示词内容
   - 点击"AI 自动填充"按钮
   - 系统将自动生成标题、描述和标签
   - 可根据需要调整生成的内容

### 支持的 AI 提供商

- **OpenAI**: GPT-3.5-turbo, GPT-4, GPT-4-turbo 等
- **自定义 API**: 任何兼容 OpenAI 格式的 API 服务

### 安全说明

- API Key 采用加密存储，确保安全性
- 支持 API Key 更新，无需重新输入即可保留原配置

## 贡献指南

欢迎贡献代码、报告问题或提出功能建议！请遵循以下步骤:

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情参见 [LICENSE](LICENSE) 文件
