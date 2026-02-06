# AI客服模块 - 即插即用架构设计

## 设计目标

打造一个**独立、可复用、易集成**的AI客服模块，可以快速接入任何业务系统。

### 核心原则
1. **解耦** - AI模块与业务系统完全分离
2. **标准化** - 统一的接口和数据格式
3. **可配置** - 通过配置适配不同业务
4. **可扩展** - 插件化架构，易于扩展
5. **独立部署** - 可以单独部署和升级

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      业务系统 A                              │
│  (毕业设计商城 / 其他电商 / 企业系统 / ...)                  │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API / WebSocket
                     │ 标准接口调用
┌────────────────────▼────────────────────────────────────────┐
│                  AI客服模块 (独立服务)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Gateway (统一入口)                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           业务适配层 (Business Adapter)               │  │
│  │  - 电商适配器  - 企业适配器  - 自定义适配器           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              AI核心引擎 (LangGraph)                   │  │
│  │  - 意图识别  - 对话管理  - 知识检索                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            插件系统 (Plugin System)                   │  │
│  │  - Function Tools  - 自定义节点  - 扩展功能          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              数据层 (独立数据库)                      │  │
│  │  - 对话历史  - 知识库  - 配置信息                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件设计

### 1. API Gateway (统一入口)

**标准化API接口：**

```python
# 对话接口
POST /api/v1/chat/message
{
    "business_id": "graduation-marketplace",  # 业务标识
    "user_id": "user_123",
    "session_id": "session_456",
    "message": "我想查询订单",
    "context": {  # 业务上下文（可选）
        "user_info": {...},
        "current_page": "order_list",
        "extra_data": {...}
    }
}

# 响应
{
    "message_id": "msg_789",
    "response": "好的，请告诉我您的订单号",
    "quick_actions": [
        {"type": "button", "label": "查看我的订单", "action": "query_orders"}
    ],
    "intent": "order_query",
    "confidence": 0.95
}
```

**WebSocket接口（流式）：**
```javascript
ws://ai-service.com/ws/chat?business_id=xxx&user_id=xxx
```

---

### 2. 业务适配层 (Business Adapter)

**作用：** 将不同业务系统的数据格式转换为AI模块的标准格式

**适配器接口：**

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BusinessAdapter(ABC):
    """业务适配器基类"""
    
    @abstractmethod
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """获取用户信息"""
        pass
    
    @abstractmethod
    async def query_orders(self, user_id: str, filters: Dict) -> List[Dict]:
        """查询订单"""
        pass
    
    @abstractmethod
    async def search_products(self, keyword: str, filters: Dict) -> List[Dict]:
        """搜索商品"""
        pass
    
    @abstractmethod
    async def create_ticket(self, user_id: str, ticket_data: Dict) -> Dict:
        """创建工单"""
        pass
    
    @abstractmethod
    def get_business_config(self) -> Dict[str, Any]:
        """获取业务配置"""
        pass
```

**电商适配器示例：**

```python
class EcommerceAdapter(BusinessAdapter):
    """电商业务适配器"""
    
    def __init__(self, api_base_url: str, api_key: str):
        self.api_base_url = api_base_url
        self.api_key = api_key
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        # 调用业务系统的用户API
        response = await self.call_business_api(
            f"/api/users/{user_id}"
        )
        # 转换为标准格式
        return {
            "user_id": response["id"],
            "username": response["username"],
            "email": response["email"],
            "vip_level": response.get("vip_level", 0)
        }
    
    async def query_orders(self, user_id: str, filters: Dict) -> List[Dict]:
        response = await self.call_business_api(
            f"/api/orders",
            params={"user_id": user_id, **filters}
        )
        # 转换为标准格式
        return [
            {
                "order_id": order["id"],
                "order_no": order["order_no"],
                "status": order["status"],
                "total_amount": order["total_amount"],
                "created_at": order["created_at"]
            }
            for order in response["orders"]
        ]
    
    def get_business_config(self) -> Dict[str, Any]:
        return {
            "business_name": "毕业设计商城",
            "business_type": "ecommerce",
            "features": ["order_query", "product_search", "refund"],
            "custom_intents": ["graduation_project_inquiry"]
        }
```

---


### 3. 插件系统 (Plugin System)

**作用：** 允许业务系统注册自定义功能

**插件接口：**

```python
from typing import Dict, Any, Callable

