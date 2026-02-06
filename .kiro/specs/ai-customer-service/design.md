# 设计文档：AI客服系统

## 概述

AI客服系统是一个基于LangChain和LangGraph的智能客户服务平台，提供多模态交互、知识库检索、工单管理等功能。系统采用前后端分离架构，前端使用Vue 3构建响应式用户界面，后端使用FastAPI提供RESTful API服务。

**核心技术栈：**
- 前端：Vue 3 + TypeScript + Vite
- 后端：FastAPI + Python 3.10+
- AI框架：LangChain 1.2.7 + LangGraph 1.0.7
- 主数据库：MySQL 8.0+
- 向量数据库：Chroma
- 缓存：Redis（可选）
- 消息队列：Celery + Redis（可选，用于异步任务）

**设计原则：**
1. 模块化：各组件职责清晰，低耦合高内聚
2. 可扩展：支持水平扩展和功能扩展
3. 可测试：所有核心逻辑可单元测试
4. 安全性：数据加密、权限控制、审计日志
5. 性能优化：异步处理、连接池、缓存策略

## 系统架构

### 整体架构图

```mermaid
graph TB
    subgraph "前端层"
        UI[Vue 3 用户界面]
        Admin[Vue 3 管理后台]
    end
    
    subgraph "API网关层"
        Gateway[FastAPI 网关]
        Auth[认证中间件]
        CORS[CORS中间件]
    end
    
    subgraph "业务逻辑层"
        ChatAPI[对话API]
        TicketAPI[工单API]
        HistoryAPI[历史API]
        AdminAPI[管理API]
    end
    
    subgraph "AI处理层"
        LangGraph[LangGraph工作流引擎]
        IntentRecognizer[意图识别器]
        Router[路由器]
        QAHandler[问答处理器]
        TicketHandler[工单处理器]
        ProductHandler[产品咨询处理器]
    end
    
    subgraph "数据访问层"
        KnowledgeRetriever[知识检索器]
        ContextManager[上下文管理器]
        DBService[数据库服务]
    end
    
    subgraph "数据存储层"
        MySQL[(MySQL数据库)]
        Chroma[(Chroma向量库)]
        Redis[(Redis缓存)]
        FileStorage[文件存储]
    end
    
    UI --> Gateway
    Admin --> Gateway
    Gateway --> Auth
    Auth --> ChatAPI
    Auth --> TicketAPI
    Auth --> HistoryAPI
    Auth --> AdminAPI
    
    ChatAPI --> LangGraph
    LangGraph --> IntentRecognizer
    IntentRecognizer --> Router
    Router --> QAHandler
    Router --> TicketHandler
    Router --> ProductHandler
    
    QAHandler --> KnowledgeRetriever
    ProductHandler --> KnowledgeRetriever
    TicketHandler --> DBService
    
    KnowledgeRetriever --> Chroma
    ContextManager --> Redis
    DBService --> MySQL
    QAHandler --> FileStorage
```

### 架构层次说明

**1. 前端层**
- 用户界面：提供对话交互、文件上传、历史查看功能
- 管理后台：提供系统配置、对话监控、知识库管理功能

**2. API网关层**
- FastAPI网关：统一入口，路由分发
- 认证中间件：JWT令牌验证，用户身份识别
- CORS中间件：跨域资源共享配置

**3. 业务逻辑层**
- 对话API：处理用户消息，调用AI引擎
- 工单API：创建、查询、更新工单
- 历史API：查询对话历史记录
- 管理API：系统配置、知识库管理

**4. AI处理层（LangGraph工作流）**
- 意图识别器：分析用户消息意图
- 路由器：根据意图路由到不同处理器
- 问答处理器：知识库检索+回答生成
- 工单处理器：提取信息+创建工单
- 产品咨询处理器：产品信息检索+推荐

**5. 数据访问层**
- 知识检索器：向量相似度搜索
- 上下文管理器：会话上下文维护
- 数据库服务：CRUD操作封装

**6. 数据存储层**
- MySQL：用户、会话、消息、工单数据
- Chroma：知识库向量索引
- Redis：会话缓存、配置缓存
- 文件存储：上传的图片和文件

## LangGraph对话工作流设计

### 工作流状态机

```mermaid
stateDiagram-v2
    [*] --> ReceiveMessage: 用户消息到达
    
    ReceiveMessage --> LoadContext: 加载会话上下文
    LoadContext --> IntentRecognition: 意图识别
    
    IntentRecognition --> RouteDecision: 路由决策
    
    RouteDecision --> QAFlow: 意图=问答
    RouteDecision --> TicketFlow: 意图=工单
    RouteDecision --> ProductFlow: 意图=产品咨询
    RouteDecision --> ClarifyIntent: 意图不明确
    
    QAFlow --> KnowledgeRetrieval: 检索知识库
    KnowledgeRetrieval --> GenerateAnswer: 生成回答
    
    TicketFlow --> ExtractInfo: 提取工单信息
    ExtractInfo --> CreateTicket: 创建工单
    
    ProductFlow --> RetrieveProduct: 检索产品信息
    RetrieveProduct --> GenerateRecommendation: 生成推荐
    
    ClarifyIntent --> AskClarification: 请求澄清
    AskClarification --> [*]: 返回澄清问题
    
    GenerateAnswer --> SaveContext: 保存上下文
    CreateTicket --> SaveContext
    GenerateRecommendation --> SaveContext
    
    SaveContext --> [*]: 返回响应
```


### LangGraph节点定义

**1. ReceiveMessage节点**
```python
def receive_message_node(state: ConversationState) -> ConversationState:
    """接收用户消息并初始化状态"""
    return {
        "user_message": state["user_message"],
        "user_id": state["user_id"],
        "session_id": state["session_id"],
        "timestamp": datetime.now(),
        "attachments": state.get("attachments", [])
    }
```

**2. LoadContext节点**
```python
def load_context_node(state: ConversationState) -> ConversationState:
    """从Redis/数据库加载会话上下文"""
    context = context_manager.get_context(state["session_id"])
    state["conversation_history"] = context.get("history", [])
    state["user_profile"] = context.get("profile", {})
    return state
```

**3. IntentRecognition节点（增强版）**
```python
def intent_recognition_node(state: ConversationState) -> ConversationState:
    """使用LLM识别用户意图 - 增强上下文感知"""
    
    # 获取页面上下文
    page_context = state.get("page_context", {})
    current_page = page_context.get("page") if page_context else None
    
    # 根据页面上下文调整意图识别
    context_hints = []
    
    if current_page == "product_detail":
        context_hints.append("用户正在查看商品详情")
        product_title = page_context.get("product_title")
        if product_title:
            context_hints.append(f"当前商品：{product_title}")
    
    elif current_page == "cart":
        cart_items = page_context.get("cart_items", [])
        context_hints.append(f"用户购物车有{len(cart_items)}件商品")
        context_hints.append(f"总金额：¥{page_context.get('cart_total', 0)}")
    
    elif current_page == "orders":
        context_hints.append("用户正在查看订单")
    
    elif current_page == "product_list":
        category = page_context.get("category")
        if category:
            context_hints.append(f"用户正在浏览{category}类别商品")
    
    # 将上下文提示加入prompt
    prompt = f"""
    分析以下用户消息的意图：
    消息：{state["user_message"]}
    历史：{state["conversation_history"][-5:]}
    
    当前上下文：
    {chr(10).join(context_hints) if context_hints else "无特定上下文"}
    
    可能的意图：问答、工单、产品咨询、购买咨询、订单查询、闲聊
    返回JSON格式：{{"intent": "...", "confidence": 0.0-1.0}}
    """
    result = llm.invoke(prompt)
    state["intent"] = result["intent"]
    state["confidence"] = result["confidence"]
    return state
```

**4. RouteDecision节点（条件边）**
```python
def route_decision(state: ConversationState) -> str:
    """根据意图决定路由"""
    if state["confidence"] < 0.6:
        return "clarify"
    
    intent_map = {
        "问答": "qa_flow",
        "工单": "ticket_flow",
        "产品咨询": "product_flow"
    }
    return intent_map.get(state["intent"], "clarify")
```

**5. QAFlow节点**
```python
def qa_flow_node(state: ConversationState) -> ConversationState:
    """问答流程：检索+生成"""
    # 检索相关文档
    docs = knowledge_retriever.retrieve(
        query=state["user_message"],
        top_k=3
    )
    state["retrieved_docs"] = docs
    
    # 生成回答
    prompt = f"""
    基于以下知识库内容回答用户问题：
    问题：{state["user_message"]}
    知识库：{docs}
    历史：{state["conversation_history"][-3:]}
    
    要求：准确、简洁、引用来源
    """
    answer = llm.invoke(prompt)
    state["response"] = answer
    state["sources"] = [doc.metadata for doc in docs]
    return state
```

**6. TicketFlow节点**
```python
def ticket_flow_node(state: ConversationState) -> ConversationState:
    """工单流程：提取信息+创建工单"""
    # 提取工单信息
    prompt = f"""
    从用户消息中提取工单信息：
    消息：{state["user_message"]}
    历史：{state["conversation_history"]}
    
    提取：问题描述、优先级、类别
    返回JSON格式
    """
    ticket_info = llm.invoke(prompt)
    
    # 创建工单
    ticket = ticket_service.create_ticket(
        user_id=state["user_id"],
        title=ticket_info["title"],
        description=ticket_info["description"],
        priority=ticket_info["priority"],
        context=state["conversation_history"]
    )
    
    state["response"] = f"工单已创建，工单号：{ticket.id}"
    state["ticket_id"] = ticket.id
    return state
```

**7. ProductFlow节点**
```python
def product_flow_node(state: ConversationState) -> ConversationState:
    """产品咨询流程：检索产品信息+推荐"""
    # 检索产品信息
    products = product_retriever.retrieve(
        query=state["user_message"],
        top_k=5
    )
    
    # 生成推荐
    prompt = f"""
    基于以下产品信息回答用户咨询：
    问题：{state["user_message"]}
    产品信息：{products}
    
    要求：突出产品特点、价格、适用场景
    """
    recommendation = llm.invoke(prompt)
    state["response"] = recommendation
    state["recommended_products"] = [p.id for p in products]
    return state
```

**8. SaveContext节点**
```python
def save_context_node(state: ConversationState) -> ConversationState:
    """保存对话上下文和消息"""
    # 保存到数据库
    message_service.save_message(
        session_id=state["session_id"],
        user_message=state["user_message"],
        ai_response=state["response"],
        metadata={
            "intent": state.get("intent"),
            "sources": state.get("sources"),
            "ticket_id": state.get("ticket_id")
        }
    )
    
    # 更新上下文缓存
    context_manager.update_context(
        session_id=state["session_id"],
        new_turn={
            "user": state["user_message"],
            "assistant": state["response"]
        }
    )
    return state
```

### LangGraph工作流构建

