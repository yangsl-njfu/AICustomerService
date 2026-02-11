# 实现计划：AI 工作流增强

## 概述

基于设计文档，将三项 AI 工作流增强功能分解为增量式编码任务。每个任务在前一个任务基础上构建，确保无孤立代码。使用 Python + hypothesis 进行属性测试。

## Tasks

- [x] 1. 扩展 ConversationState 和配置项
  - [x] 1.1 在 `backend/services/ai/state.py` 中为 ConversationState 添加 `intent_history` 和 `conversation_summary` 字段
    - `intent_history: Optional[List[Dict[str, Any]]]`
    - `conversation_summary: Optional[str]`
    - _Requirements: 1.1, 1.6, 3.2, 3.7_
  - [x] 1.2 在 `backend/config.py` 的 Settings 类中添加新配置项
    - `INTENT_HISTORY_SIZE: int = 5`
    - `INTENT_FALLBACK_THRESHOLD: float = 0.6`
    - `SUMMARY_TRIGGER_THRESHOLD: int = 10`
    - `CONTEXT_MAX_TOKENS: int = 3000`
    - _Requirements: 1.2, 1.3, 3.1, 3.5_

- [x] 2. 改造 ContextNode 和 Redis Cache
  - [x] 2.1 修改 `backend/services/redis_cache.py` 的 `get_context` 和 `update_context` 方法，支持 `intent_history` 和 `conversation_summary` 字段的读写
    - _Requirements: 1.6, 3.7_
  - [x] 2.2 修改 `backend/services/ai/nodes/context_node.py`，在加载上下文时读取 `intent_history` 和 `conversation_summary` 并写入 state
    - _Requirements: 1.5, 1.6, 3.4_
  - [ ]* 2.3 编写属性测试：上下文持久化往返一致性
    - **Property 4: 上下文持久化往返一致性**
    - **Validates: Requirements 1.6, 3.7**

- [x] 3. 实现多轮对话意图追踪
  - [x] 3.1 修改 `backend/services/ai/nodes/intent_node.py`，增加意图历史上下文 prompt 模板和回退逻辑
    - 新增 `SYSTEM_PROMPT_WITH_HISTORY` 和 `PROMPT_WITH_HISTORY`
    - 当 intent_history 非空时使用带历史的 prompt
    - 将新意图追加到 state["intent_history"]
    - 当置信度低于阈值时回退到最近高置信度意图
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [ ]* 3.2 编写属性测试：意图历史每轮增长一条
    - **Property 1: 意图历史每轮增长一条**
    - **Validates: Requirements 1.1**
  - [ ]* 3.3 编写属性测试：Prompt 中仅包含最近 N 条意图历史
    - **Property 2: Prompt 中仅包含最近 N 条意图历史**
    - **Validates: Requirements 1.2**
  - [ ]* 3.4 编写属性测试：低置信度回退到最近高置信度意图
    - **Property 3: 低置信度回退到最近高置信度意图**
    - **Validates: Requirements 1.3**

- [x] 4. Checkpoint - 确保意图追踪相关测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 5. 迁移至 LangChain 原生 Tool Binding
  - [x] 5.1 在 `backend/services/function_tools.py` 中使用 `@tool` 装饰器重新定义六个工具函数（query_order、search_products、get_user_info、check_inventory、get_logistics、calculate_price），保留原有业务逻辑
    - 导出 `all_tools` 列表
    - 保留旧的 `FunctionTool` 类和 `function_tool_manager` 以便渐进迁移
    - _Requirements: 2.1, 2.3, 2.7_
  - [x] 5.2 改造 `backend/services/ai/nodes/function_calling_node.py`，使用 `llm.bind_tools(all_tools)` 替代自定义 JSON Schema 匹配
    - 解析 `response.tool_calls` 并执行对应工具
    - 无 tool_calls 时跳过
    - 异常时捕获并记录错误
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 2.6_
  - [ ]* 5.3 编写属性测试：Tool Call 正确分发
    - **Property 5: Tool Call 正确分发**
    - **Validates: Requirements 2.2**
  - [ ]* 5.4 编写属性测试：无 Tool Call 时跳过工具执行
    - **Property 6: 无 Tool Call 时跳过工具执行**
    - **Validates: Requirements 2.5**
  - [ ]* 5.5 编写属性测试：工具异常不中断工作流
    - **Property 7: 工具异常不中断工作流**
    - **Validates: Requirements 2.6**
  - [ ]* 5.6 编写属性测试：工具 Schema 向后兼容
    - **Property 8: 工具 Schema 向后兼容**
    - **Validates: Requirements 2.7**

- [x] 6. Checkpoint - 确保 Tool Binding 迁移测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 7. 实现对话摘要压缩机制
  - [x] 7.1 新建 `backend/services/ai/summarizer.py`，实现 ConversationSummarizer 类
    - `should_summarize(history)` 方法
    - `summarize(history, existing_summary)` 方法（调用 LLM 生成摘要）
    - `fallback_truncate(history)` 方法
    - token 估算和限制逻辑
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.6_
  - [x] 7.2 修改 `backend/services/ai/nodes/save_context_node.py`，集成 ConversationSummarizer
    - 在保存上下文后检查是否需要摘要
    - 摘要成功时更新 cache 中的 summary 和 history
    - 摘要失败时执行回退截断
    - 持久化 intent_history
    - _Requirements: 3.1, 3.2, 3.3, 3.6, 3.7_
  - [x] 7.3 修改 `backend/services/ai/nodes/qa_node.py` 的 RAG_PROMPT，在 prompt 中注入 conversation_summary
    - _Requirements: 3.4_
  - [ ]* 7.4 编写属性测试：摘要触发阈值判定
    - **Property 9: 摘要触发阈值判定**
    - **Validates: Requirements 3.1**
  - [ ]* 7.5 编写属性测试：摘要保留尾部历史
    - **Property 10: 摘要保留尾部历史**
    - **Validates: Requirements 3.2, 3.3**
  - [ ]* 7.6 编写属性测试：摘要注入 QA Prompt
    - **Property 11: 摘要注入 QA Prompt**
    - **Validates: Requirements 3.4**
  - [ ]* 7.7 编写属性测试：摘要后 Token 数不超限
    - **Property 12: 摘要后 Token 数不超限**
    - **Validates: Requirements 3.5**
  - [ ]* 7.8 编写属性测试：摘要异常时回退截断
    - **Property 13: 摘要异常时回退截断**
    - **Validates: Requirements 3.6**

- [x] 8. 集成与连线
  - [x] 8.1 修改 `backend/services/ai/workflow.py` 中的 AIWorkflow，将 LLM 传递给 SaveContextNode 以支持摘要功能，并更新 `_make_initial_state` 初始化新字段
    - _Requirements: 1.5, 3.1_
  - [x] 8.2 清理旧代码：移除 `function_tools.py` 中不再使用的 `FunctionTool` 基类和 `FunctionToolManager`（确认所有引用已迁移后）
    - _Requirements: 2.1, 2.3_

- [x] 9. Final Checkpoint - 确保所有测试通过
  - 确保所有测试通过，如有问题请向用户确认。

## 备注

- 标记 `*` 的子任务为可选测试任务，可跳过以加速 MVP
- 每个任务引用了具体的需求编号以确保可追溯性
- 属性测试验证通用正确性属性，单元测试验证具体示例和边界情况
- Checkpoint 任务确保增量验证
