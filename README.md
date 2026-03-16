# AICustomerService

一个面向电商客服场景的 AI 项目，当前正在从“单业务定制工作流”演进为“微内核 + Business Pack 插件化”架构。

这份 README 重点说明 AI 部分的设计，不只是介绍功能。

## 1. 项目定位

这个项目的目标不是单纯做一个能聊天的客服，而是把 AI 能力沉淀成一套可复用的业务内核：

- 内核负责通用能力
- 业务包负责行业能力
- 新业务尽量通过配置和插件接入，而不是改核心 workflow

当前默认业务包是 `graduation-marketplace`，也就是“毕业设计商城”。

## 2. 为什么要改架构

旧结构的主要问题是：

- 模型初始化写在 workflow 里，模型切换依赖改代码
- 工具函数是固定集合，业务能力和 LangChain tool 强耦合
- `gateway` 虽然有 `business_id`，但 AI 主流程实际上没有按业务动态装配
- workflow 节点里混了大量电商/毕设业务语义，不利于复用

这会导致：

- 很难支持多业务
- 很难支持多租户
- 很难做模型分层策略
- 很难把工具治理、权限控制、开关管理做规范

## 3. 目标架构

核心思想：

```text
Business Request
  -> RuntimeFactory
     -> BusinessPack
     -> Models
     -> Tool Plugins
     -> Intent Handlers
     -> Prompt Config
  -> AIWorkflow
     -> Context
     -> Intent Recognition
     -> Function Calling / Agent
     -> Route
     -> Business Node
     -> Save Context
```

这套结构里有 4 个关键概念。

### 3.1 AI Kernel

AI Kernel 是稳定的共性能力，主要包括：

- workflow 编排
- 对话状态管理
- 意图路由框架
- 工具调用框架
- Agent 执行框架
- 上下文持久化
- 模型注入接口

它不应该知道“毕业设计商城”“订单退款”“技术栈匹配”这些具体业务词。

### 3.2 Business Pack

Business Pack 是业务包，负责当前业务的差异化能力：

- 业务标识
- 意图处理映射
- prompt 配置
- 工具插件启用清单
- 知识库配置
- 业务特性开关
- 模型覆盖配置

当前业务包配置在：

- `backend/config/businesses/graduation-marketplace.yaml`

### 3.3 Runtime

Runtime 是装配层，不负责回答用户问题，只负责把“这次请求该用哪套能力”装起来。

它负责：

- 读取 business pack
- 创建 adapter
- 初始化当前业务可用模型
- 注册当前业务允许使用的插件
- 对 workflow 暴露统一接口

### 3.4 Plugin

插件不是为了把函数换个名字，而是把能力变成“可注册、可过滤、可分组、可治理”的模块。

在这个项目里，插件主要承担的是工具能力：

- 查询订单
- 搜索商品
- 查询项目详情
- 技术栈匹配
- 个性化推荐

## 4. 当前代码映射

### 4.1 Kernel

- `backend/services/ai/workflow.py`
- `backend/services/ai/router.py`
- `backend/services/ai/state.py`
- `backend/services/ai/nodes/`

### 4.2 Runtime / Business Pack

- `backend/services/ai/runtime.py`
- `backend/config/businesses/graduation-marketplace.yaml`

### 4.3 Plugin System

- `backend/plugins/base.py`
- `backend/plugins/manager.py`
- `backend/plugins/builtin_tools.py`

### 4.4 API Entry

- `backend/api/chat.py`
- `backend/api/gateway.py`

## 5. 本次已经落地的改造

### 5.1 模型从 workflow 中解耦

现在 workflow 不再自己决定模型来源，而是通过 runtime 注入。

已经实现：

- `init_chat_model()` 支持 provider/model/api_key/base_url 覆盖
- `init_intent_model()` 支持独立模型配置
- runtime 可按 business pack 覆盖 LLM 参数

相关文件：

- `backend/config/__init__.py`
- `backend/services/ai/runtime.py`
- `backend/services/ai/workflow.py`

### 5.2 引入 Business Pack Runtime

新增 `AIRuntime` 和 `AIRuntimeFactory`，让 `business_id` 真正进入 AI 主链路。

已经实现：

- 根据 `business_id` 加载业务配置
- 缓存 runtime 和 workflow
- 创建 `ExecutionContext`
- 提供 `get_langchain_tools()`、`get_handler_for_intent()` 等运行时能力

相关文件：

- `backend/services/ai/runtime.py`

### 5.3 工具插件化

当前做法不是让业务代码直接依赖 `@tool`，而是先把内置 LangChain tools 包装成平台插件，再按业务包过滤。

已经实现：

- `LangChainToolPlugin`
- 插件别名解析
- 按组过滤插件
- `default` / `topic_advisor` 两套工具组

相关文件：

- `backend/plugins/builtin_tools.py`
- `backend/plugins/manager.py`

### 5.4 Workflow 改成运行时装配

workflow 现在会读取 runtime：

- 聊天模型
- 意图模型
- 工具插件
- business_id
- execution_context