class AIPlugin(ABC):
    """AI插件基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行插件功能"""
        pass
    
    def get_schema(self) -> Dict:
        """返回插件的参数schema（用于Function Calling）"""
        return {}


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, AIPlugin] = {}
    
    def register(self, plugin: AIPlugin):
        """注册插件"""
        self.plugins[plugin.name] = plugin
    
    async def execute(self, plugin_name: str, **kwargs) -> Any:
        """执行插件"""
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin {plugin_name} not found")
        return await self.plugins[plugin_name].execute(**kwargs)
    
    def list_plugins(self) -> List[Dict]:
        """列出所有插件"""
        return [
            {
                "name": plugin.name,
                "description": plugin.description,
                "schema": plugin.get_schema()
            }
            for plugin in self.plugins.values()
        ]
```

**自定义插件示例：**

```python
class GraduationProjectPlugin(AIPlugin):
    """毕业设计项目查询插件"""
    
    @property
    def name(self) -> str:
        return "query_graduation_projects"
    
    @property
    def description(self) -> str:
        return "查询毕业设计项目，支持按技术栈、难度、价格筛选"
    
    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "tech_stack": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "技术栈列表"
                },
                "difficulty": {
                    "type": "string",
                    "enum": ["easy", "medium", "hard"],
                    "description": "难度"
                },
                "max_price": {
                    "type": "number",
                    "description": "最高价格"
                }
            }
        }
    
    async def execute(self, **kwargs) -> Any:
        # 调用业务系统API查询项目
        tech_stack = kwargs.get("tech_stack", [])
        difficulty = kwargs.get("difficulty")
        max_price = kwargs.get("max_price")
        
        # 返回标准格式
        return {
            "projects": [...],
            "total": 10
        }
```

---

### 4. 配置系统

**业务配置文件：** `config/businesses/graduation-marketplace.yaml`

```yaml
# 业务标识
business_id: graduation-marketplace
business_name: 毕业设计商城
business_type: ecommerce

# API配置
api:
  base_url: http://localhost:8000
  api_key: ${BUSINESS_API_KEY}
  timeout: 30

# 适配器配置
adapter:
  type: ecommerce
  class: adapters.EcommerceAdapter

# 功能开关
features:
  order_query: true
  product_search: true
  refund_service: true
  logistics_tracking: false  # 暂未开启

# 自定义意图
custom_intents:
  - name: graduation_project_inquiry
    description: 用户询问毕业设计项目
    keywords: [毕业设计, 项目, 作品, 源码]
  
  - name: tech_stack_query
    description: 用户询问技术栈
    keywords: [技术栈, 用什么开发, 框架]

# 插件配置
plugins:
  - name: query_graduation_projects
    enabled: true
    class: plugins.GraduationProjectPlugin
  
  - name: recommend_projects
    enabled: true
    class: plugins.ProjectRecommendationPlugin

# 知识库配置
knowledge_base:
  collections:
    - name: graduation_projects
      description: 毕业设计项目知识库
    - name: tech_docs
      description: 技术文档知识库

# 提示词模板
prompts:
  system_prompt: |
    你是毕业设计商城的AI客服助手。
    你的任务是帮助用户找到合适的毕业设计项目。
    
  greeting: |
    您好！我是毕业设计商城的AI助手，很高兴为您服务！
    我可以帮您：
    - 推荐合适的毕业设计项目
    - 查询订单状态
    - 解答技术问题
    
    请问有什么可以帮您的吗？
```

---

### 5. SDK封装

**为不同语言提供SDK，方便集成**

**Python SDK:**

```python
from ai_customer_service import AIServiceClient

# 初始化客户端
client = AIServiceClient(
    api_url="http://ai-service.com",
    business_id="graduation-marketplace",
    api_key="your_api_key"
)

# 发送消息
response = await client.send_message(
    user_id="user_123",
    session_id="session_456",
    message="我想找个Vue的毕业设计",
    context={
        "user_info": {"vip_level": 1},
        "current_page": "home"
    }
)

print(response.text)  # AI回复
print(response.quick_actions)  # 快速操作按钮
```

**JavaScript SDK:**

```javascript
import { AIServiceClient } from '@ai-service/client';

const client = new AIServiceClient({
  apiUrl: 'http://ai-service.com',
  businessId: 'graduation-marketplace',
  apiKey: 'your_api_key'
});

// 发送消息
const response = await client.sendMessage({
  userId: 'user_123',
  sessionId: 'session_456',
  message: '我想找个Vue的毕业设计',
  context: {
    userInfo: { vipLevel: 1 },
    currentPage: 'home'
  }
});