```python
from langgraph.graph import StateGraph, END

# 定义状态类型
class ConversationState(TypedDict):
    user_message: str
    user_id: str
    session_id: str
    conversation_history: List[Dict]
    intent: str
    confidence: float
    response: str
    # ... 其他字段

# 构建图
workflow = StateGraph(ConversationState)

# 添加节点
workflow.add_node("receive", receive_message_node)
workflow.add_node("load_context", load_context_node)
workflow.add_node("intent_recognition", intent_recognition_node)
workflow.add_node("qa_flow", qa_flow_node)
workflow.add_node("ticket_flow", ticket_flow_node)
workflow.add_node("product_flow", product_flow_node)
workflow.add_node("clarify", clarify_intent_node)
workflow.add_node("save_context", save_context_node)

# 添加边
workflow.add_edge("receive", "load_context")
workflow.add_edge("load_context", "intent_recognition")

# 添加条件边（路由）
workflow.add_conditional_edges(
    "intent_recognition",
    route_decision,
    {
        "qa_flow": "qa_flow",
        "ticket_flow": "ticket_flow",
        "product_flow": "product_flow",
        "clarify": "clarify"
    }
)

workflow.add_edge("qa_flow", "save_context")
workflow.add_edge("ticket_flow", "save_context")
workflow.add_edge("product_flow", "save_context")
workflow.add_edge("clarify", END)
workflow.add_edge("save_context", END)

# 设置入口点
workflow.set_entry_point("receive")

# 编译图
conversation_graph = workflow.compile()
```


## 组件与接口设计

### 1. 认证服务（AuthService）

**职责：** 用户认证、会话管理、JWT令牌生成与验证

**接口：**
```python
class AuthService:
    def login(self, username: str, password: str) -> AuthToken:
        """用户登录，返回JWT令牌"""
        
    def verify_token(self, token: str) -> User:
        """验证JWT令牌，返回用户信息"""
        
    def create_session(self, user_id: str) -> Session:
        """创建新的对话会话"""
        
    def get_session(self, session_id: str) -> Session:
        """获取会话信息"""
        
    def refresh_token(self, refresh_token: str) -> AuthToken:
        """刷新访问令牌"""
```

### 2. 对话引擎（ConversationEngine）

**职责：** 协调LangGraph工作流，处理用户消息

**接口：**
```python
class ConversationEngine:
    def __init__(self, graph: CompiledGraph, llm: BaseLLM):
        self.graph = graph
        self.llm = llm
        
    async def process_message(
        self,
        user_id: str,
        session_id: str,
        message: str,
        attachments: List[Attachment] = None
    ) -> ConversationResponse:
        """处理用户消息，返回AI响应"""
        
    async def stream_response(
        self,
        user_id: str,
        session_id: str,
        message: str
    ) -> AsyncIterator[str]:
        """流式返回AI响应"""
```

### 3. 知识检索器（KnowledgeRetriever）

**职责：** 从Chroma向量数据库检索相关文档

**接口：**
```python
class KnowledgeRetriever:
    def __init__(self, chroma_client: ChromaClient, embedding_model: Embeddings):
        self.client = chroma_client
        self.embeddings = embedding_model
        
    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        filter: Dict = None
    ) -> List[Document]:
        """检索相关文档"""
        
    def add_documents(
        self,
        documents: List[Document],
        collection_name: str = "knowledge_base"
    ) -> None:
        """添加文档到知识库"""
        
    def delete_document(self, document_id: str) -> None:
        """删除文档"""
```

### 4. 上下文管理器（ContextManager）

**职责：** 管理会话上下文，维护对话历史

**接口：**
```python
class ContextManager:
    def __init__(self, redis_client: Redis, max_history: int = 20):
        self.redis = redis_client
        self.max_history = max_history
        
    def get_context(self, session_id: str) -> ConversationContext:
        """获取会话上下文"""
        
    def update_context(
        self,
        session_id: str,
        new_turn: Dict[str, str]
    ) -> None:
        """更新会话上下文"""
        
    def clear_context(self, session_id: str) -> None:
        """清除会话上下文"""
```

### 5. 工单服务（TicketService）

**职责：** 创建、查询、更新工单

**接口：**
```python
class TicketService:
    def create_ticket(
        self,
        user_id: str,
        title: str,
        description: str,
        priority: str = "medium",
        context: List[Dict] = None
    ) -> Ticket:
        """创建工单"""
        
    def get_ticket(self, ticket_id: str) -> Ticket:
        """获取工单详情"""
        
    def update_ticket_status(
        self,
        ticket_id: str,
        status: str,
        operator_id: str
    ) -> Ticket:
        """更新工单状态"""
        
    def list_user_tickets(
        self,
        user_id: str,
        status: str = None
    ) -> List[Ticket]:
        """列出用户的工单"""
```

### 6. 消息服务（MessageService）

**职责：** 持久化对话消息

**接口：**
```python
class MessageService:
    def save_message(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        metadata: Dict = None
    ) -> Message:
        """保存消息"""
        
    def get_session_messages(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Message]:
        """获取会话的所有消息"""
        
    def search_messages(
        self,
        user_id: str = None,
        keyword: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[Message]:
        """搜索消息"""
```

### 7. 文件服务（FileService）

**职责：** 处理文件上传、存储、检索

**接口：**
```python
class FileService:
    def upload_file(
        self,
        file: UploadFile,
        user_id: str,
        session_id: str
    ) -> FileMetadata:
        """上传文件"""
        
    def get_file(self, file_id: str) -> bytes:
        """获取文件内容"""
        
    def extract_text(self, file_id: str) -> str:
        """从文件提取文本内容"""
        
    def analyze_image(self, file_id: str) -> ImageAnalysis:
        """分析图片内容（使用视觉模型）"""
```

## 数据模型设计

### MySQL数据库表结构

