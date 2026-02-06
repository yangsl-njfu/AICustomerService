# AI客服系统 - 安装和启动指南

## 环境准备

### 必需软件
- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Redis 7+

### 可选软件
- Chroma (向量数据库，用于知识库检索)

## 安装步骤

### 1. 数据库准备

#### MySQL
```bash
# 登录MySQL
mysql -u root -p

# 执行初始化脚本
source backend/database/init.sql

# 或者直接导入
mysql -u root -p < backend/database/init.sql
```

默认会创建一个管理员账户：
- 用户名：`admin`
- 密码：`admin123`

#### Redis
```bash
# 启动Redis服务
redis-server

# 或者使用配置文件启动
redis-server /path/to/redis.conf
```

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 编辑.env文件，填入以下必要配置：
# - MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
# - REDIS_HOST, REDIS_PORT
# - OPENAI_API_KEY (必需，用于AI功能)
# - JWT_SECRET_KEY (建议修改为随机字符串)

# 启动后端服务
python main.py
```

后端服务将在 http://localhost:8000 启动

API文档：http://localhost:8000/api/docs

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将在 http://localhost:5173 启动

## 配置说明

### 后端配置 (.env)

```env
# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ai_customer_service

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379

# OpenAI配置（必需）
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7

# JWT配置（建议修改）
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# 文件上传配置
UPLOAD_DIR=./data/uploads
MAX_FILE_SIZE=10485760

# CORS配置
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Chroma向量数据库（可选）

如果需要使用知识库功能，Chroma会在应用启动时自动初始化。数据将存储在 `backend/data/chroma` 目录。

## 功能测试

### 1. 登录系统
- 访问 http://localhost:5173
- 使用默认管理员账户登录：
  - 用户名：`admin`
  - 密码：`admin123`

### 2. 创建对话
- 点击"新建对话"
- 输入消息测试AI回复

### 3. 创建工单
- 进入"工单"页面
- 点击"创建工单"
- 填写工单信息

### 4. 管理后台（管理员）
- 进入"管理后台"
- 查看系统统计
- 上传知识库文档

## 常见问题

### 1. 数据库连接失败
- 检查MySQL服务是否启动
- 确认.env中的数据库配置正确
- 确认数据库已创建

### 2. Redis连接失败
- 检查Redis服务是否启动
- 确认Redis端口（默认6379）未被占用

### 3. OpenAI API调用失败
- 确认OPENAI_API_KEY配置正确
- 检查网络连接
- 确认API额度充足

### 4. 前端无法连接后端
- 确认后端服务已启动
- 检查CORS配置是否包含前端地址
- 查看浏览器控制台错误信息

## 开发建议

### 后端开发
```bash
# 运行测试
cd backend
pytest

# 代码格式化
black .
flake8 .
```

### 前端开发
```bash
# 运行测试
cd frontend
npm run test

# 代码检查
npm run lint

# 构建生产版本
npm run build
```

## 生产部署

### 后端
1. 修改.env中的配置（特别是JWT_SECRET_KEY）
2. 设置DEBUG=False
3. 使用Gunicorn或uWSGI部署
4. 配置Nginx反向代理
5. 启用HTTPS

### 前端
1. 构建生产版本：`npm run build`
2. 将dist目录部署到Web服务器
3. 配置Nginx服务静态文件

## 技术支持

如有问题，请查看：
- API文档：http://localhost:8000/api/docs
- 项目README：README.md
- 设计文档：.kiro/specs/ai-customer-service/design.md