console.log(response.text);
console.log(response.quickActions);
```

**Vue组件封装:**

```vue
<template>
  <AIChat
    :business-id="businessId"
    :user-id="userId"
    :api-url="apiUrl"
    :api-key="apiKey"
    @message-sent="handleMessageSent"
    @action-clicked="handleActionClicked"
  />
</template>

<script setup>
import { AIChat } from '@ai-service/vue';

const businessId = 'graduation-marketplace';
const userId = 'user_123';
const apiUrl = 'http://ai-service.com';
const apiKey = 'your_api_key';

const handleMessageSent = (message) => {
  console.log('用户发送:', message);
};

const handleActionClicked = (action) => {
  console.log('点击操作:', action);
  // 执行相应操作，如跳转页面
};
</script>
```

---


## 部署方案

### 方案1：独立服务部署（推荐）

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   业务系统 A    │      │   业务系统 B    │      │   业务系统 C    │
│  (商城前端)     │      │  (企业系统)     │      │  (其他平台)     │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │ HTTP/WebSocket
                    ┌─────────────▼─────────────┐
                    │   AI客服服务 (独立部署)   │
                    │   - FastAPI               │
                    │   - LangGraph             │
                    │   - Redis                 │
                    │   - Chroma                │
                    └───────────────────────────┘
```

**优点：**
- 完全解耦，业务系统无需关心AI实现
- 可以独立升级和维护
- 多个业务系统共享一个AI服务
- 资源利用率高

**部署步骤：**

```bash
# 1. 克隆AI模块代码
git clone https://github.com/your-org/ai-customer-service.git
cd ai-customer-service

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 使用Docker Compose部署
docker-compose up -d

# 4. 业务系统通过API调用
# 在业务系统中配置AI服务地址
AI_SERVICE_URL=http://ai-service.com
AI_SERVICE_API_KEY=your_api_key
```

---

### 方案2：Docker镜像部署

**构建Docker镜像：**

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**使用镜像：**

```bash
# 拉取镜像
docker pull your-org/ai-customer-service:latest

# 运行容器
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e REDIS_URL=redis://redis:6379 \
  --name ai-service \
  your-org/ai-customer-service:latest
```

---

### 方案3：Python包部署

**打包为Python包：**

```bash
# 安装AI模块
pip install ai-customer-service

# 在业务系统中使用
from ai_customer_service import AIServiceApp

app = AIServiceApp(
    business_id="graduation-marketplace",
    config_path="./ai_config.yaml"
)

# 集成到FastAPI
from fastapi import FastAPI
main_app = FastAPI()
main_app.mount("/ai", app)
```

---

## 集成指南

### 快速集成（5分钟）

**步骤1：注册业务**

```bash
# 调用注册API
curl -X POST http://ai-service.com/api/v1/admin/businesses \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "my-business",
    "business_name": "我的业务系统",
    "business_type": "ecommerce",
    "api_base_url": "http://my-business.com/api",
    "api_key": "my_business_api_key"
  }'

# 返回
{
  "business_id": "my-business",
  "ai_api_key": "ai_service_key_xxx",  # 用于调用AI服务
  "status": "active"
}
```

**步骤2：配置适配器**

创建配置文件 `config/businesses/my-business.yaml`：

```yaml
business_id: my-business
business_name: 我的业务系统
business_type: ecommerce

api:
  base_url: http://my-business.com/api
  api_key: ${MY_BUSINESS_API_KEY}

adapter:
  type: ecommerce
  class: adapters.EcommerceAdapter

features:
  order_query: true
  product_search: true
```

**步骤3：前端集成**

```html
<!-- 方式1：使用iframe -->
<iframe 
  src="http://ai-service.com/chat?business_id=my-business&user_id=user_123"
  width="400" 
  height="600"
  frameborder="0"
></iframe>

<!-- 方式2：使用Web Component -->
<script src="http://ai-service.com/sdk/web-component.js"></script>
<ai-chat-widget
  business-id="my-business"
  user-id="user_123"
  api-key="ai_service_key_xxx"
  position="bottom-right"
></ai-chat-widget>

<!-- 方式3：使用Vue组件 -->
<template>
  <AIChat
    business-id="my-business"
    :user-id="userId"
    api-key="ai_service_key_xxx"
  />
</template>
```

**步骤4：测试**