**1. users表（用户表）**
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**2. sessions表（会话表）**
```sql
CREATE TABLE sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP,
    message_count INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**3. messages表（消息表）**
```sql
CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**4. attachments表（附件表）**
```sql
CREATE TABLE attachments (
    id VARCHAR(36) PRIMARY KEY,
    message_id VARCHAR(36) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    INDEX idx_message_id (message_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**5. tickets表（工单表）**
```sql
CREATE TABLE tickets (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    status ENUM('pending', 'in_progress', 'resolved', 'closed') DEFAULT 'pending',
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    category VARCHAR(50),
    assigned_to VARCHAR(36),
    context JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**6. ticket_history表（工单历史表）**
```sql
CREATE TABLE ticket_history (
    id VARCHAR(36) PRIMARY KEY,
    ticket_id VARCHAR(36) NOT NULL,
    operator_id VARCHAR(36),
    action VARCHAR(50) NOT NULL,
    old_value VARCHAR(100),
    new_value VARCHAR(100),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (operator_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_ticket_id (ticket_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**7. knowledge_documents表（知识库文档元数据表）**
```sql
CREATE TABLE knowledge_documents (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    tags JSON,
    source VARCHAR(200),
    version INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_category (category),
    INDEX idx_is_active (is_active),
    FULLTEXT idx_content (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**8. system_config表（系统配置表）**
```sql
CREATE TABLE system_config (
    id VARCHAR(36) PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description VARCHAR(500),
    updated_by VARCHAR(36),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**9. audit_logs表（审计日志表）**
```sql
CREATE TABLE audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(36),
    details JSON,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```


### Chroma向量数据库设计

**Collection结构：**

**1. knowledge_base集合（通用知识库）**
```python
{
    "name": "knowledge_base",
    "metadata": {
        "description": "通用产品知识库",
        "embedding_model": "text-embedding-ada-002"
    },
    "documents": [
        {
            "id": "doc_uuid",
            "content": "文档内容...",
            "metadata": {
                "title": "文档标题",
                "category": "FAQ",
                "source": "manual.pdf",
                "page": 5,
                "created_at": "2024-01-01T00:00:00Z",
                "doc_id": "对应MySQL中的knowledge_documents.id"
            },
            "embedding": [0.1, 0.2, ...]  # 向量表示
        }
    ]
}
```

**2. product_catalog集合（产品目录）**
```python
{
    "name": "product_catalog",
    "metadata": {
        "description": "产品信息库",
        "embedding_model": "text-embedding-ada-002"
    },
    "documents": [
        {
            "id": "product_uuid",
            "content": "产品名称、描述、特性...",
            "metadata": {
                "product_id": "P001",
                "name": "产品A",
                "price": 999.00,
                "category": "电子产品",
                "features": ["特性1", "特性2"],
                "in_stock": true
            },
            "embedding": [0.1, 0.2, ...]
        }
    ]
}
```

**检索策略：**
- 使用余弦相似度进行向量检索
- 支持元数据过滤（如按类别、日期范围）
- 返回top_k个最相关文档（默认k=3）
- 相似度阈值：0.7（低于此值视为不相关）

### Redis缓存设计

**1. 会话上下文缓存**
```
Key: session:{session_id}:context
Type: Hash
TTL: 3600秒（1小时）
Fields:
  - history: JSON字符串，最近20轮对话
  - user_profile: JSON字符串，用户信息
  - last_intent: 最后识别的意图
  - updated_at: 最后更新时间
```

**2. 用户认证令牌缓存**
```
Key: auth:token:{token_hash}
Type: String
TTL: 86400秒（24小时）
Value: user_id
```

**3. 系统配置缓存**
```
Key: config:system
Type: Hash
TTL: 300秒（5分钟）
Fields:
  - llm_temperature: 0.7
  - llm_max_tokens: 2000
  - retrieval_top_k: 3
  - max_concurrent_sessions: 50
```

**4. 速率限制**
```
Key: ratelimit:{user_id}:{endpoint}
Type: String
TTL: 60秒
Value: 请求计数
```

### Python数据模型（Pydantic）

**1. 用户模型**
```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class User(BaseModel):
    id: str
    username: str
    email: Optional[EmailStr]
    role: str = "user"
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool = True

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr]

class AuthToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
```

**2. 会话模型**
```python
class Session(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]
    message_count: int = 0
    is_active: bool = True

class SessionCreate(BaseModel):
    user_id: str
    title: Optional[str] = "新对话"
```

**3. 消息模型**
```python
class Message(BaseModel):
    id: str
    session_id: str
    role: str  # user, assistant, system
    content: str
    metadata: Optional[dict]
    created_at: datetime

class MessageCreate(BaseModel):
    session_id: str
    role: str
    content: str
    metadata: Optional[dict] = None

class ConversationResponse(BaseModel):
    message_id: str
    content: str
    sources: Optional[List[dict]] = None
    intent: Optional[str] = None
    ticket_id: Optional[str] = None
    recommended_products: Optional[List[dict]] = None  # 新增：推荐商品
    quick_actions: Optional[List[dict]] = None  # 新增：快速操作
```

**4. 工单模型**
```python
class Ticket(BaseModel):
    id: str
    user_id: str
    session_id: Optional[str]
    title: str
    description: str
    status: str  # pending, in_progress, resolved, closed
    priority: str  # low, medium, high, urgent
    category: Optional[str]
    assigned_to: Optional[str]
    context: Optional[dict]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

class TicketCreate(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    category: Optional[str]
    context: Optional[dict]
```

**5. 附件模型**
```python
class Attachment(BaseModel):
    id: str
    message_id: str
    file_name: str
    file_type: str
    file_size: int
    file_path: str
    mime_type: Optional[str]
    created_at: datetime

class FileUpload(BaseModel):
    file_name: str
    file_type: str
    file_size: int
    content: bytes
```

**6. 页面上下文模型（新增）**
```python
class PageContext(BaseModel):
    """页面上下文 - 用于AI感知用户当前浏览状态"""
    page: str  # 页面类型：product_detail, product_list, cart, orders, home
    
    # 商品详情页上下文
    product_id: Optional[str] = None
    product_title: Optional[str] = None
    product_price: Optional[float] = None
    product_description: Optional[str] = None
    product_tech_stack: Optional[List[str]] = None
    
    # 购物车上下文
    cart_items: Optional[List[dict]] = None
    cart_total: Optional[float] = None
    cart_item_count: Optional[int] = None
    
    # 订单上下文
    order_id: Optional[str] = None
    order_status: Optional[str] = None
    
    # 商品列表上下文
    category: Optional[str] = None
    search_query: Optional[str] = None
    
    # 用户行为数据
    time_on_page: Optional[int] = None  # 页面停留时间（秒）
    scroll_depth: Optional[float] = None  # 滚动深度（百分比）
```

**7. 聊天请求模型（增强）**
```python
class ChatRequest(BaseModel):
    """聊天请求 - 增强版包含页面上下文"""
    user_id: str
    session_id: str
    message: str
    context: Optional[PageContext] = None  # 新增：页面上下文
    attachments: Optional[List[Dict]] = None
```

**8. AI建议模型（新增）**
```python
class AISuggestion(BaseModel):
    """AI建议 - 用于购物车等页面的智能推荐"""
    type: str  # coupon, bundle, product_recommendation
    title: str
    description: str
    action_url: Optional[str] = None
    action_data: Optional[dict] = None
    priority: int = 0  # 优先级，数字越大越重要

class CartSuggestionsResponse(BaseModel):
    """购物车建议响应"""
    coupon_suggestion: Optional[AISuggestion] = None
    bundle_recommendation: Optional[AISuggestion] = None
    product_recommendations: Optional[List[dict]] = None
```

**9. LangGraph状态模型（增强）**
```python
from typing import TypedDict, List, Dict, Optional

class ConversationState(TypedDict):
    # 输入
    user_message: str
    user_id: str
    session_id: str
    attachments: Optional[List[Attachment]]
    page_context: Optional[PageContext]  # 新增：页面上下文
    
    # 上下文
    conversation_history: List[Dict[str, str]]
    user_profile: Dict
    
    # 处理过程
    intent: Optional[str]
    confidence: Optional[float]
    retrieved_docs: Optional[List[dict]]
    
    # 输出
    response: str
    sources: Optional[List[dict]]
    ticket_id: Optional[str]
    recommended_products: Optional[List[str]]
    quick_actions: Optional[List[dict]]  # 新增：快速操作按钮
    
    # 元数据
    timestamp: datetime
    processing_time: Optional[float]
```

## API接口设计

### 认证相关API

**POST /api/auth/login**
```python
# 请求
{
    "username": "user123",
    "password": "password123"
}

# 响应
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 86400
}
```

**POST /api/auth/refresh**
```python
# 请求
{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# 响应
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 86400
}
```

**POST /api/auth/logout**
```python
# 请求头
Authorization: Bearer <access_token>

# 响应
{
    "message": "登出成功"
}
```

### 对话相关API

**POST /api/chat/message**
```python
# 请求
{
    "session_id": "session_uuid",
    "message": "如何重置密码？",
    "attachments": []  # 可选
}

# 响应
{
    "message_id": "msg_uuid",
    "content": "重置密码的步骤如下：\n1. 点击登录页面的'忘记密码'\n2. 输入注册邮箱...",
    "sources": [
        {
            "title": "用户手册",
            "page": 5,
            "relevance": 0.92
        }
    ],
    "intent": "问答",
    "processing_time": 1.2
}
```

**POST /api/chat/stream**
```python
# 请求
{
    "session_id": "session_uuid",
    "message": "介绍一下你们的产品"
}

# 响应（Server-Sent Events流）
data: {"type": "start", "message_id": "msg_uuid"}

data: {"type": "content", "delta": "我们的"}

data: {"type": "content", "delta": "产品包括"}

data: {"type": "content", "delta": "..."}

data: {"type": "end", "sources": [...]}
```

**POST /api/chat/session**
```python
# 请求
{
    "title": "产品咨询"  # 可选
}

# 响应
{
    "session_id": "session_uuid",
    "title": "产品咨询",
    "created_at": "2024-01-01T00:00:00Z"
}
```

**GET /api/chat/sessions**
```python
# 请求参数
?limit=20&offset=0

# 响应
{
    "sessions": [
        {
            "id": "session_uuid",
            "title": "产品咨询",
            "created_at": "2024-01-01T00:00:00Z",
            "message_count": 15,
            "last_message_at": "2024-01-01T01:00:00Z"
        }
    ],
    "total": 50
}
```

**GET /api/chat/session/{session_id}/messages**
```python
# 响应
{
    "messages": [
        {
            "id": "msg_uuid",
            "role": "user",
            "content": "你好",
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": "msg_uuid2",
            "role": "assistant",
            "content": "您好！有什么可以帮您的吗？",
            "created_at": "2024-01-01T00:00:01Z",
            "metadata": {
                "intent": "闲聊"
            }
        }
    ],
    "total": 10
}
```

### 工单相关API

**POST /api/tickets**
```python
# 请求
{
    "title": "无法登录账户",
    "description": "尝试登录时提示密码错误，但密码确认无误",
    "priority": "high",
    "category": "账户问题"
}

# 响应
{
    "ticket_id": "ticket_uuid",
    "title": "无法登录账户",
    "status": "pending",
    "created_at": "2024-01-01T00:00:00Z",
    "estimated_response_time": "2小时内"
}
```

**GET /api/tickets/{ticket_id}**
```python
# 响应
{
    "id": "ticket_uuid",
    "title": "无法登录账户",
    "description": "...",
    "status": "in_progress",
    "priority": "high",
    "category": "账户问题",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:30:00Z",
    "history": [
        {
            "action": "status_change",
            "old_value": "pending",
            "new_value": "in_progress",
            "operator": "admin_user",
            "created_at": "2024-01-01T00:30:00Z"
        }
    ]
}
```

**GET /api/tickets**
```python
# 请求参数
?status=pending&limit=20

# 响应
{
    "tickets": [...],
    "total": 5
}
```

### 文件上传API

**POST /api/files/upload**
```python
# 请求（multipart/form-data）
file: <binary>
session_id: "session_uuid"
message_id: "msg_uuid"  # 可选

# 响应
{
    "file_id": "file_uuid",
    "file_name": "document.pdf",
    "file_size": 1024000,
    "file_type": "pdf",
    "upload_url": "/files/file_uuid"
}
```

**GET /api/files/{file_id}**
```python
# 响应
<binary file content>
Content-Type: application/pdf
Content-Disposition: attachment; filename="document.pdf"
```

### 管理后台API

**GET /api/admin/stats**
```python
# 响应
{
    "total_users": 1000,
    "total_sessions": 5000,
    "total_messages": 50000,
    "total_tickets": 200,
    "active_sessions": 25,
    "pending_tickets": 15
}
```

**POST /api/admin/knowledge/upload**
```python
# 请求（multipart/form-data）
file: <binary>
title: "产品手册"
category: "文档"
tags: ["产品", "使用指南"]

# 响应
{
    "document_id": "doc_uuid",
    "title": "产品手册",
    "status": "processing",
    "chunks_created": 0
}
```

**DELETE /api/admin/knowledge/{document_id}**
```python
# 响应
{
    "message": "文档已删除",
    "chunks_deleted": 25
}
```

**PUT /api/admin/config**
```python
# 请求
{
    "llm_temperature": 0.8,
    "llm_max_tokens": 2500,
    "retrieval_top_k": 5
}

# 响应
{
    "message": "配置已更新",
    "config": {...}
}
```

**GET /api/admin/conversations**
```python
# 请求参数
?user_id=user_uuid&keyword=产品&start_date=2024-01-01&limit=20

# 响应
{
    "conversations": [
        {
            "session_id": "session_uuid",
            "user_id": "user_uuid",
            "username": "user123",
            "message_count": 10,
            "created_at": "2024-01-01T00:00:00Z",
            "preview": "用户询问产品价格..."
        }
    ],
    "total": 100
}
```

### AI-商城集成API（新增）

**POST /api/ai/cart-suggestions**
```python
# 请求
{
    "cart_items": [
        {
            "product_id": "prod_123",
            "title": "毕业设计项目A",
            "price": 299.00,
            "quantity": 1
        }
    ],
    "total_amount": 299.00
}

# 响应
{
    "coupon_suggestion": {
        "type": "coupon",
        "title": "满300减50优惠券",
        "description": "再加1元即可使用此优惠券，节省50元",
        "action_data": {
            "coupon_code": "SAVE50",
            "min_amount": 300
        },
        "priority": 1
    },
    "bundle_recommendation": {
        "type": "bundle",
        "title": "搭配推荐：项目B",
        "description": "与项目A技术栈相似，一起购买更优惠",
        "action_url": "/products/prod_456",
        "action_data": {
            "product_id": "prod_456",
            "bundle_discount": 0.15
        },
        "priority": 2
    },
    "product_recommendations": [
        {
            "id": "prod_789",
            "title": "相关项目C",
            "price": 199.00,
            "reason": "基于您的浏览历史推荐"
        }
    ]
}
```

**POST /api/ai/product-questions**
```python
# 请求
{
    "product_id": "prod_123",
    "question": "这个项目适合我吗？"
}

# 响应
{
    "answer": "这个项目非常适合您！它使用Vue 3 + FastAPI技术栈...",
    "sources": [
        {
            "type": "product_info",
            "field": "description"
        }
    ],
    "quick_actions": [
        {
            "type": "add_to_cart",
            "label": "加入购物车",
            "product_id": "prod_123"
        },
        {
            "type": "view_demo",
            "label": "查看演示",
            "url": "/demo/prod_123"
        }
    ]
}
```

**POST /api/ai/proactive-trigger**
```python
# 请求
{
    "trigger_type": "page_dwell",  # page_dwell, scroll_bottom, cart_idle
    "page_context": {
        "page": "product_detail",
        "product_id": "prod_123",
        "time_on_page": 35
    }
}

# 响应
{
    "should_trigger": true,
    "message": "您已经浏览这个商品一会儿了，有什么疑问吗？我可以帮您解答！",
    "priority": "medium"
}
```

**POST /api/ai/sync-product**
```python
# 请求
{
    "product_id": "prod_123",
    "action": "create",  # create, update, delete
    "product_data": {
        "title": "Vue3 + FastAPI 毕业设计",
        "description": "完整的前后端分离项目...",
        "price": 299.00,
        "tech_stack": ["Vue3", "FastAPI", "MySQL"],
        "features": ["用户认证", "数据管理", "API接口"]
    }
}

# 响应
{
    "success": true,
    "message": "商品信息已同步到AI知识库",
    "indexed_chunks": 5
}
```


## 前端组件设计

### Vue 3组件架构

```
src/
├── components/
│   ├── chat/
│   │   ├── ChatWindow.vue          # 主对话窗口
│   │   ├── MessageList.vue         # 消息列表
│   │   ├── MessageItem.vue         # 单条消息
│   │   ├── InputBox.vue            # 输入框
│   │   ├── FileUpload.vue          # 文件上传
│   │   ├── TypingIndicator.vue     # 输入指示器
│   │   ├── GlobalAIAssistant.vue   # 全局AI助手（新增）
│   │   ├── ProductCard.vue         # 商品卡片（新增）
│   │   └── QuickActions.vue        # 快速操作按钮（新增）
│   ├── session/
│   │   ├── SessionList.vue         # 会话列表
│   │   └── SessionItem.vue         # 会话项
│   ├── ticket/
│   │   ├── TicketList.vue          # 工单列表
│   │   └── TicketDetail.vue        # 工单详情
│   ├── mall/
│   │   ├── AIConsultCard.vue       # AI咨询卡片（新增）
│   │   ├── AISuggestionsCard.vue   # AI建议卡片（新增）
│   │   └── MiniChat.vue            # 迷你聊天窗口（新增）
│   └── admin/
│       ├── Dashboard.vue           # 管理仪表板
│       ├── ConversationMonitor.vue # 对话监控
│       ├── KnowledgeManager.vue    # 知识库管理
│       └── ConfigPanel.vue         # 配置面板
├── composables/
│   ├── useAIProactive.ts           # 主动提示逻辑（新增）
│   └── usePageContext.ts           # 页面上下文收集（新增）
├── stores/
│   ├── auth.ts                     # 认证状态
│   ├── chat.ts                     # 对话状态
│   ├── session.ts                  # 会话状态
│   ├── config.ts                   # 配置状态
│   ├── product.ts                  # 商品状态（新增）
│   └── cart.ts                     # 购物车状态（新增）
├── services/
│   ├── api.ts                      # API客户端
│   ├── websocket.ts                # WebSocket连接
│   └── storage.ts                  # 本地存储
└── router/
    └── index.ts                    # 路由配置
```

### 核心组件设计

**1. ChatWindow.vue（主对话窗口）**
```vue
<template>
  <div class="chat-window">
    <SessionList @select="handleSessionSelect" />
    <div class="chat-main">
      <MessageList :messages="currentMessages" />
      <InputBox 
        @send="handleSendMessage"
        @upload="handleFileUpload"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
const currentMessages = computed(() => chatStore.currentSessionMessages)

const handleSendMessage = async (message: string) => {
  await chatStore.sendMessage(message)
}

const handleFileUpload = async (file: File) => {
  await chatStore.uploadFile(file)
}
</script>
```

**2. MessageList.vue（消息列表）**
```vue
<template>
  <div class="message-list" ref="listRef">
    <MessageItem
      v-for="msg in messages"
      :key="msg.id"
      :message="msg"
    />
    <TypingIndicator v-if="isTyping" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = defineProps<{
  messages: Message[]
}>()

const listRef = ref<HTMLElement>()
const isTyping = ref(false)

// 自动滚动到底部
watch(() => props.messages.length, async () => {
  await nextTick()
  listRef.value?.scrollTo({
    top: listRef.value.scrollHeight,
    behavior: 'smooth'
  })
})
</script>
```

**3. InputBox.vue（输入框）**
```vue
<template>
  <div class="input-box">
    <textarea
      v-model="message"
      @keydown.enter.exact.prevent="handleSend"
      placeholder="输入消息..."
      :disabled="isSending"
    />
    <div class="actions">
      <button @click="handleFileClick">
        <FileIcon />
      </button>
      <button @click="handleSend" :disabled="!canSend">
        <SendIcon />
      </button>
    </div>
    <input
      ref="fileInput"
      type="file"
      hidden
      @change="handleFileChange"
      accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const emit = defineEmits<{
  send: [message: string]
  upload: [file: File]
}>()

const message = ref('')
const isSending = ref(false)
const fileInput = ref<HTMLInputElement>()

const canSend = computed(() => 
  message.value.trim().length > 0 && !isSending.value
)

const handleSend = async () => {
  if (!canSend.value) return
  
  isSending.value = true
  try {
    emit('send', message.value)
    message.value = ''
  } finally {
    isSending.value = false
  }
}

const handleFileClick = () => {
  fileInput.value?.click()
}

const handleFileChange = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) {
    emit('upload', file)
  }
}
</script>
```

**4. GlobalAIAssistant.vue（全局AI助手）- 新增**
```vue
<template>
  <div class="ai-assistant-container">
    <!-- 浮动按钮 -->
    <button 
      v-if="!isOpen" 
      @click="toggleChat"
      class="ai-float-btn"
      :class="{ 'has-notification': hasNotification }"
    >
      <span class="ai-icon">🤖</span>
      <span v-if="hasNotification" class="notification-badge">{{ notificationCount }}</span>
    </button>

    <!-- 聊天窗口 -->
    <transition name="slide-up">
      <div v-if="isOpen" class="ai-chat-window">
        <!-- 头部 -->
        <div class="chat-header">
          <div class="header-left">
            <span class="ai-avatar">🤖</span>
            <div class="header-info">
              <h3>AI助手</h3>
              <p class="status">在线 · 随时为您服务</p>
            </div>
          </div>
          <div class="header-actions">
            <button @click="minimizeChat" class="icon-btn">➖</button>
            <button @click="closeChat" class="icon-btn">✖️</button>
          </div>
        </div>

        <!-- 上下文提示 -->
        <div v-if="currentContext" class="context-banner">
          <span class="context-icon">📍</span>
          <span class="context-text">{{ currentContext }}</span>
        </div>

        <!-- 消息区域 -->
        <div class="messages-area" ref="messagesArea">
          <div v-for="msg in messages" :key="msg.id" :class="['message', msg.role]">
            <div class="message-content">{{ msg.content }}</div>
            
            <!-- 商品卡片 -->
            <ProductCard 
              v-if="msg.products" 
              :products="msg.products"
              @add-to-cart="handleAddToCart"
              @view-detail="handleViewDetail"
            />
            
            <!-- 快速操作 -->
            <QuickActions 
              v-if="msg.quick_actions"
              :actions="msg.quick_actions"
              @action-click="handleQuickAction"
            />
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <input 
            v-model="userInput"
            @keyup.enter="sendMessage"
            placeholder="输入消息..."
            class="message-input"
          />
          <button @click="sendMessage" class="send-btn">发送</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useProductStore } from '@/stores/product'
