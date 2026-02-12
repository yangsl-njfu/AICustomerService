# 🎓 AI 智能客服系统

基于 LangChain + LangGraph 的智能客户服务平台，同时具备完整电商功能。

## ✨ 特性

- 🤖 **AI 智能客服** - 基于大语言模型的智能对话系统
- 🔍 **意图识别** - 自动识别用户意图（问答、工单、商品推荐、订单查询等）
- 🛒 **商品推荐** - 智能推荐系统，根据用户需求推荐商品
- 📦 **订单管理** - 完整的电商订单流程
- 💬 **多轮对话** - 支持上下文记忆的连续对话
- 📄 **RAG 知识库** - 基于向量数据库的智能问答
- ⚡ **Function Calling** - AI 自动调用后端服务查询数据

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Pinia + Element Plus |
| 后端 | FastAPI + Python 3.10+ |
| AI 框架 | LangChain 1.2.7 + LangGraph 1.0.7 |
| 主数据库 | MySQL 8.0+ |
| 向量数据库 | Chroma |
| 缓存 | 内存缓存（支持 Redis 扩展） |

## 📁 项目结构

```
AICustomerService/
├── backend/                 # 后端服务
│   ├── api/                # API 路由
│   │   ├── chat.py         # AI 对话接口
│   │   ├── products.py     # 商品接口
│   │   ├── orders.py       # 订单接口
│   │   └── ...
│   ├── services/            # 业务逻辑
│   │   ├── ai/            # AI 服务
│   │   │   ├── nodes/     # LangGraph 节点
│   │   │   │   ├── intent_node.py       # 意图识别
│   │   │   │   ├── function_calling_node.py  # 函数调用
│   │   │   │   ├── product_recommendation_node.py  # 商品推荐
│   │   │   │   └── ...
│   │   │   ├── workflow.py # 工作流编排
│   │   │   ├── router.py  # 路由决策
│   │   │   └── state.py   # 对话状态
│   │   ├── product_service.py
│   │   ├── order_service.py
│   │   └── ...
│   ├── database/           # 数据库模型
│   │   ├── models.py      # SQLAlchemy 模型
│   │   └── init.sql      # 初始化 SQL
│   └── main.py            # FastAPI 入口
│
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── views/        # 页面组件
│   │   │   ├── Chat.vue  # AI 对话页面
│   │   │   ├── Products.vue # 商品列表
│   │   │   └── ...
│   │   ├── stores/       # Pinia 状态管理
│   │   └── api/          # API 调用
│   └── package.json
│
└── README.md
```

## 🚀 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+

### 1. 克隆项目

```bash
git clone <repository-url>
cd AICustomerService
```

### 2. 配置后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env
# 编辑 .env 配置数据库和 API Key
```

### 3. 配置数据库

```sql
-- 创建数据库
CREATE DATABASE ai_customer_service CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 初始化数据
source database/init.sql
```

### 4. 启动后端

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 运行

- API 文档: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### 5. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将在 http://localhost:5173 运行

### 6. 登录系统

- 访问 http://localhost:5173
- 使用初始账号登录（可自行注册）

## 📖 AI 功能说明

### 支持的场景

| 场景 | 示例 | 处理方式 |
|------|------|----------|
| 问答 | "你们平台是做什么的" | 知识库检索 |
| 商品推荐 | "推荐python毕业设计" | 搜索商品并展示卡片 |
| 商品咨询 | "这个项目用什么技术" | 查询商品详情 |
| 订单查询 | "我的订单到哪了" | 查询订单状态/物流 |
| 工单处理 | "东西坏了要退款" | 创建售后工单 |
| 购买指导 | "怎么购买" | 解答购买流程 |

### 工作流

```
用户输入 → 意图识别 → 函数调用 → 路由决策 → 业务处理 → 保存上下文
```

### 缓存机制

- 意图识别结果缓存
- 对话上下文缓存
- 智能问题推荐缓存

## 📦 主要功能模块

### 后端 API

- `/api/chat/*` - AI 对话接口
- `/api/products/*` - 商品管理
- `/api/orders/*` - 订单管理
- `/api/cart/*` - 购物车
- `/api/favorites/*` - 收藏
- `/api/tickets/*` - 工单管理

### 前端页面

- 首页 - 商品展示
- 商品列表 - 筛选、搜索
- 商品详情 - 购买
- 购物车 - 下单
- 订单管理 - 状态查看
- AI 客服 - 智能对话
- 工单系统 - 售后支持

## 🔧 环境变量

```env
# 应用配置
APP_NAME=AI客服系统
DEBUG=True

# 数据库
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ai_customer_service

# Redis (可选)
REDIS_HOST=localhost
REDIS_PORT=6379

# OpenAI API
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4

# JWT
JWT_SECRET_KEY=your-secret-key
```

## 📄 许可证

MIT License
