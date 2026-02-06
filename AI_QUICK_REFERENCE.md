# AI核心代码快速参考

## 🎯 最重要的3个文件

### 1. LangGraph工作流
**文件：** `backend/services/langgraph_workflow.py`

**核心代码片段：**

```python
# 状态定义
class ConversationState(TypedDict):
    user_message: str
    intent: str
    response: str

# 构建图
workflow = StateGraph(ConversationState)
workflow.add_node("intent", intent_node)
workflow.add_node("qa", qa_node)
workflow.add_conditional_edges("intent", route_decision)
graph = workflow.compile()

# 执行
result = await graph.ainvoke(initial_state)
```

### 2. 向量检索
**文件：** `backend/services/knowledge_retriever.py`

**核心代码片段：**

```python
# 初始化
embeddings = OpenAIEmbeddings()
client = chromadb.Client()

# 添加文档
embeddings_list = embeddings.embed_documents(texts)
collection.add(documents=texts, embeddings=embeddings_list)

# 检索
query_embedding = embeddings.embed_query(query)
results = collection.query(query_embeddings=[query_embedding], n_results=3)
```

### 3. 提示词模板
**文件：** `backend/services/langgraph_workflow.py`

**核心代码片段：**

```python
# 构建提示词
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是AI客服..."),
    ("human", "用户问题：{question}")
])

# 调用LLM
response = await llm.ainvoke(prompt.format_messages(question="..."))
```

---

## 📝 常用代码模板

### 添加新节点
```python
async def my_new_node(self, state: ConversationState):
    # 1. 构建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你的角色定义"),
        ("human", "{input}")
    ])
    
    # 2. 调用LLM
    response = await self.llm.ainvoke(
        prompt.format_messages(input=state["user_message"])
    )
    
    # 3. 更新状态
    state["response"] = response.content
    
    return state
```

### 添加条件路由
```python
def my_route_decision(state: ConversationState) -> str:
    if state["confidence"] > 0.8:
        return "high_confidence_path"
    else:
        return "low_confidence_path"

# 在图中使用
workflow.add_conditional_edges(
    "source_node",
    my_route_decision,
    {
        "high_confidence_path": "node_a",
        "low_confidence_path": "node_b"
    }
)
```

### 检索并生成回答（RAG）
```python
# 1. 检索
docs = await knowledge_retriever.retrieve(query, top_k=3)

# 2. 构建上下文
context = "\n".join([doc.page_content for doc in docs])

# 3. 生成回答
prompt = ChatPromptTemplate.from_messages([
    ("system", "基于以下知识库回答"),
    ("human", "知识库：{context}\n问题：{question}")
])

response = await llm.ainvoke(prompt.format_messages(
    context=context,
    question=query
))
```

---

## 🔧 配置参数

### LLM参数（config.py）
```python
OPENAI_MODEL = "gpt-4"           # 模型选择
OPENAI_TEMPERATURE = 0.7         # 创造性（0-2）
OPENAI_MAX_TOKENS = 2000         # 最大输出长度
```

**温度说明：**
- 0.0-0.3: 确定性强，适合事实性回答
- 0.4-0.7: 平衡，适合对话
- 0.8-1.0: 创造性强，适合创意内容

### 检索参数
```python
RETRIEVAL_TOP_K = 3              # 检索文档数量
CONTEXT_MAX_HISTORY = 20         # 保留对话轮数
```

---

## 🐛 调试命令

### 测试单个组件
```python
# 测试意图识别
python -c "
from services.langgraph_workflow import langgraph_workflow
import asyncio

async def test():
    state = {'user_message': '如何重置密码？'}
    result = await langgraph_workflow.intent_recognition_node(state)
    print(result)

asyncio.run(test())
"
```

### 查看向量库内容
```python
# 查看集合统计
python -c "
from services.knowledge_retriever import knowledge_retriever
stats = knowledge_retriever.get_collection_stats()
print(stats)
"
```

---

## 💡 快速修改指南

### 修改AI回答风格
**位置：** `langgraph_workflow.py` → `qa_flow_node`

```python
# 找到这行
("system", "你是一个专业的AI客服助手...")

# 修改为
("system", "你是一个友好活泼的AI助手，用轻松幽默的语气回答...")
```

### 添加新的意图类型
**位置：** `langgraph_workflow.py`

```python
# 1. 在 intent_recognition_node 的提示词中添加
"- 投诉：用户表达不满或投诉"

# 2. 在 route_decision 中添加路由
intent_map = {
    "问答": "qa_flow",
    "工单": "ticket_flow",
    "投诉": "complaint_flow"  # 新增
}

# 3. 实现 complaint_flow_node
async def complaint_flow_node(self, state):
    # 处理投诉逻辑
    pass

# 4. 在 _build_graph 中注册
workflow.add_node("complaint_flow", self.complaint_flow_node)
```

### 调整检索数量
**位置：** `config.py`

```python
RETRIEVAL_TOP_K = 5  # 从3改为5，检索更多文档
```

---

## 📊 性能优化

### 减少LLM调用次数
```python
# 缓存常见问题的回答
if state["user_message"] in common_questions:
    state["response"] = cached_answers[state["user_message"]]
    return state
```

### 并行处理
```python
import asyncio

# 并行检索多个来源
results = await asyncio.gather(
    knowledge_retriever.retrieve(query, "knowledge_base"),
    knowledge_retriever.retrieve(query, "product_catalog")
)
```

---

## 🎓 学习检查清单

- [ ] 理解StateGraph的工作原理
- [ ] 能够添加新的节点
- [ ] 能够修改提示词
- [ ] 理解RAG流程
- [ ] 能够调试LLM输出
- [ ] 理解向量检索原理
- [ ] 能够添加条件路由
- [ ] 理解上下文管理

---

## 🔗 相关文件索引

| 功能 | 文件路径 |
|------|----------|
| LangGraph工作流 | `backend/services/langgraph_workflow.py` |
| 向量检索 | `backend/services/knowledge_retriever.py` |
| 上下文管理 | `backend/services/redis_cache.py` |
| AI配置 | `backend/config.py` |
| 对话API | `backend/api/chat.py` |
| 完整学习指南 | `AI_LEARNING_GUIDE.md` |