import { useCartStore } from '@/stores/cart'
import { usePageContext } from '@/composables/usePageContext'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const productStore = useProductStore()
const cartStore = useCartStore()
const { getPageContext } = usePageContext()

const isOpen = ref(false)
const userInput = ref('')
const messages = ref([])
const hasNotification = ref(false)
const notificationCount = ref(0)

// 当前上下文
const currentContext = computed(() => {
  const routeName = route.name
  const params = route.params
  
  if (routeName === 'ProductDetail' && params.id) {
    const product = productStore.currentProduct
    return `正在查看：${product?.title || '商品详情'}`
  } else if (routeName === 'ProductList') {
    return '正在浏览商品列表'
  } else if (routeName === 'Cart') {
    return `购物车（${cartStore.items.length}件商品）`
  } else if (routeName === 'Orders') {
    return '我的订单'
  }
  
  return null
})

// 监听路由变化，自动发送上下文
watch(() => route.fullPath, (newPath, oldPath) => {
  if (isOpen.value && newPath !== oldPath) {
    sendContextUpdate()
  }
})

// 发送上下文更新
const sendContextUpdate = () => {
  const context = getPageContext()
  chatStore.updateContext(context)
}

// 切换聊天窗口
const toggleChat = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    sendContextUpdate()
    hasNotification.value = false
    notificationCount.value = 0
  }
}

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim()) return
  
  const message = userInput.value
  userInput.value = ''
  
  // 添加用户消息
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: message
  })
  
  // 发送到后端（带上下文）
  const context = getPageContext()
  const response = await chatStore.sendMessageWithContext(message, context)
  
  // 添加AI回复
  messages.value.push({
    id: Date.now() + 1,
    role: 'assistant',
    content: response.response,
    products: response.recommended_products,
    quick_actions: response.quick_actions
  })
}

// 处理加入购物车
const handleAddToCart = async (product: any) => {
  await cartStore.addItem(product.id, 1)
  
  // AI确认消息
  messages.value.push({
    id: Date.now(),
    role: 'assistant',
    content: `已将"${product.title}"加入购物车！您还需要其他帮助吗？`
  })
}

// 处理查看详情
const handleViewDetail = (product: any) => {
  router.push(`/products/${product.id}`)
  minimizeChat()
}

// 主动推送通知
const pushNotification = (message: string) => {
  if (!isOpen.value) {
    hasNotification.value = true
    notificationCount.value++
  }
  
  messages.value.push({
    id: Date.now(),
    role: 'assistant',
    content: message
  })
}

// 暴露给外部调用
defineExpose({
  pushNotification,
  openChat: () => { isOpen.value = true }
})
</script>
```

**5. AIConsultCard.vue（AI咨询卡片）- 新增**
```vue
<template>
  <div class="ai-consult-card">
    <div class="card-header">
      <span class="ai-icon">🤖</span>
      <h3>AI助手为您解答</h3>
    </div>
    
    <!-- 快速问题 -->
    <div class="quick-questions">
      <button 
        v-for="q in quickQuestions" 
        :key="q"
        @click="askQuestion(q)"
        class="quick-question-btn"
      >
        {{ q }}
      </button>
    </div>
    
    <!-- 迷你聊天 -->
    <MiniChat 
      v-if="showMiniChat"
      :messages="miniMessages"
      @send="sendMiniMessage"
    />
    
    <button @click="openFullChat" class="open-full-chat-btn">
      展开完整对话
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, inject } from 'vue'
import { useRoute } from 'vue-router'
import { useProductStore } from '@/stores/product'
import { useChatStore } from '@/stores/chat'

const route = useRoute()
const productStore = useProductStore()
const chatStore = useChatStore()
const aiAssistant = inject('aiAssistant')

const product = computed(() => productStore.currentProduct)

// 快速问题（根据商品动态生成）
const quickQuestions = computed(() => [
  '这个项目适合我吗？',
  '技术栈是什么？',
  '包含哪些功能？',
  '有演示视频吗？'
])

const showMiniChat = ref(false)
const miniMessages = ref([])