```bash
# 发送测试消息
curl -X POST http://ai-service.com/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ai_service_key_xxx" \
  -d '{
    "business_id": "my-business",
    "user_id": "user_123",
    "session_id": "session_456",
    "message": "你好"
  }'
```

---

## 自定义扩展

### 添加自定义意图

```python
# plugins/custom_intents.py
from ai_customer_service.core import IntentHandler

class CustomIntentHandler(IntentHandler):
    """自定义意图处理器"""
    
    intent_name = "custom_intent"
    intent_description = "处理自定义业务逻辑"
    
    async def handle(self, state: ConversationState) -> ConversationState:
        # 自定义处理逻辑
        user_message = state["user_message"]
        
        # 调用业务API
        result = await self.call_business_api("/custom/endpoint")
        
        # 生成回复
        state["response"] = f"处理结果：{result}"
        return state

# 注册意图
from ai_customer_service import register_intent_handler
register_intent_handler(CustomIntentHandler())
```

### 添加自定义Function Tool

```python
# plugins/custom_tools.py
from ai_customer_service.tools import FunctionTool

class CustomTool(FunctionTool):
    """自定义工具"""
    
    name = "custom_query"
    description = "查询自定义数据"
    
    parameters = {
        "type": "object",
        "properties": {
            "query_type": {
                "type": "string",
                "description": "查询类型"
            },
            "filters": {
                "type": "object",
                "description": "过滤条件"
            }
        },
        "required": ["query_type"]
    }
    
    async def execute(self, query_type: str, filters: dict = None):
        # 执行查询
        result = await self.adapter.custom_query(query_type, filters)
        return result

# 注册工具
from ai_customer_service import register_tool
register_tool(CustomTool())
```

### 自定义提示词模板

```yaml
# config/businesses/my-business.yaml
prompts:
  system_prompt: |
    你是{business_name}的AI客服助手。
    你的职责是：
    1. 回答用户问题
    2. 提供专业建议
    3. 保持友好态度
    
    当前业务特点：
    {business_features}
  
  greeting: |
    您好！欢迎来到{business_name}！
    我是AI助手，很高兴为您服务。
    
  error_message: |
    抱歉，我遇到了一些问题。
    请稍后再试，或联系人工客服。
```

---

## 数据隔离

### 多租户数据隔离

**方案1：数据库级隔离（推荐）**

```python
# 每个业务使用独立的数据库schema
class MultiTenantDatabase:
    def get_connection(self, business_id: str):
        # 根据business_id选择对应的schema
        schema_name = f"business_{business_id}"
        return f"postgresql://user:pass@host/db?options=-c search_path={schema_name}"
```

**方案2：表级隔离**

```sql
-- 所有表添加business_id字段
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    business_id VARCHAR(50) NOT NULL,  -- 业务标识
    user_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_business_id (business_id)
);

-- 查询时自动过滤
SELECT * FROM conversations 
WHERE business_id = 'my-business' 
AND user_id = 'user_123';
```

**方案3：知识库隔离**

```python
# Chroma集合命名规则
collection_name = f"{business_id}_knowledge_base"

# 每个业务独立的知识库
knowledge_retriever.retrieve(
    query=query,
    collection_name=f"{business_id}_knowledge_base"
)
```

---

## 监控与管理

### 管理后台

**业务管理面板：**

```
http://ai-service.com/admin

功能：
- 业务列表和配置
- 对话监控和分析
- 知识库管理
- 插件管理
- 性能监控
- 日志查看
```

**监控指标：**

```python
# 每个业务的独立指标
metrics = {
    "business_id": "my-business",
    "total_conversations": 1000,
    "total_messages": 5000,
    "avg_response_time": 1.2,  # 秒
    "success_rate": 0.95,
    "user_satisfaction": 4.5,  # 1-5分
    "active_users": 50,
    "peak_concurrent_users": 20
}
```

---


## 实施路线图

### 阶段1：核心架构重构（2周）

**目标：** 将现有系统改造为可插拔架构

**任务清单：**

- [ ] **1.1 创建适配器层**
  - 定义BusinessAdapter接口
  - 实现EcommerceAdapter
  - 重构现有代码使用适配器

- [ ] **1.2 实现插件系统**
  - 创建Plugin基类和PluginManager
  - 将现有功能改造为插件
  - 实现插件注册和加载机制

- [ ] **1.3 配置系统**
  - 设计配置文件格式
  - 实现配置加载和验证
  - 支持多业务配置

