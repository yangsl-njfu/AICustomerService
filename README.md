# AI客服系统

基于LangChain和LangGraph的智能客户服务平台，提供多模态交互、知识库检索、工单管理等功能。

## 技术栈

### 后端
- **框架**: FastAPI
- **AI**: LangChain 1.2.7 + LangGraph 1.0.7
- **数据库**: MySQL 8.0+
- **向量数据库**: Chroma
- **缓存**: Redis
- **语言**: Python 3.10+

### 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **状态管理**: Pinia
- **UI组件**: Element Plus
- **HTTP客户端**: Axios

## 快速开始

### 1. 环境要求
- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Redis 7+
- Chroma (可选，用于向量检索)

### 2. 数据库准备

**MySQL:**
```bash
# 登录MySQL
mysql -u root -p

# 执行初始化脚本
source backend/database/init.sql
```

**Redis:**
```bash
# 启动Redis服务
redis-server
```

**Chroma:**
```bash
# 安装Chroma
pip install chromadb

# Chroma会在应用启动时自动初始化
```

### 3. 后端设置
```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，填入MySQL、Redis、OpenAI等配置

# 启动后端服务
python main.py
```

后端服务将在 http://localhost:8000 启动
API文档: http://localhost:8000/api/docs

### 4. 前端设置
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将在 http://localhost:5173 启动

## 项目结构

```
.
├── backend/                 # 后端代码
│   ├── main.py             # FastAPI应用入口
│   ├── config.py           # 配置管理
│   ├── requirements.txt    # Python依赖
│   ├── models/             # 数据模型
│   ├── services/           # 业务逻辑
│   ├── api/                # API路由
│   ├── database/           # 数据库相关
│   └── tests/              # 测试
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── main.ts        # 应用入口
│   │   ├── App.vue        # 根组件
│   │   ├── components/    # 组件
│   │   ├── views/         # 页面
│   │   ├── stores/        # 状态管理
│   │   └── api/           # API客户端
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 功能特性

- ✅ 用户认证与会话管理
- ✅ 多模态输入（文本、图片、文件）
- ✅ LangGraph智能对话工作流
- ✅ 知识库检索与问答
- ✅ 工单创建与管理
- ✅ 对话历史持久化
- ✅ 管理后台
- ✅ 流式响应
- ✅ 响应式UI

## 开发指南

### 运行测试
```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

### 代码规范
```bash
# 后端
black backend/
flake8 backend/

# 前端
npm run lint
```

## 许可证

MIT License