// 询问快速问题
const askQuestion = async (question: string) => {
  showMiniChat.value = true
  
  miniMessages.value.push({
    id: Date.now(),
    role: 'user',
    content: question
  })
  
  // 发送到AI（带商品上下文）
  const context = {
    page: 'product_detail',
    product_id: product.value.id,
    product_title: product.value.title,
    product_price: product.value.price,
    product_tech_stack: product.value.tech_stack
  }
  
  const response = await chatStore.sendMessageWithContext(question, context)
  
  miniMessages.value.push({
    id: Date.now() + 1,
    role: 'assistant',
    content: response.response
  })
}

// 打开完整聊天
const openFullChat = () => {
  aiAssistant.value?.openChat()
}
</script>
```

**6. AISuggestionsCard.vue（AI建议卡片）- 新增**
```vue
<template>
  <div class="ai-suggestions-card">
    <div class="card-header">
      <span class="ai-icon">💡</span>
      <h3>AI为您推荐</h3>
    </div>
    
    <!-- 优惠建议 -->
    <div v-if="couponSuggestion" class="suggestion-item">
      <span class="suggestion-icon">🎫</span>
      <div class="suggestion-content">
        <p class="suggestion-title">{{ couponSuggestion.title }}</p>
        <p class="suggestion-desc">{{ couponSuggestion.description }}</p>
      </div>
      <button @click="applyCoupon" class="apply-btn">应用</button>
    </div>
    
    <!-- 搭配推荐 -->
    <div v-if="bundleRecommendation" class="suggestion-item">
      <span class="suggestion-icon">📦</span>
      <div class="suggestion-content">
        <p class="suggestion-title">{{ bundleRecommendation.title }}</p>
        <p class="suggestion-desc">{{ bundleRecommendation.description }}</p>
      </div>
      <button @click="viewBundle" class="view-btn">查看</button>
    </div>
    
    <!-- 咨询按钮 -->
    <button @click="askAI" class="ask-ai-btn">
      <span>🤖</span>
      <span>有疑问？问问AI助手</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, inject } from 'vue'
import { useCartStore } from '@/stores/cart'
import { useChatStore } from '@/stores/chat'

const cartStore = useCartStore()
const chatStore = useChatStore()
const aiAssistant = inject('aiAssistant')

const couponSuggestion = ref(null)
const bundleRecommendation = ref(null)

// 获取AI建议
onMounted(async () => {
  const suggestions = await chatStore.getCartSuggestions({
    cart_items: cartStore.items,
    total_amount: cartStore.total
  })
  
  couponSuggestion.value = suggestions.coupon_suggestion
  bundleRecommendation.value = suggestions.bundle_recommendation
})

// 询问AI
const askAI = () => {
  aiAssistant.value?.openChat()
  aiAssistant.value?.pushNotification('我看到您的购物车有几件商品，有什么可以帮您的吗？')
}
</script>
```

### Composables（新增）

**usePageContext.ts（页面上下文收集）**
```typescript
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProductStore } from '@/stores/product'
import { useCartStore } from '@/stores/cart'

export function usePageContext() {
  const route = useRoute()
  const productStore = useProductStore()
  const cartStore = useCartStore()
  
  const getPageContext = () => {
    const context: any = {
      page: route.name as string
    }
    
    // 商品详情页
    if (route.name === 'ProductDetail') {
      const product = productStore.currentProduct
      if (product) {
        context.product_id = product.id
        context.product_title = product.title
        context.product_price = product.price
        context.product_description = product.description
        context.product_tech_stack = product.tech_stack
      }
    }
    
    // 购物车页面
    if (route.name === 'Cart') {
      context.cart_items = cartStore.items
      context.cart_total = cartStore.total
      context.cart_item_count = cartStore.items.length
    }
    
    // 订单页面
    if (route.name === 'Orders' && route.params.id) {
      context.order_id = route.params.id
    }
    
    // 商品列表页
    if (route.name === 'ProductList') {
      context.category = route.query.category
      context.search_query = route.query.q
    }
    
    return context
  }
  
  return {
    getPageContext
  }
}
```

**useAIProactive.ts（主动提示逻辑）**
```typescript
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

export function useAIProactive(aiAssistant: any) {
  const route = useRoute()
  let timeOnPage = 0
  let scrollDepth = 0
  let timer: any = null
  const triggeredEvents = new Set()

  // 监听用户行为
  onMounted(() => {
    // 页面停留时间
    timer = setInterval(() => {
      timeOnPage++
      checkTriggers()
    }, 1000)

    // 滚动深度
    window.addEventListener('scroll', handleScroll)
  })

  onUnmounted(() => {
    clearInterval(timer)
    window.removeEventListener('scroll', handleScroll)
  })

  const handleScroll = () => {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop
    const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight
    scrollDepth = (scrollTop / scrollHeight) * 100
    checkTriggers()
  }

  // 检查触发条件
  const checkTriggers = () => {
    // 商品详情页停留超过30秒
    if (route.name === 'ProductDetail' && timeOnPage === 30 && !triggeredEvents.has('product_30s')) {
      triggerAI('您已经浏览这个商品一会儿了，有什么疑问吗？我可以帮您解答！')
      triggeredEvents.add('product_30s')
    }

    // 滚动到页面底部
    if (scrollDepth > 90 && !triggeredEvents.has('scroll_bottom')) {
      triggerAI('看完了吗？有什么想了解的可以问我哦！')
      triggeredEvents.add('scroll_bottom')
    }

    // 购物车停留超过60秒未结算
    if (route.name === 'Cart' && timeOnPage === 60 && !triggeredEvents.has('cart_60s')) {
      triggerAI('需要帮您看看有没有可用的优惠券吗？')
      triggeredEvents.add('cart_60s')
    }
  }

  const triggerAI = (message: string) => {
    aiAssistant.value?.pushNotification(message)
  }

  return {
    timeOnPage: ref(timeOnPage),
    scrollDepth: ref(scrollDepth)
  }
}
```

### 状态管理（Pinia）

**chat.ts（对话状态）- 增强版**
```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/services/api'

export const useChatStore = defineStore('chat', () => {
  const currentSessionId = ref<string | null>(null)
  const sessions = ref<Session[]>([])
  const messages = ref<Map<string, Message[]>>(new Map())
  const currentContext = ref<any>(null)  // 新增：当前页面上下文
  
  const currentSessionMessages = computed(() => {
    if (!currentSessionId.value) return []
    return messages.value.get(currentSessionId.value) || []
  })
  
  // 更新上下文
  const updateContext = (context: any) => {
    currentContext.value = context
  }
  
  // 发送消息（带上下文）
  const sendMessageWithContext = async (content: string, context?: any) => {
    if (!currentSessionId.value) {
      await createSession()
    }
    
    // 添加用户消息
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      created_at: new Date().toISOString()
    }
    addMessage(currentSessionId.value!, userMessage)
    
    // 调用API（带上下文）
    const response = await apiClient.sendMessageWithContext({
      session_id: currentSessionId.value!,
      message: content,
      context: context || currentContext.value
    })
    
    // 添加AI回复
    const aiMessage: Message = {
      id: response.message_id,
      role: 'assistant',
      content: response.content,
      metadata: {
        sources: response.sources,
        intent: response.intent,
        recommended_products: response.recommended_products,
        quick_actions: response.quick_actions
      },
      created_at: new Date().toISOString()
    }
    addMessage(currentSessionId.value!, aiMessage)
    
    return response
  }
  
  // 原有的sendMessage方法（兼容性）
  const sendMessage = async (content: string) => {
    return sendMessageWithContext(content)
  }
  
  // 获取购物车建议
  const getCartSuggestions = async (cartData: any) => {
    const response = await apiClient.getCartSuggestions(cartData)
    return response
  }
  
  const streamMessage = async (content: string) => {
    if (!currentSessionId.value) {
      await createSession()
    }
    
    // 添加用户消息
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      created_at: new Date().toISOString()
    }
    addMessage(currentSessionId.value!, userMessage)
    
    // 创建AI消息占位符
    const aiMessageId = crypto.randomUUID()
    const aiMessage: Message = {
      id: aiMessageId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString()
    }
    addMessage(currentSessionId.value!, aiMessage)
    
    // 流式接收
    const stream = await apiClient.streamMessage({
      session_id: currentSessionId.value!,
      message: content,
      context: currentContext.value  // 新增：带上下文
    })
    
    for await (const chunk of stream) {
      if (chunk.type === 'content') {
        aiMessage.content += chunk.delta
        // 触发响应式更新
        messages.value = new Map(messages.value)
      }
    }
  }
  
  const createSession = async () => {
    const session = await apiClient.createSession()
    sessions.value.unshift(session)
    currentSessionId.value = session.id
    messages.value.set(session.id, [])
  }
  
  const loadSessions = async () => {
    const result = await apiClient.getSessions()
    sessions.value = result.sessions
  }
  
  const loadSessionMessages = async (sessionId: string) => {
    const result = await apiClient.getSessionMessages(sessionId)
    messages.value.set(sessionId, result.messages)
    currentSessionId.value = sessionId
  }
  
  const addMessage = (sessionId: string, message: Message) => {
    const sessionMessages = messages.value.get(sessionId) || []
    sessionMessages.push(message)
    messages.value.set(sessionId, sessionMessages)
  }
  
  return {
    currentSessionId,
    sessions,
    currentSessionMessages,
    currentContext,
    sendMessage,
    sendMessageWithContext,  // 新增
    getCartSuggestions,  // 新增
    updateContext,  // 新增
    streamMessage,
    createSession,
    loadSessions,
    loadSessionMessages
  }
})
```

### API客户端

**api.ts**
```typescript
import axios, { AxiosInstance } from 'axios'
import { useAuthStore } from '@/stores/auth'

class APIClient {
  private client: AxiosInstance
  
  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
      timeout: 30000
    })
    
    // 请求拦截器：添加认证令牌
    this.client.interceptors.request.use((config) => {
      const authStore = useAuthStore()
      if (authStore.token) {
        config.headers.Authorization = `Bearer ${authStore.token}`
      }
      return config
    })
    
    // 响应拦截器：处理错误
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          const authStore = useAuthStore()
          await authStore.logout()
        }
        return Promise.reject(error)
      }
    )
  }
  
  async login(username: string, password: string) {
    const response = await this.client.post('/api/auth/login', {
      username,
      password
    })
    return response.data
  }
  
  async sendMessage(data: { session_id: string; message: string }) {
    const response = await this.client.post('/api/chat/message', data)
    return response.data
  }
  
  // 新增：带上下文的消息发送
  async sendMessageWithContext(data: { session_id: string; message: string; context?: any }) {
    const response = await this.client.post('/api/chat/message', data)
    return response.data
  }
  
  // 新增：获取购物车AI建议
  async getCartSuggestions(cartData: any) {
    const response = await this.client.post('/api/ai/cart-suggestions', cartData)
    return response.data
  }
  
  async *streamMessage(data: { session_id: string; message: string; context?: any }) {
    const response = await fetch(
      `${this.client.defaults.baseURL}/api/chat/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${useAuthStore().token}`
        },
        body: JSON.stringify(data)
      }
    )
    
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader!.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          yield data
        }
      }
    }
  }
  
  async createSession(title?: string) {
    const response = await this.client.post('/api/chat/session', { title })
    return response.data
  }
  
  async getSessions(limit = 20, offset = 0) {
    const response = await this.client.get('/api/chat/sessions', {
      params: { limit, offset }
    })
    return response.data
  }
  
  async getSessionMessages(sessionId: string) {
    const response = await this.client.get(
      `/api/chat/session/${sessionId}/messages`
    )
    return response.data
  }
  
  async uploadFile(file: File, sessionId: string) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', sessionId)
    
    const response = await this.client.post('/api/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }
  
  async createTicket(data: TicketCreate) {
    const response = await this.client.post('/api/tickets', data)
    return response.data
  }
  
  async getTicket(ticketId: string) {
    const response = await this.client.get(`/api/tickets/${ticketId}`)
    return response.data
  }
}

