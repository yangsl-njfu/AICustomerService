# 需求文档：AI 工作流增强

## 简介

本需求文档描述毕业设计交易平台 AI 客服系统的三项核心增强功能：多轮对话意图追踪、迁移至 LangChain 原生 Tool Binding、以及对话摘要压缩机制。这三项改进旨在提升意图识别的连贯性、工具调用的稳定性和长对话的上下文保持能力。

## 术语表

- **Intent_Tracker（意图追踪器）**：负责在多轮对话中维护意图历史并利用上下文推断当前意图的组件
- **Intent_History（意图历史）**：按时间顺序记录的意图序列，包含每轮对话的意图标签和置信度
- **Tool_Binding（工具绑定）**：LangChain 提供的原生机制，将 Python 函数或 Pydantic 模型直接绑定到 LLM，由 LLM 自动生成结构化工具调用
- **Function_Calling_Node（函数调用节点）**：LangGraph 工作流中负责工具选择和执行的节点
- **Conversation_Summarizer（对话摘要器）**：负责将较早的对话历史压缩为摘要文本的组件
- **Context_Window（上下文窗口）**：发送给 LLM 的对话历史范围，当前固定为最近 20 轮
- **Redis_Cache（缓存服务）**：当前使用内存缓存实现的会话上下文存储服务
- **ConversationState（对话状态）**：LangGraph 工作流中流转的 TypedDict 状态对象
- **DeepSeek_LLM**：系统使用的大语言模型，通过 LangChain ChatOpenAI 接口调用

## 需求

### 需求 1：多轮对话意图追踪

**用户故事：** 作为一名用户，我希望 AI 客服在多轮对话中能记住我之前的意图，这样当我在话题之间切换时不会丢失上下文。

#### 验收标准

1. WHEN 用户发送一条新消息, THE Intent_Tracker SHALL 将当前轮的意图分类结果（意图标签和置信度）追加到 Intent_History 中
2. WHEN 进行意图识别时, THE Intent_Tracker SHALL 将最近 N 轮的 Intent_History 作为上下文提供给 LLM，辅助当前意图分类（N 通过配置项 `INTENT_HISTORY_SIZE` 控制，默认值为 5）
3. WHEN 用户消息的意图不明确且置信度低于阈值时, THE Intent_Tracker SHALL 参考 Intent_History 中最近的高置信度意图作为回退依据
4. WHEN 用户明确切换话题（例如从"商品咨询"转到"订单查询"）时, THE Intent_Tracker SHALL 识别出新意图并正确更新 Intent_History，不受历史意图的干扰
5. WHEN 一个新会话开始时, THE Intent_Tracker SHALL 初始化一个空的 Intent_History
6. THE Intent_History SHALL 与 ConversationState 一起在 Redis_Cache 中持久化，确保页面刷新后意图历史不丢失

### 需求 2：迁移至 LangChain 原生 Tool Binding

**用户故事：** 作为一名开发者，我希望将自定义的 JSON Schema 工具调用实现替换为 LangChain 原生 Tool Binding，这样可以获得更好的稳定性和可维护性。

#### 验收标准

1. THE Function_Calling_Node SHALL 使用 LangChain 的 `bind_tools` 方法将工具绑定到 DeepSeek_LLM，替代当前的自定义 JSON Schema 匹配实现
2. WHEN LLM 返回 tool_calls 时, THE Function_Calling_Node SHALL 解析 tool_calls 并自动执行对应的工具函数
3. THE Tool_Binding SHALL 使用 `@tool` 装饰器或 Pydantic 模型定义工具，替代当前的 `FunctionTool` 抽象基类
4. WHEN 工具执行完成后, THE Function_Calling_Node SHALL 将工具执行结果以 `ToolMessage` 格式回传给 LLM，使 LLM 能基于工具结果生成最终回复
5. WHEN LLM 未返回任何 tool_calls 时, THE Function_Calling_Node SHALL 跳过工具执行并按原有路由逻辑继续处理
6. IF 工具执行过程中发生异常, THEN THE Function_Calling_Node SHALL 捕获异常并返回包含错误信息的 ToolMessage，确保工作流不中断
7. THE Tool_Binding SHALL 保持与现有六个工具（query_order、search_products、get_user_info、check_inventory、get_logistics、calculate_price）相同的功能和参数接口

### 需求 3：对话摘要压缩机制

**用户故事：** 作为一名用户，我希望在长对话中 AI 客服仍然能记住早期讨论的重要信息，这样我不需要重复说过的内容。

#### 验收标准

1. WHEN 对话历史轮数超过配置的阈值（`SUMMARY_TRIGGER_THRESHOLD`，默认 10 轮）时, THE Conversation_Summarizer SHALL 自动触发摘要生成
2. WHEN 摘要触发时, THE Conversation_Summarizer SHALL 将阈值之前的历史消息压缩为一段结构化摘要文本，保留关键信息（用户意图、提及的商品、订单号、已解决的问题）
3. WHEN 摘要生成完成后, THE Conversation_Summarizer SHALL 用摘要文本替换被压缩的历史消息，并保留阈值之后的最近对话原文
4. WHEN 向 LLM 发送上下文时, THE QA_Node SHALL 将摘要文本作为系统上下文的一部分，与最近的对话历史原文一起提供给 LLM
5. THE Conversation_Summarizer SHALL 确保摘要后的总 token 数不超过配置的上限（`CONTEXT_MAX_TOKENS`，默认 3000）
6. IF 摘要生成过程中发生异常, THEN THE Conversation_Summarizer SHALL 回退到截断策略（保留最近 N 轮原文），确保对话不中断
7. THE Conversation_Summarizer SHALL 将生成的摘要与对话历史一起持久化到 Redis_Cache 中