- [ ] **1.4 API Gateway**
  - 统一API入口
  - 添加business_id参数
  - 实现请求路由

**修改文件：**
```
backend/
├── adapters/
│   ├── __init__.py
│   ├── base.py              # BusinessAdapter基类
│   └── ecommerce.py         # 电商适配器
├── plugins/
│   ├── __init__.py
│   ├── base.py              # Plugin基类
│   ├── manager.py           # PluginManager
│   └── builtin/             # 内置插件
│       ├── order_query.py
│       ├── product_search.py
│       └── ticket_create.py
├── config/
│   ├── __init__.py
│   ├── loader.py            # 配置加载器
│   └── businesses/          # 业务配置目录
│       └── graduation-marketplace.yaml
└── api/
    └── gateway.py           # API网关
```

---

### 阶段2：数据隔离与多租户（1周）

**目标：** 实现多业务数据隔离

**任务清单：**

- [ ] **2.1 数据库改造**
  - 添加business_id字段到所有表
  - 创建数据库迁移脚本
  - 实现自动数据隔离

- [ ] **2.2 知识库隔离**
  - 按业务创建独立Chroma集合
  - 实现知识库命名空间
  - 迁移现有知识库数据

- [ ] **2.3 缓存隔离**
  - Redis key添加业务前缀
  - 实现缓存命名空间

**修改文件：**
```
backend/
├── database/
│   ├── migrations/          # 数据库迁移
│   │   └── add_business_id.sql
│   └── multi_tenant.py      # 多租户支持
└── services/
    ├── knowledge_retriever.py  # 支持业务隔离
    └── redis_cache.py          # 支持业务隔离
```

---

### 阶段3：SDK开发（1周）

**目标：** 提供易用的集成SDK

**任务清单：**

- [ ] **3.1 Python SDK**
  - 创建客户端库
  - 实现同步/异步接口
  - 添加错误处理和重试

- [ ] **3.2 JavaScript SDK**
  - 创建NPM包
  - 支持浏览器和Node.js
  - 实现WebSocket连接

- [ ] **3.3 Vue组件**
  - 创建AIChat组件
  - 支持自定义样式
  - 发布到NPM

- [ ] **3.4 Web Component**
  - 创建独立的Web Component
  - 支持任何前端框架
  - CDN部署

**创建文件：**
```
sdk/
├── python/
│   ├── ai_customer_service/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── models.py
│   ├── setup.py
│   └── README.md
├── javascript/
│   ├── src/
│   │   ├── client.ts
│   │   ├── websocket.ts
│   │   └── types.ts
│   ├── package.json
│   └── README.md
├── vue/
│   ├── src/
│   │   ├── AIChat.vue
│   │   └── index.ts
│   ├── package.json
│   └── README.md
└── web-component/
    ├── src/
    │   └── ai-chat-widget.ts
    ├── package.json
    └── README.md
```

---

### 阶段4：文档与示例（3天）

**目标：** 完善文档，降低集成门槛

**任务清单：**

- [ ] **4.1 API文档**
  - 使用OpenAPI规范
  - 生成交互式文档
  - 添加代码示例

- [ ] **4.2 集成指南**
  - 快速开始教程
  - 详细集成步骤
  - 常见问题解答

- [ ] **4.3 示例项目**
  - 电商集成示例
  - 企业系统集成示例
  - 最小化示例

**创建文件：**
```
docs/
├── api/
│   ├── openapi.yaml
│   └── endpoints.md
├── guides/
│   ├── quick-start.md
│   ├── integration.md
│   ├── customization.md
│   └── deployment.md
├── examples/
│   ├── ecommerce/
│   ├── enterprise/
│   └── minimal/
└── faq.md
```

---

## 使用场景示例

### 场景1：电商平台集成

```python
# 业务系统：毕业设计商城
# 需求：AI客服帮助用户查询订单、推荐商品

# 1. 配置适配器
class GraduationMarketplaceAdapter(EcommerceAdapter):
    async def query_orders(self, user_id: str, filters: Dict):
        # 调用商城API
        response = await self.http_client.get(
            f"{self.api_base_url}/api/orders",
            params={"user_id": user_id, **filters}
        )
        return response.json()

# 2. 注册自定义插件
class ProjectRecommendationPlugin(AIPlugin):
    name = "recommend_projects"
    description = "推荐毕业设计项目"
    
    async def execute(self, tech_stack=None, difficulty=None, budget=None):
        # 调用推荐算法
        projects = await self.adapter.search_products(
            filters={
                "tech_stack": tech_stack,
                "difficulty": difficulty,
                "max_price": budget
            }
        )
        return projects

# 3. 前端集成
# 在Vue组件中使用
<AIChat
  business-id="graduation-marketplace"
  :user-id="currentUser.id"
  :context="{ vipLevel: currentUser.vipLevel }"
/>
```