export const apiClient = new APIClient()
```

## 技术实现细节

### 1. LangChain集成

**LLM配置**
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 初始化LLM
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7,
    max_tokens=2000,
    streaming=True
)

# 意图识别提示模板
intent_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个意图识别助手。分析用户消息并识别意图。"),
    ("user", "{message}")
])

# 问答提示模板
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个客服助手。基于提供的知识库内容回答用户问题。"),
    ("user", "问题：{question}\n\n知识库：{context}\n\n历史：{history}")
])
```

### 2. Chroma向量数据库集成

**初始化和索引**
```python
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# 初始化Chroma客户端
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# 初始化嵌入模型
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

# 创建知识库集合
knowledge_base = Chroma(
    client=chroma_client,
    collection_name="knowledge_base",
    embedding_function=embeddings
)

# 添加文档
def add_documents_to_kb(documents: List[str], metadatas: List[dict]):
    knowledge_base.add_texts(
        texts=documents,
        metadatas=metadatas
    )

# 检索文档
def retrieve_documents(query: str, top_k: int = 3):
    results = knowledge_base.similarity_search_with_score(
        query=query,
        k=top_k
    )
    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": score
        }
        for doc, score in results
    ]
```

### 3. MySQL数据库连接

**SQLAlchemy配置**
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# 数据库URL
DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/ai_customer_service"

# 创建引擎（使用连接池）
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # 连接前检查
    pool_recycle=3600    # 1小时回收连接
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# 依赖注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 4. Redis缓存集成

**Redis配置**
```python
import redis
from typing import Optional
import json

class RedisCache:
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
    
    def get_context(self, session_id: str) -> Optional[dict]:
        key = f"session:{session_id}:context"
        data = self.client.hgetall(key)
        if not data:
            return None
        
        return {
            "history": json.loads(data.get("history", "[]")),
            "user_profile": json.loads(data.get("user_profile", "{}")),
            "last_intent": data.get("last_intent")
        }
    
    def update_context(
        self,
        session_id: str,
        history: list,
        user_profile: dict,
        last_intent: str
    ):
        key = f"session:{session_id}:context"
        self.client.hset(key, mapping={
            "history": json.dumps(history),
            "user_profile": json.dumps(user_profile),
            "last_intent": last_intent
        })
        self.client.expire(key, 3600)  # 1小时过期
    
    def cache_token(self, token_hash: str, user_id: str, ttl: int = 86400):
        key = f"auth:token:{token_hash}"
        self.client.setex(key, ttl, user_id)
    
    def get_user_from_token(self, token_hash: str) -> Optional[str]:
        key = f"auth:token:{token_hash}"
        return self.client.get(key)
```

### 5. FastAPI应用结构

