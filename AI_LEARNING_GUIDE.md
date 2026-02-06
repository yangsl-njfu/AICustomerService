# AI客服系统 - AI核心脚本学习指南

本指南将帮助你理解系统中所有与AI相关的核心代码，适合学习LangChain和LangGraph。

## 📚 目录

1. [核心AI文件概览](#核心ai文件概览)
2. [LangGraph工作流详解](#langgraph工作流详解)
3. [知识检索系统](#知识检索系统)
4. [提示词工程](#提示词工程)
5. [学习路径](#学习路径)

---

## 核心AI文件概览

### 🎯 最重要的AI文件（必学）

| 文件 | 作用 | 难度 | 学习重点 |
|------|------|------|----------|
| `backend/services/langgraph_workflow.py` | LangGraph对话工作流 | ⭐⭐⭐⭐⭐ | 状态机、节点、路由 |
| `backend/services/knowledge_retriever.py` | 向量检索 | ⭐⭐⭐⭐ | Chroma、Embeddings |
| `backend/services/redis_cache.py` | 上下文管理 | ⭐⭐⭐ | 对话历史缓存 |

### 📋 辅助AI文件

| 文件 | 作用 |
|------|------|
| `backend/config.py` | AI模型配置（温度、token等） |
| `backend/api/chat.py` | AI对话API接口 |

---

## LangGraph工作流详解

### 文件位置
`backend/services/langgraph_workflow.py`

### 核心概念

#### 1. 状态定义（ConversationState）
```python
class ConversationState(TypedDict):
    # 输入
    user_message: str          # 用户消息
    user_id: str              # 用户ID
    session_id: str           # 会话ID
    
    # 上下文
    conversation_history: List[Dict[str, str]]  # 对话历史
    
    # 处理过程
    intent: Optional[str]      # 识别的意图
    confidence: Optional[float] # 置信度
    
    # 输出
    response: str             # AI回复
    sources: Optional[List[Dict]]  # 知识来源
```

**学习要点：**
- TypedDict定义了工作流中传递的数据结构
- 状态在节点间传递和更新
- 这是LangGraph的核心概念



#### 2. 工作流图构建
```python
def _build_graph(self):
    workflow = StateGraph(ConversationState)
    
    # 添加节点
    workflow.add_node("load_context", self.load_context_node)
    workflow.add_node("intent_recognition", self.intent_recognition_node)
    workflow.add_node("qa_flow", self.qa_flow_node)
    
    # 设置入口
    workflow.set_entry_point("load_context")
    
    # 添加边（节点连接）
    workflow.add_edge("load_context", "intent_recognition")
    
    # 条件路由
    workflow.add_conditional_edges(
        "intent_recognition",
        self.route_decision,
        {
            "qa_flow": "qa_flow",
            "ticket_flow": "ticket_flow",
            "product_flow": "product_flow"
        }
    )
    
    return workflow.compile()
```

**学习要点：**
- `StateGraph`：创建状态图
- `add_node`：添加处理节点
- `add_edge`：添加固定连接
- `add_conditional_edges`：添加条件路由（根据状态决定下一步）
- `compile()`：编译成可执行的图

#### 3. 核心节点详解

##### 节点1：意图识别（intent_recognition_node）
```python
async def intent_recognition_node(self, state: ConversationState):
    # 构建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是意图识别助手..."),
        ("human", "用户消息：{message}\n历史：{history}")
    ])
    
    # 调用LLM
    response = await self.llm.ainvoke(prompt.format_messages(...))
    
    # 解析结果
    result = json.loads(response.content)
    state["intent"] = result.get("intent")
    state["confidence"] = result.get("confidence")
    
    return state
```

**学习要点：**
- `ChatPromptTemplate`：构建对话提示词模板
- `llm.ainvoke()`：异步调用LLM
- 节点接收state，处理后返回更新的state

##### 节点2：问答流程（qa_flow_node）
```python
async def qa_flow_node(self, state: ConversationState):
    # 1. 检索相关文档
    docs = await knowledge_retriever.retrieve(
        query=state["user_message"],
        top_k=3
    )
    
    # 2. 构建提示词（包含检索到的文档）
    docs_text = "\n\n".join([doc.page_content for doc in docs])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "基于知识库回答问题..."),
        ("human", "知识库：{docs}\n问题：{question}")
    ])
    
    # 3. 生成回答
    response = await self.llm.ainvoke(prompt.format_messages(...))
    
    state["response"] = response.content
    state["sources"] = [doc.metadata for doc in docs]
    
    return state
```

**学习要点：**
- RAG模式：检索（Retrieve）→ 增强（Augment）→ 生成（Generate）
- 先从向量数据库检索相关文档
- 将文档作为上下文传给LLM
- 这是知识库问答的标准流程

##### 节点3：路由决策（route_decision）
```python
def route_decision(self, state: ConversationState) -> str:
    # 根据置信度和意图决定路由
    if state["confidence"] < 0.6:
        return "clarify"  # 意图不明确，请求澄清
    
    intent_map = {
        "问答": "qa_flow",
        "工单": "ticket_flow",
        "产品咨询": "product_flow"
    }
    return intent_map.get(state["intent"], "clarify")
```

**学习要点：**
- 条件路由函数返回下一个节点的名称
- 可以根据state中的任何字段做决策
- 这是LangGraph实现复杂逻辑的关键



---

## 知识检索系统

### 文件位置
`backend/services/knowledge_retriever.py`

### 核心概念

#### 1. 初始化Chroma和Embeddings
```python
class KnowledgeRetriever:
    def __init__(self):
        # 初始化Chroma客户端
        self.client = chromadb.Client(Settings(
            persist_directory="./data/chroma"
        ))
        
        # 初始化嵌入模型（将文本转为向量）
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # 创建集合
        self.knowledge_collection = self._get_or_create_collection("knowledge_base")
```

**学习要点：**
- Chroma：开源向量数据库
- Embeddings：将文本转换为向量（数字表示）
- 向量可以计算相似度，实现语义搜索

#### 2. 添加文档到向量库
```python
async def add_documents(self, documents: List[Dict]):
    texts = [doc["content"] for doc in documents]
    
    # 生成嵌入向量
    embeddings = self.embeddings.embed_documents(texts)
    
    # 添加到Chroma
    collection.add(
        ids=doc_ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )
```

**学习要点：**
- `embed_documents()`：批量将文本转为向量
- 向量和原文本一起存储
- metadata存储额外信息（标题、分类等）

#### 3. 语义检索
```python
async def retrieve(self, query: str, top_k: int = 3):
    # 1. 将查询转为向量
    query_embedding = self.embeddings.embed_query(query)
    
    # 2. 在向量库中搜索最相似的文档
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    # 3. 转换为Document对象
    documents = []
    for i, doc_text in enumerate(results['documents'][0]):
        documents.append(Document(
            page_content=doc_text,
            metadata=results['metadatas'][0][i]
        ))
    
    return documents
```

**学习要点：**
- 查询也要转为向量
- 通过向量相似度找到最相关的文档
- 这就是"语义搜索"：理解意思而非关键词匹配



---

## 提示词工程

### 关键提示词模板

#### 1. 意图识别提示词
```python
prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个意图识别助手。分析用户消息并识别其意图。
可能的意图：
- 问答：用户询问问题，需要从知识库检索答案
- 工单：用户需要创建工单或查询工单状态
- 产品咨询：用户询问产品信息、价格、功能等
- 闲聊：一般性对话

返回JSON格式：{"intent": "意图类型", "confidence": 0.0-1.0}"""),
    ("human", "用户消息：{message}\n历史对话：{history}\n请识别意图：")
])
```

**学习要点：**
- system消息：定义AI的角色和任务
- human消息：用户输入和上下文
- 明确输出格式（JSON）便于解析
- 提供示例和选项帮助AI理解

#### 2. 知识库问答提示词
```python
prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的AI客服助手。基于提供的知识库内容回答用户问题。
要求：
1. 回答要准确、简洁、有帮助
2. 如果知识库中没有相关信息，明确告知用户
3. 引用知识库来源
4. 保持友好专业的语气"""),
    ("human", """知识库内容：
{docs}

历史对话：
{history}

用户问题：{question}

请回答：""")
])
```

**学习要点：**
- 明确要求AI基于提供的知识库回答
- 包含历史对话提供上下文
- 设定回答的质量标准
- 这是RAG（检索增强生成）的标准提示词结构

#### 3. 工单信息提取提示词
```python
prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个工单处理助手。从用户消息中提取工单信息。
返回JSON格式：
{
    "title": "工单标题",
    "description": "问题描述",
    "priority": "low/medium/high/urgent",
    "category": "问题类别"
}"""),
    ("human", "用户消息：{message}\n历史对话：{history}\n请提取工单信息：")
])
```

**学习要点：**
- 结构化信息提取
- 明确JSON schema
- 从非结构化文本中提取结构化数据



---

## 上下文管理

### 文件位置
`backend/services/redis_cache.py`

### 核心功能

#### 1. 保存对话上下文
```python
async def update_context(
    self,
    session_id: str,
    history: List[Dict]
):
    key = f"session:{session_id}:context"
    
    # 只保留最近N轮对话
    max_history = 20
    data = {
        "history": json.dumps(history[-max_history:])
    }
    
    # 存储到Redis，1小时过期
    await self.redis_client.hset(key, mapping=data)
    await self.redis_client.expire(key, 3600)
```

**学习要点：**
- 对话历史存储在Redis（快速访问）
- 限制历史长度避免token超限
- 设置过期时间节省资源

#### 2. 添加消息到上下文
```python
async def add_message_to_context(
    self,
    session_id: str,
    user_message: str,
    assistant_message: str
):
    context = await self.get_context(session_id)
    history = context.get("history", []) if context else []
    
    # 添加新的对话轮次
    history.append({
        "user": user_message,
        "assistant": assistant_message
    })
    
    await self.update_context(session_id, history=history)
```

**学习要点：**
- 每轮对话包含用户消息和AI回复
- 累积的历史用于多轮对话理解
- 这是实现"记忆"的关键



---

## 学习路径

### 🎓 初级（1-2周）

#### 第1步：理解基础概念
1. **LLM基础**
   - 什么是大语言模型
   - Token的概念
   - 温度（temperature）参数的作用
   
2. **提示词工程**
   - 阅读 `langgraph_workflow.py` 中的所有提示词
   - 尝试修改提示词，观察输出变化
   - 学习system/human消息的区别

#### 第2步：运行和测试
```bash
# 启动系统
cd backend
python main.py

# 测试不同的对话
# 1. 问答："如何重置密码？"
# 2. 工单："我的账户无法登录"
# 3. 产品咨询："你们有哪些产品？"
```

**练习：**
- 修改意图识别的提示词
- 添加新的意图类型（如"投诉"）
- 观察AI如何响应

### 🎓 中级（2-4周）

#### 第3步：深入LangGraph
1. **学习StateGraph**
   - 阅读 `_build_graph()` 方法
   - 理解节点、边、条件路由
   - 画出工作流程图

2. **实践：添加新节点**
```python
# 在 langgraph_workflow.py 中添加
async def complaint_flow_node(self, state: ConversationState):
    """投诉处理流程"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是投诉处理专员..."),
        ("human", "投诉内容：{message}")
    ])
    
    response = await self.llm.ainvoke(prompt.format_messages(...))
    state["response"] = response.content
    return state

# 在 _build_graph() 中注册
workflow.add_node("complaint_flow", self.complaint_flow_node)

# 在 route_decision() 中添加路由
intent_map = {
    "问答": "qa_flow",
    "工单": "ticket_flow",
    "投诉": "complaint_flow"  # 新增
}
```

#### 第4步：向量检索实践
1. **添加测试文档**
```python
# 创建测试脚本 test_knowledge.py
from services.knowledge_retriever import knowledge_retriever

# 添加文档
documents = [{
    "content": "密码重置步骤：1. 点击忘记密码 2. 输入邮箱 3. 查收邮件",
    "metadata": {"title": "密码重置指南", "category": "账户"}
}]

await knowledge_retriever.add_documents(documents)

# 测试检索
results = await knowledge_retriever.retrieve("如何重置密码")
print(results)
```

2. **理解向量相似度**
   - 尝试不同的查询语句
   - 观察相似度分数
   - 理解语义搜索vs关键词搜索

### 🎓 高级（4-8周）

#### 第5步：优化工作流
1. **添加循环和条件**
```python
# 实现多轮澄清
async def clarify_loop_node(self, state: ConversationState):
    if state.get("clarify_count", 0) < 3:
        state["clarify_count"] = state.get("clarify_count", 0) + 1
        return state
    else:
        # 澄清次数过多，转人工
        state["response"] = "我将为您转接人工客服"
        return state

# 添加循环边
workflow.add_conditional_edges(
    "clarify",
    lambda s: "clarify_loop" if s.get("clarify_count", 0) < 3 else END,
    {"clarify_loop": "intent_recognition"}
)
```

2. **实现流式输出**
   - 研究 `api/chat.py` 中的 `stream_message`
   - 理解Server-Sent Events
   - 实现真正的流式LLM调用

#### 第6步：高级RAG技术
1. **混合检索**
   - 向量检索 + 关键词检索
   - 重排序（Reranking）
   
2. **文档分块策略**
   - 固定大小分块
   - 语义分块
   - 重叠分块

3. **多查询检索**
   - 生成多个查询变体
   - 合并检索结果



---

## 实战练习项目

### 练习1：添加情感分析
**目标：** 识别用户情绪，对负面情绪特殊处理

```python
# 在 langgraph_workflow.py 添加
async def sentiment_analysis_node(self, state: ConversationState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "分析用户情绪，返回：positive/neutral/negative"),
        ("human", "{message}")
    ])
    
    response = await self.llm.ainvoke(prompt.format_messages(
        message=state["user_message"]
    ))
    
    state["sentiment"] = response.content.strip()
    return state

# 在路由中使用
def route_decision(self, state: ConversationState) -> str:
    if state.get("sentiment") == "negative":
        return "priority_support"  # 负面情绪优先处理
    # ... 其他逻辑
```

### 练习2：实现对话摘要
**目标：** 当对话历史过长时，自动生成摘要

```python
async def summarize_context_node(self, state: ConversationState):
    if len(state["conversation_history"]) > 10:
        history_text = "\n".join([
            f"用户：{turn['user']}\n助手：{turn['assistant']}"
            for turn in state["conversation_history"]
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "总结以下对话的关键信息"),
            ("human", "{history}")
        ])
        
        summary = await self.llm.ainvoke(prompt.format_messages(
            history=history_text
        ))
        
        # 用摘要替换历史
        state["conversation_history"] = [{
            "user": "对话摘要",
            "assistant": summary.content
        }]
    
    return state
```

### 练习3：多语言支持
**目标：** 自动检测语言并用相应语言回复

```python
async def language_detection_node(self, state: ConversationState):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "检测语言，返回：zh/en/ja等"),
        ("human", "{message}")
    ])
    
    response = await self.llm.ainvoke(prompt.format_messages(
        message=state["user_message"]
    ))
    
    state["language"] = response.content.strip()
    return state

# 在回答时使用检测到的语言
async def qa_flow_node(self, state: ConversationState):
    language_instruction = {
        "zh": "用中文回答",
        "en": "Answer in English",
        "ja": "日本語で答えてください"
    }.get(state.get("language", "zh"), "用中文回答")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"你是AI客服。{language_instruction}"),
        ("human", "...")
    ])
    # ...
```



---

## 调试技巧

### 1. 打印状态变化
```python
async def debug_node(self, state: ConversationState):
    print("=" * 50)
    print(f"当前节点: {state.get('current_node')}")
    print(f"意图: {state.get('intent')}")
    print(f"置信度: {state.get('confidence')}")
    print(f"历史长度: {len(state.get('conversation_history', []))}")
    print("=" * 50)
    return state

# 在关键位置添加
workflow.add_node("debug", self.debug_node)
workflow.add_edge("intent_recognition", "debug")
workflow.add_edge("debug", "qa_flow")
```

### 2. 查看LLM原始输出
```python
response = await self.llm.ainvoke(prompt.format_messages(...))
print(f"LLM原始输出: {response.content}")  # 添加这行
result = json.loads(response.content)
```

### 3. 测试单个节点
```python
# 创建测试脚本 test_nodes.py
from services.langgraph_workflow import langgraph_workflow

# 构造测试状态
test_state = {
    "user_message": "如何重置密码？",
    "user_id": "test_user",
    "session_id": "test_session",
    "conversation_history": []
}

# 测试单个节点
result = await langgraph_workflow.intent_recognition_node(test_state)
print(f"识别的意图: {result['intent']}")
print(f"置信度: {result['confidence']}")
```

---

## 常见问题

### Q1: 如何调整AI回答的风格？
**A:** 修改system提示词中的角色描述和要求

```python
# 更正式
("system", "你是一个专业、严谨的企业级AI客服...")

# 更友好
("system", "你是一个热情、友好的AI助手，用轻松的语气...")

# 更简洁
("system", "你是AI客服。要求：回答简洁，不超过3句话...")
```

### Q2: 如何提高意图识别准确率？
**A:** 
1. 提供更多示例
2. 明确意图定义
3. 增加few-shot示例

```python
("system", """意图识别助手。

示例：
- "密码忘了" -> 问答
- "我要投诉" -> 工单
- "产品价格" -> 产品咨询

现在分析：""")
```

### Q3: 如何处理知识库检索不到的情况？
**A:** 在提示词中明确指示

```python
("system", """基于知识库回答。
重要：如果知识库中没有相关信息，回复：
"抱歉，我在知识库中没有找到相关信息。我可以为您创建工单，由人工客服跟进。"
""")
```

### Q4: 如何限制AI回答长度？
**A:** 
1. 在提示词中要求
2. 调整max_tokens参数

```python
# 方法1：提示词
("system", "回答要简洁，不超过100字...")

# 方法2：配置
self.llm = ChatOpenAI(
    max_tokens=200  # 限制输出长度
)
```

---

## 推荐学习资源

### 官方文档
- [LangChain文档](https://python.langchain.com/)
- [LangGraph文档](https://langchain-ai.github.io/langgraph/)
- [OpenAI API文档](https://platform.openai.com/docs)
- [Chroma文档](https://docs.trychroma.com/)

### 进阶阅读
- RAG技术详解
- 提示词工程最佳实践
- 向量数据库原理
- LangGraph高级模式

### 实践建议
1. 每天修改一个提示词，观察效果
2. 尝试添加新的节点和路由
3. 用真实场景测试系统
4. 记录遇到的问题和解决方案

---

## 总结

### 核心文件清单
✅ `backend/services/langgraph_workflow.py` - LangGraph工作流（最重要）
✅ `backend/services/knowledge_retriever.py` - 向量检索
✅ `backend/services/redis_cache.py` - 上下文管理
✅ `backend/config.py` - AI配置参数

### 关键概念
- **StateGraph**: 状态机工作流
- **节点（Node）**: 处理逻辑单元
- **边（Edge）**: 节点连接
- **条件路由**: 根据状态决定流程
- **RAG**: 检索增强生成
- **Embeddings**: 文本向量化
- **提示词工程**: 引导AI输出

### 学习建议
1. 先运行系统，理解整体流程
2. 逐个研究每个节点的实现
3. 修改提示词，观察变化
4. 添加新功能，实践所学
5. 阅读官方文档，深入理解

祝学习顺利！🚀