---

### 场景2：企业内部系统集成

```python
# 业务系统：企业OA系统
# 需求：AI助手帮助员工查询考勤、请假、报销

# 1. 创建企业适配器
class EnterpriseAdapter(BusinessAdapter):
    async def query_attendance(self, employee_id: str, date_range: Dict):
        # 查询考勤记录
        pass
    
    async def submit_leave_request(self, employee_id: str, leave_data: Dict):
        # 提交请假申请
        pass
    
    async def query_reimbursement(self, employee_id: str):
        # 查询报销状态
        pass

# 2. 配置文件
# config/businesses/my-company.yaml
business_id: my-company
business_name: XX公司OA系统
business_type: enterprise

adapter:
  type: enterprise
  class: adapters.EnterpriseAdapter

custom_intents:
  - name: attendance_query
    description: 查询考勤记录
  - name: leave_request
    description: 请假申请
  - name: reimbursement_query
    description: 查询报销

# 3. 集成到企业系统
# 在企业门户添加AI助手入口
<ai-chat-widget
  business-id="my-company"
  user-id="{{ employee.id }}"
  api-key="enterprise_api_key"
  theme="corporate"
></ai-chat-widget>
```

---

### 场景3：SaaS平台集成

```python
# 业务系统：多租户SaaS平台
# 需求：为每个租户提供独立的AI客服

# 1. 动态注册租户
async def register_tenant(tenant_id: str, tenant_config: Dict):
    # 调用AI服务注册API
    response = await ai_service_client.register_business(
        business_id=f"tenant_{tenant_id}",
        business_name=tenant_config["name"],
        business_type="saas",
        api_base_url=f"https://api.saas-platform.com/tenants/{tenant_id}",
        api_key=tenant_config["api_key"]
    )
    return response

# 2. 租户使用AI服务
# 每个租户有独立的配置和数据
<AIChat
  :business-id="`tenant_${tenantId}`"
  :user-id="userId"
  :api-key="aiServiceKey"
  :custom-config="tenantAIConfig"
/>

# 3. 数据完全隔离
# - 独立的知识库
# - 独立的对话历史
# - 独立的配置
```

---

## 优势总结

### 对开发者的优势

1. **快速集成** - 5分钟接入，无需了解AI实现细节
2. **灵活定制** - 插件系统支持任意扩展
3. **多语言SDK** - Python、JavaScript、Vue等
4. **完善文档** - API文档、集成指南、示例代码

### 对业务的优势

1. **降低成本** - 无需自建AI团队
2. **快速上线** - 即插即用，快速部署
3. **持续优化** - AI模块统一升级，所有业务受益
4. **数据安全** - 完全隔离，互不影响

### 对用户的优势

1. **统一体验** - 不同平台的AI助手体验一致
2. **智能服务** - 持续优化的AI能力
3. **快速响应** - 7x24小时在线服务

---

## 下一步行动

### 立即开始（本周）

1. **重构适配器层** - 将现有代码改造为适配器模式
2. **创建配置系统** - 支持多业务配置
3. **实现插件管理器** - 支持动态加载插件

### 短期目标（2周内）

1. **完成核心架构** - 适配器、插件、配置系统
2. **实现数据隔离** - 多租户支持
3. **开发Python SDK** - 方便其他系统集成

### 中期目标（1个月内）

1. **完善SDK** - JavaScript、Vue组件
2. **编写文档** - API文档、集成指南
3. **创建示例** - 多个集成示例项目

### 长期目标（3个月内）

1. **商业化** - 提供SaaS服务
2. **生态建设** - 插件市场、社区
3. **持续优化** - 性能、功能、体验

---

## 总结

通过这个**即插即用的AI客服模块架构**，你可以：

✅ **轻松集成** - 任何系统5分钟接入  
✅ **灵活扩展** - 插件化架构，无限可能  
✅ **数据隔离** - 多租户安全保障  
✅ **持续进化** - 统一升级，全员受益  

**这不仅是一个AI客服系统，更是一个AI服务平台！**

现在就开始重构，让你的AI模块成为可以服务多个业务的通用平台！🚀