**主应用**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI(
    title="AI客服系统API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 路由注册
from routers import auth, chat, tickets, admin, files

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话"])
app.include_router(tickets.router, prefix="/api/tickets", tags=["工单"])
app.include_router(files.router, prefix="/api/files", tags=["文件"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 6. 流式响应实现

**Server-Sent Events**
```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import AsyncIterator

router = APIRouter()

@router.post("/stream")
async def stream_chat(request: ChatRequest):
    async def generate() -> AsyncIterator[str]:
        # 初始化状态
        yield f"data: {json.dumps({'type': 'start', 'message_id': message_id})}\n\n"
        
        # 流式生成回答
        async for chunk in conversation_engine.stream_response(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message
        ):
            yield f"data: {json.dumps({'type': 'content', 'delta': chunk})}\n\n"
        
        # 结束标记
        yield f"data: {json.dumps({'type': 'end', 'sources': sources})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```


## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性反思

在分析所有验收标准后，我识别出以下可以合并或简化的冗余属性：

**合并的属性：**
1. 需求1的1.2和1.3（有效/无效凭据）可以合并为一个认证属性
2. 需求2的2.2和2.3（图片和文件上传）可以合并为附件处理属性
3. 需求3的3.2、3.3、3.4（不同意图路由）可以合并为意图路由属性
4. 需求7的7.1和7.2（用户消息和AI回复持久化）可以合并为消息持久化属性
5. 需求9的9.4和4.6（来源引用）是重复的，合并为一个属性
6. 需求13的13.3和13.4（请求验证和错误响应）可以合并为API错误处理属性

**保留的独立属性：**
- 会话管理、上下文维护、工单处理等核心功能属性
- 性能相关属性（响应时间、并发处理）
- 安全相关属性（加密、权限控制）

### 核心属性列表

**属性1：认证令牌验证**
*对于任何*认证请求，如果提供有效凭据，系统应该返回有效的JWT令牌并创建会话；如果提供无效凭据，系统应该拒绝访问并返回错误
**验证需求：1.2, 1.3**

**属性2：会话关联**
*对于任何*已认证用户发起的对话，系统应该创建新会话并正确关联到该用户ID
**验证需求：1.4**

**属性3：会话超时处理**
*对于任何*超时的会话，当用户尝试使用该会话时，系统应该要求重新认证
**验证需求：1.5**

**属性4：用户身份维护**
*对于任何*已认证用户的请求，系统应该在整个请求处理过程中维护用户身份信息
**验证需求：1.6**

**属性5：多模态输入处理**
*对于任何*支持的文件类型（文本、图片、文档），系统应该接收、存储并提取相关信息
**验证需求：2.1, 2.2, 2.3**

**属性6：文件格式验证**
*对于任何*不支持的文件格式，系统应该拒绝上传并返回包含支持格式列表的错误消息
**验证需求：2.4**

**属性7：文件大小限制**
*对于任何*超过大小限制的文件，系统应该拒绝上传并提示大小限制
**验证需求：2.5**

**属性8：意图识别优先**
*对于任何*用户消息，LangGraph工作流应该首先执行意图识别步骤
**验证需求：3.1**

**属性9：意图路由正确性**
*对于任何*被识别的意图（问答、工单、产品咨询），LangGraph工作流应该路由到对应的处理流程
**验证需求：3.2, 3.3, 3.4**

**属性10：意图不明确处理**
*对于任何*置信度低于阈值的意图识别结果，系统应该请求用户澄清
**验证需求：3.5**

**属性11：上下文维护**
*对于任何*LangGraph工作流步骤，系统应该在状态中维护完整的对话上下文
**验证需求：3.6**

**属性12：知识库检索触发**
*对于任何*问答意图的消息，系统应该从知识库检索相关文档
**验证需求：4.1**

**属性13：检索结果使用**
*对于任何*成功检索到的文档，系统应该使用这些文档生成回答
**验证需求：4.2**

**属性14：未找到文档处理**
*对于任何*未找到相关文档的查询，系统应该明确告知用户无法找到相关信息
**验证需求：4.3**

**属性15：语义检索方法**
*对于任何*知识库查询，检索器应该使用向量相似度而非简单关键词匹配
**验证需求：4.4**

**属性16：检索数量保证**
*对于任何*知识库查询，如果存在相关文档，检索器应该返回至少3个最相关的文档片段
**验证需求：4.5**

**属性17：来源引用**
*对于任何*使用知识库内容生成的回答，系统应该标注信息来源
**验证需求：4.6, 9.4**

**属性18：对话历史维护**
*对于任何*会话中的多轮对话，系统应该维护完整的对话历史
**验证需求：5.1**

**属性19：上下文感知回答**
*对于任何*生成的回答，系统应该考虑之前的对话上下文
**验证需求：5.2**

**属性20：引用理解**
*对于任何*包含对之前内容引用的消息，系统应该正确理解引用关系
**验证需求：5.3**

**属性21：上下文容量**
*对于任何*会话，系统应该保留至少最近20轮对话的上下文
**验证需求：5.4**

**属性22：对话持久化**
*对于任何*会话结束事件，系统应该将完整对话历史持久化到数据库
**验证需求：5.5**

**属性23：工单创建唯一性**
*对于任何*工单创建请求，系统应该创建新工单并分配唯一的工单号
**验证需求：6.1**

**属性24：工单信息完整性**
*对于任何*创建的工单，系统应该记录用户信息、问题描述和对话上下文
**验证需求：6.2**

**属性25：工单创建响应**
*对于任何*成功创建的工单，系统应该返回工单号和预计处理时间
**验证需求：6.3**

**属性26：工单状态查询**
*对于任何*工单查询请求，系统应该返回当前状态和处理进度
**验证需求：6.4**

**属性27：工单状态变更记录**
*对于任何*工单状态变更，系统应该记录变更时间和操作者
**验证需求：6.6**

**属性28：消息即时持久化**
*对于任何*用户消息或AI回复，系统应该立即将其保存到数据库
**验证需求：7.1, 7.2**

**属性29：历史查询完整性**
*对于任何*用户的历史查询请求，系统应该返回该用户的所有历史会话
**验证需求：7.3**

**属性30：消息时间排序**
*对于任何*历史对话显示，系统应该按时间顺序排列消息
**验证需求：7.4**

**属性31：消息字段完整性**
*对于任何*保存的消息，应该包含时间戳、发送者、内容和会话ID
**验证需求：7.5**

**属性32：附件路径保存**
*对于任何*上传的文件或图片，系统应该保存其引用路径
**验证需求：7.6**

**属性33：管理员权限验证**
*对于任何*管理后台访问请求，系统应该验证用户具有管理员权限
**验证需求：8.1**

**属性34：对话记录访问**
*对于任何*管理员的对话记录查询，系统应该返回所有用户的对话记录
**验证需求：8.2**

**属性35：配置修改生效**
*对于任何*AI参数修改，系统应该保存配置并应用到后续对话
**验证需求：8.4**

**属性36：知识库文档索引**
*对于任何*上传的知识库文档，系统应该处理并索引该文档，使其可被检索
**验证需求：8.5**

**属性37：知识库文档删除**
*对于任何*删除的知识库文档，系统应该从索引中移除，使其无法被检索
**验证需求：8.6**

**属性38：统计信息准确性**
*对于任何*系统统计查询，返回的数据应该与数据库中的实际数据一致
**验证需求：8.7**

**属性39：搜索功能正确性**
*对于任何*带有搜索条件的对话记录查询，返回的结果应该匹配所有指定条件
**验证需求：8.8**

**属性40：回答生成依据**
*对于任何*生成的回答，应该基于检索到的知识库内容和对话上下文
**验证需求：9.1**

**属性41：流式响应时间**
*对于任何*回答生成请求，系统应该在200毫秒内开始流式返回响应
**验证需求：9.2**

**属性42：多要点格式化**
*对于任何*包含多个要点的回答，系统应该使用结构化格式（如列表）呈现
**验证需求：9.3**

**属性43：不确定性表达**
*对于任何*无法确定准确答案的情况，系统应该明确表示不确定性而非提供错误信息
**验证需求：9.5**

**属性44：参数配置使用**
*对于任何*回答生成，系统应该使用配置的AI模型参数（温度、最大token等）
**验证需求：9.6**

**属性45：产品信息检索**
*对于任何*产品相关查询（功能、价格、使用方法），系统应该从产品知识库检索信息
**验证需求：10.1, 10.2, 10.3**

**属性46：产品对比功能**
*对于任何*产品对比请求，系统应该提供多个产品的对比信息
**验证需求：10.4**

**属性47：产品库独立性**
*对于任何*产品查询，应该从独立的产品知识库检索，而非通用知识库
**验证需求：10.5**

**属性48：产品信息更新**
*对于任何*产品信息更新操作，后续查询应该返回更新后的信息
**验证需求：10.6**

**属性49：AI失败错误处理**
*对于任何*AI模型调用失败，系统应该返回友好的错误消息并记录错误日志
**验证需求：11.1**

**属性50：检索超时处理**
*对于任何*知识库检索操作，如果超过5秒未返回，系统应该返回超时提示
**验证需求：11.2**

**属性51：数据库重连机制**
*对于任何*数据库连接失败，系统应该尝试重连，并在3次失败后返回错误
**验证需求：11.3**

**属性52：恶意内容过滤**
*对于任何*包含恶意内容的用户输入，系统应该拒绝处理并记录安全日志
**验证需求：11.4**

**属性53：错误时会话保持**
*对于任何*系统错误，用户会话状态应该保持不丢失
**验证需求：11.5**

**属性54：错误日志完整性**
*对于任何*系统错误，日志应该包含时间戳、用户ID和错误详情
**验证需求：11.6**

**属性55：UI消息显示**
*对于任何*发送的消息，界面应该立即显示用户消息并显示"正在输入"指示器
**验证需求：12.3**

**属性56：流式内容显示**
*对于任何*AI回复，界面应该以流式方式逐步显示内容
**验证需求：12.4**

**属性57：上传进度显示**
*对于任何*文件上传操作，界面应该显示上传进度
**验证需求：12.5**

**属性58：响应式布局**
*对于任何*屏幕尺寸，用户界面应该保持响应式布局
**验证需求：12.7**

**属性59：连接状态提示**
*对于任何*网络连接中断，界面应该显示连接状态提示
**验证需求：12.8**

**属性60：API请求验证**
*对于任何*API请求，系统应该验证请求格式和认证令牌
**验证需求：13.3**

**属性61：API错误响应**
*对于任何*API处理失败，系统应该返回标准的HTTP错误码和错误消息
**验证需求：13.4**

**属性62：CORS支持**
*对于任何*跨域请求，系统应该返回正确的CORS头
**验证需求：13.6**

**属性63：流式响应支持**
*对于任何*对话API调用，系统应该支持流式响应（SSE或WebSocket）
**验证需求：13.7**

**属性64：并发处理能力**
*对于任何*并发请求场景，系统应该支持至少50个并发对话会话
**验证需求：14.1**

**属性65：检索性能**
*对于任何*知识库检索操作，应该在2秒内返回结果
**验证需求：14.2**

**属性66：异步处理**
*对于任何*AI模型调用，系统应该使用异步处理机制，不阻塞其他请求
**验证需求：14.3**

**属性67：配置参数生效**
*对于任何*并发限制和超时参数的配置修改，系统应该应用新配置
**验证需求：14.5**

**属性68：过载保护**
*对于任何*系统负载过高的情况，系统应该返回503状态码并提示稍后重试
**验证需求：14.6**

**属性69：密码哈希存储**
*对于任何*存储的用户密码，应该以哈希形式存储而非明文
**验证需求：15.2**

**属性70：数据删除完整性**
*对于任何*用户数据删除请求，系统应该从数据库中永久删除该用户的对话历史
**验证需求：15.4**

**属性71：权限访问控制**
*对于任何*管理员操作，系统应该限制只能访问授权的数据和功能
**验证需求：15.5**

**属性72：审计日志记录**
*对于任何*敏感操作，系统应该记录审计日志，包含用户ID、操作类型和时间戳
**验证需求：15.6**

**属性73：全局AI助手可访问性**
*对于任何*商城页面，全局AI助手浮动按钮应该始终可见且可点击
**验证需求：16.1, 16.2**

**属性74：页面上下文自动更新**
*对于任何*页面切换，AI助手应该自动更新并显示新的页面上下文信息
**验证需求：16.3, 16.4**

**属性75：通知徽章显示**
*对于任何*新的AI主动消息，如果聊天窗口未打开，浮动按钮应该显示通知徽章
**验证需求：16.5**

**属性76：对话状态保持**
*对于任何*聊天窗口最小化操作，系统应该保持对话历史和状态不丢失
**验证需求：16.7**

**属性77：商品上下文传递**
*对于任何*在商品详情页发送的消息，系统应该将商品ID、标题、价格等信息传递到后端
**验证需求：17.1, 17.5**

**属性78：购物车上下文传递**
*对于任何*在购物车页面发送的消息，系统应该将购物车商品列表和总金额传递到后端
**验证需求：17.2, 17.5**

**属性79：上下文感知回答生成**
*对于任何*带页面上下文的请求，AI生成的回答应该考虑并引用页面上下文信息
**验证需求：17.6**

**属性80：快速问题显示**
*对于任何*商品详情页，AI咨询卡片应该显示针对该商品的快速问题按钮
**验证需求：18.2**

**属性81：快速问题自动发送**
*对于任何*快速问题按钮点击，系统应该自动发送该问题到AI并显示回答
**验证需求：18.3**

**属性82：商品信息基础回答**
*对于任何*商品相关问题，AI回答应该基于该商品的详细信息生成
**验证需求：18.6**

**属性83：优惠券建议准确性**
*对于任何*购物车状态，如果存在可用优惠券，AI建议应该包含优惠券推荐
**验证需求：19.2**

**属性84：搭配商品推荐相关性**
*对于任何*购物车商品，AI推荐的搭配商品应该与购物车中的商品相关
**验证需求：19.3**

**属性85：优惠券自动应用**
*对于任何*优惠券应用操作，系统应该自动将优惠券应用到购物车
**验证需求：19.4**

**属性86：主动提示触发条件**
*对于任何*满足触发条件的用户行为（停留30秒、滚动到底部等），AI应该发送主动提示
**验证需求：20.1, 20.2, 20.3**

**属性87：主动提示非侵入性**
*对于任何*主动提示，应该以通知徽章形式显示，不打断用户当前操作
**验证需求：20.5**

**属性88：用户偏好记录**
*对于任何*用户关闭的主动提示，系统应该记录用户偏好，减少类似提示频率
**验证需求：20.6**

**属性89：商品卡片显示**
*对于任何*AI推荐的商品，聊天窗口应该显示商品卡片和操作按钮
**验证需求：21.1**

**属性90：加购操作执行**
*对于任何*聊天中的"加入购物车"操作，系统应该成功将商品添加到购物车
**验证需求：21.2**

**属性91：加购确认消息**
*对于任何*成功的加购操作，AI应该发送确认消息告知用户
**验证需求：21.3**

**属性92：页面跳转正确性**
*对于任何*聊天中的"查看详情"或"立即购买"操作，系统应该跳转到正确的页面
**验证需求：21.4, 21.5**

**属性93：PageContext字段完整性**
*对于任何*ChatRequest，如果包含PageContext，应该包含页面类型和相关上下文字段
**验证需求：22.1, 22.2**

**属性94：上下文驱动意图识别**
*对于任何*带页面上下文的请求，意图识别应该考虑页面上下文信息
**验证需求：22.3**

**属性95：上下文增强提示词**
*对于任何*回答生成，如果有页面上下文，应该将上下文信息加入LLM提示词
**验证需求：22.4**

**属性96：商品详情页优先检索**
*对于任何*在商品详情页的询问，系统应该优先从该商品信息中检索答案
**验证需求：22.5**

**属性97：商品信息自动同步**
*对于任何*新增或更新的商品，系统应该自动将商品信息同步到AI知识库
**验证需求：23.1, 23.2**

**属性98：下架商品移除**
*对于任何*下架的商品，系统应该从AI知识库中移除该商品信息
**验证需求：23.3**

**属性99：商品知识库字段完整性**
*对于任何*同步到知识库的商品，应该包含标题、描述、价格、技术栈、功能特性等信息
**验证需求：23.4**

**属性100：异步同步不阻塞**
*对于任何*商品同步操作，应该在后台异步执行，不影响商城的正常操作
**验证需求：23.6**


## 错误处理策略

### 错误分类

**1. 客户端错误（4xx）**
- 400 Bad Request：请求格式错误、参数缺失
- 401 Unauthorized：未认证或令牌无效
- 403 Forbidden：权限不足
- 404 Not Found：资源不存在
- 413 Payload Too Large：文件过大
- 422 Unprocessable Entity：业务逻辑验证失败
- 429 Too Many Requests：速率限制

**2. 服务器错误（5xx）**
- 500 Internal Server Error：未预期的服务器错误
- 502 Bad Gateway：上游服务（AI模型）错误
- 503 Service Unavailable：服务过载或维护中
- 504 Gateway Timeout：上游服务超时

### 错误响应格式

```python
{
    "error": {
        "code": "INVALID_INPUT",
        "message": "用户友好的错误消息",
        "details": {
            "field": "message",
            "reason": "消息内容不能为空"
        },
        "request_id": "req_uuid",
        "timestamp": "2024-01-01T00:00:00Z"
    }
}
```

### 错误处理实现

**1. 全局异常处理器**
```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求参数验证失败",
                "details": exc.errors(),
                "request_id": request.state.request_id
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误，请稍后重试",
                "request_id": request.state.request_id
            }
        }
    )
```

**2. 自定义异常类**
```python
class AIServiceException(Exception):
    """AI服务异常基类"""
    def __init__(self, message: str, code: str = "AI_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class KnowledgeBaseException(Exception):
    """知识库异常"""
    pass

class AuthenticationException(Exception):
    """认证异常"""
    pass

class RateLimitException(Exception):
    """速率限制异常"""
    pass
```

**3. 重试机制**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def call_ai_model_with_retry(prompt: str):
    """带重试的AI模型调用"""
    try:
        return await llm.ainvoke(prompt)
    except Exception as e:
        logger.warning(f"AI model call failed: {e}")
        raise
```

**4. 超时处理**
```python
import asyncio

async def retrieve_with_timeout(query: str, timeout: float = 5.0):
    """带超时的知识库检索"""
    try:
        return await asyncio.wait_for(
            knowledge_retriever.retrieve(query),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"Knowledge retrieval timeout for query: {query}")
        raise KnowledgeBaseException("知识库检索超时，请稍后重试")
```

**5. 断路器模式**
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_external_service(url: str):
    """带断路器的外部服务调用"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

### 日志记录

**日志级别和内容**
```python
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 请求日志
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    logger.info(f"Request {request_id}: {request.method} {request.url}")
    
    start_time = datetime.now()
    response = await call_next(request)
    duration = (datetime.now() - start_time).total_seconds()
    
    logger.info(
        f"Request {request_id} completed: "
        f"status={response.status_code} duration={duration}s"
    )
    
    return response

# 错误日志
def log_error(error: Exception, context: dict):
    logger.error(
        f"Error occurred: {type(error).__name__}: {str(error)}",
        extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        },
        exc_info=True
    )

# 审计日志
def log_audit(user_id: str, action: str, resource: str, details: dict):
    logger.info(
        f"Audit: user={user_id} action={action} resource={resource}",
        extra={
            "audit": True,
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
    )
```

## 测试策略

### 测试方法论

本系统采用**双重测试方法**：
1. **单元测试**：验证特定示例、边界情况和错误条件
2. **基于属性的测试**：验证跨所有输入的通用属性

这两种方法是互补的：
- 单元测试捕获具体的错误和已知的边界情况
- 基于属性的测试通过随机化验证通用正确性

### 基于属性的测试配置

**测试库选择：**
- Python后端：**Hypothesis**
- TypeScript前端：**fast-check**

**配置要求：**
- 每个属性测试最少运行**100次迭代**
- 每个测试必须引用设计文档中的属性
- 标签格式：`# Feature: ai-customer-service, Property N: [属性文本]`

### 测试覆盖范围

**1. 单元测试（Pytest）**

```python
# tests/test_auth_service.py
import pytest
from services.auth import AuthService

class TestAuthService:
    def test_login_with_valid_credentials(self):
        """测试有效凭据登录"""
        auth_service = AuthService()
        token = auth_service.login("user123", "password123")
        assert token is not None
        assert token.access_token
        assert token.token_type == "bearer"
    
    def test_login_with_invalid_credentials(self):
        """测试无效凭据登录"""
        auth_service = AuthService()
        with pytest.raises(AuthenticationException):
            auth_service.login("user123", "wrong_password")
    
    def test_token_expiration(self):
        """测试令牌过期"""
        auth_service = AuthService()
        # 创建过期令牌
        expired_token = create_expired_token()
        with pytest.raises(AuthenticationException):
            auth_service.verify_token(expired_token)
```

**2. 基于属性的测试（Hypothesis）**

```python
# tests/property_tests/test_auth_properties.py
from hypothesis import given, strategies as st
from services.auth import AuthService

# Feature: ai-customer-service, Property 1: 认证令牌验证
@given(
    username=st.text(min_size=1, max_size=50),
    password=st.text(min_size=8, max_size=100)
)
def test_property_authentication_token_validation(username, password):
    """
    属性1：对于任何有效凭据，系统应该返回有效的JWT令牌
    """
    auth_service = AuthService()
    
    # 先注册用户
    auth_service.register(username, password)
    
    # 登录应该成功
    token = auth_service.login(username, password)
    
    # 验证令牌有效
    assert token is not None
    assert token.access_token
    
    # 验证令牌可以被解析
    user = auth_service.verify_token(token.access_token)
    assert user.username == username

# Feature: ai-customer-service, Property 2: 会话关联
@given(
    user_id=st.uuids(),
    message=st.text(min_size=1, max_size=1000)
)
def test_property_session_association(user_id, message):
    """
    属性2：对于任何已认证用户发起的对话，系统应该创建新会话并关联到该用户
    """
    conversation_engine = ConversationEngine()
    
    # 发起对话
    response = conversation_engine.process_message(
        user_id=str(user_id),
        session_id=None,  # 新会话
        message=message
    )
    
    # 验证会话被创建
    assert response.session_id is not None
    
    # 验证会话关联到用户
    session = session_service.get_session(response.session_id)
    assert session.user_id == str(user_id)
```

**3. 集成测试**

```python
# tests/integration/test_conversation_flow.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_complete_conversation_flow():
    """测试完整对话流程"""
    # 1. 登录
    login_response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpass"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 创建会话
    session_response = client.post(
        "/api/chat/session",
        headers=headers,
        json={"title": "测试对话"}
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["session_id"]
    
    # 3. 发送消息
    message_response = client.post(
        "/api/chat/message",
        headers=headers,
        json={
            "session_id": session_id,
            "message": "如何重置密码？"
        }
    )
    assert message_response.status_code == 200
    assert "message_id" in message_response.json()
    assert "content" in message_response.json()
    
    # 4. 查询历史
    history_response = client.get(
        f"/api/chat/session/{session_id}/messages",
        headers=headers
    )
    assert history_response.status_code == 200
    messages = history_response.json()["messages"]
    assert len(messages) >= 2  # 用户消息 + AI回复
```

**4. 前端测试（Vitest + fast-check）**

```typescript
// tests/unit/ChatStore.spec.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'
import * as fc from 'fast-check'

describe('ChatStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })
  
  it('should add message to current session', () => {
    const store = useChatStore()
    store.currentSessionId = 'session-1'
    
    const message = {
      id: 'msg-1',
      role: 'user',
      content: 'Hello',
      created_at: new Date().toISOString()
    }
    
    store.addMessage('session-1', message)
    
    expect(store.currentSessionMessages).toHaveLength(1)
    expect(store.currentSessionMessages[0]).toEqual(message)
  })
  
  // Feature: ai-customer-service, Property 30: 消息时间排序
  it('property: messages should be sorted by timestamp', () => {
    fc.assert(
      fc.property(
        fc.array(fc.record({
          id: fc.uuid(),
          role: fc.constantFrom('user', 'assistant'),
          content: fc.string(),
          created_at: fc.date().map(d => d.toISOString())
        }), { minLength: 2, maxLength: 20 }),
        (messages) => {
          const store = useChatStore()
          const sessionId = 'test-session'
          store.currentSessionId = sessionId
          
          // 随机顺序添加消息
          const shuffled = [...messages].sort(() => Math.random() - 0.5)
          shuffled.forEach(msg => store.addMessage(sessionId, msg))
          
          // 获取消息
          const retrieved = store.currentSessionMessages
          
          // 验证按时间排序
          for (let i = 1; i < retrieved.length; i++) {
            const prev = new Date(retrieved[i - 1].created_at)
            const curr = new Date(retrieved[i].created_at)
            expect(prev.getTime()).toBeLessThanOrEqual(curr.getTime())
          }
        }
      ),
      { numRuns: 100 }
    )
  })
})
```

### 测试数据生成

**Hypothesis策略示例**
```python
from hypothesis import strategies as st

# 用户策略
user_strategy = st.builds(
    User,
    id=st.uuids().map(str),
    username=st.text(min_size=3, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        min_codepoint=ord('a'),
        max_codepoint=ord('z')
    )),
    email=st.emails(),
    role=st.sampled_from(['user', 'admin'])
)

# 消息策略
message_strategy = st.builds(
    Message,
    id=st.uuids().map(str),
    session_id=st.uuids().map(str),
    role=st.sampled_from(['user', 'assistant', 'system']),
    content=st.text(min_size=1, max_size=2000),
    created_at=st.datetimes().map(lambda dt: dt.isoformat())
)

# 工单策略
ticket_strategy = st.builds(
    Ticket,
    id=st.uuids().map(str),
    user_id=st.uuids().map(str),
    title=st.text(min_size=5, max_size=200),
    description=st.text(min_size=10, max_size=2000),
    status=st.sampled_from(['pending', 'in_progress', 'resolved', 'closed']),
    priority=st.sampled_from(['low', 'medium', 'high', 'urgent'])
)
```

### 性能测试

**负载测试（Locust）**
```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class ChatUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """登录并创建会话"""
        response = self.client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        response = self.client.post(
            "/api/chat/session",
            headers=self.headers
        )
        self.session_id = response.json()["session_id"]
    
    @task(3)
    def send_message(self):
        """发送消息（高频任务）"""
        self.client.post(
            "/api/chat/message",
            headers=self.headers,
            json={
                "session_id": self.session_id,
                "message": "测试消息"
            }
        )
    
    @task(1)
    def get_history(self):
        """查询历史（低频任务）"""
        self.client.get(
            f"/api/chat/session/{self.session_id}/messages",
            headers=self.headers
        )
```

### 测试执行

**运行所有测试**
```bash
# 后端测试
pytest tests/ -v --cov=. --cov-report=html

# 基于属性的测试
pytest tests/property_tests/ -v --hypothesis-show-statistics

# 前端测试
npm run test:unit

# 集成测试
pytest tests/integration/ -v

# 性能测试
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### 持续集成

**GitHub Actions配置**
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: testpass
          MYSQL_DATABASE: test_db
        ports:
          - 3306:3306
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov hypothesis
      
      - name: Run tests
        run: |
          pytest tests/ -v --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## 部署架构

### 开发环境

```
Docker Compose配置：
- FastAPI后端容器
- Vue前端开发服务器
- MySQL容器
- Redis容器
- Chroma容器
```

### 生产环境

```
- 负载均衡器（Nginx）
- FastAPI应用服务器（多实例）
- MySQL主从复制
- Redis集群
- Chroma向量数据库
- 文件存储（S3或MinIO）
- 监控（Prometheus + Grafana）
- 日志聚合（ELK Stack）
```

### 扩展性考虑

1. **水平扩展**：FastAPI应用无状态，可通过增加实例扩展
2. **数据库读写分离**：MySQL主从复制，读操作分流到从库
3. **缓存策略**：Redis缓存热点数据，减少数据库压力
4. **异步任务**：使用Celery处理耗时任务（文档索引、邮件发送）
5. **CDN**：静态资源通过CDN分发

---

## 总结

本设计文档详细描述了AI客服系统的架构、组件、数据模型和实现细节。系统采用现代化的技术栈，结合LangChain和LangGraph构建智能对话工作流，提供完整的前后端解决方案。

**核心特性：**
- 基于LangGraph的智能对话工作流
- 多模态输入支持（文本、图片、文件）
- 知识库集成与语义检索
- 工单管理系统
- 完整的管理后台
- 高性能和可扩展性设计
- 全面的测试策略

**下一步：**
根据本设计文档创建详细的任务列表，指导实际开发工作。