并且保留了原有流程能力：

- 普通问答
- function calling
- 订单查询
- 商品咨询
- 购买流程
- 售后流程
- 选题推荐 Agent

相关文件：

- `backend/services/ai/workflow.py`

### 5.5 Chat / Gateway 接入新架构

已经实现：

- `chat.py` 改走默认 runtime workflow
- `gateway.py` 改走按 `business_id` 装配的 workflow
- `gateway` 的业务信息和插件列表可返回真实运行时内容

相关文件：

- `backend/api/chat.py`
- `backend/api/gateway.py`

### 5.6 业务包插件清单真正生效

`graduation-marketplace.yaml` 现在不只是占位配置，而是实际参与工具过滤。

当前已配置的工具示例：

- `query_order`
- `search_products`
- `get_personalized_recommendations`
- `search_projects`
- `get_project_detail`
- `compare_projects`
- `check_tech_stack_match`

### 5.7 修复了两个会直接挡住改造的基础问题

- 补了 `OrderService.get_order_by_no()`，避免订单工具调用断裂
- 修了 `DEBUG=release` 这类环境变量导致配置初始化失败的问题

## 6. 当前请求流转

以 `gateway` 请求为例：

```text
Client
  -> /api/v1/gateway/chat/message
  -> runtime_factory.get_runtime(business_id)
  -> runtime_factory.get_workflow(business_id)
  -> workflow.process_message(...)
     -> load_context
     -> intent_recognition
     -> function_calling / topic_advisor
     -> router
     -> business node
     -> save_context
  -> response
```

“推荐”意图是一个典型例子：

```text
用户消息
  -> 意图识别: 推荐
  -> workflow 直接路由到 TopicAdvisorNode
  -> TopicAdvisorNode 从 runtime 获取 topic_advisor 工具组
  -> Agent 自主调用项目搜索/详情/对比/匹配工具
  -> 生成文本 + quick_actions
```

## 7. 现在这套设计的意义

这次改造不会直接让 LLM 更聪明，也不会凭空提升回答质量。

它带来的价值是系统工程能力：

- 更容易切模型
- 更容易做多模型分工
- 更容易做多业务接入
- 更容易按业务开关工具
- 更容易后续接权限、审计、限流和 MCP

也就是说，这一步主要提升的是：

- 可扩展性
- 可维护性
- 可插拔性
- 运行时治理能力

## 8. 如何新增一个业务包

理论步骤如下：

1. 新建一个业务配置文件
2. 定义 business_id、features、plugins、prompts、llm 配置
3. 如果需要新的工具能力，注册新插件
4. 如果需要新的意图处理器，扩展 handler 映射
5. 通过 `gateway` 传入新的 `business_id`

最小形态下，只改配置就可以切换已有工具组合。

## 9. 如何新增一个工具插件

当前推荐做法：

1. 先实现业务能力
2. 如果它已经是 LangChain tool，就通过 `LangChainToolPlugin` 包装
3. 注册到 `PluginManager`
4. 在业务包 YAML 中启用
5. 通过 runtime 分组暴露给 workflow 或 agent

## 10. 当前边界

这次不是“企业级平台最终版”，而是第一阶段。

还没完全做完的部分：

- 意图定义还没有完全配置驱动
- prompt 体系还没有完全下沉到 business pack
- 工具层还没有统一改成 `ExecutionContext + Adapter + 权限校验`
- 还没有多租户隔离、审计、限流、熔断、观测
- 还没有把外部能力做成 MCP Server / MCP Client 体系

所以当前更准确的描述是：

**已经完成微内核插件架构的主链路重构，但还没有完成企业级治理层。**

## 11. 后续建议

如果继续往企业级做，建议按这个顺序推进：

1. 工具层统一接入 `ExecutionContext`
2. 增加 adapter 权限校验
3. 把 intent handler 和 prompt 完全配置化
4. 引入可观测性和审计日志
5. 做多租户隔离
6. 评估 MCP 接入外部系统

## 12. 开发说明

后端主要目录：

```text
backend/
  api/
  adapters/
  config/
  plugins/
  services/
    ai/
      nodes/
      runtime.py
      workflow.py
```

启动方式可参考：

- `start.bat`

如果只看 AI 主线，优先阅读这些文件：

- `backend/services/ai/runtime.py`
- `backend/services/ai/workflow.py`
- `backend/services/ai/router.py`
- `backend/plugins/builtin_tools.py`
- `backend/config/businesses/graduation-marketplace.yaml`

## 13. 安全提示

当前仓库里仍然存在敏感配置和较强的本地耦合，这部分不属于本次 README 改造范围，但在正式部署前必须继续处理：

- 清理硬编码密钥
- 统一环境变量管理
- 区分开发/测试/生产配置
- 为工具访问补权限和审计

---

如果后续继续演进，这份 README 应该同步更新，尤其是以下内容：

- Business Pack 结构
- 插件注册方式
- Intent Handler 配置方式
- MCP 接入说明
