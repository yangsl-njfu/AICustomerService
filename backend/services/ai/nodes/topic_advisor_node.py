"""
智能选题助手 Agent 节点

与普通 Workflow 节点的核心区别：
- Workflow: LLM 调用一次工具就结束，工具结果不会回传给 LLM
- Agent:   LLM 调用工具 → 拿到结果 → 再次思考 → 决定继续调工具还是给出最终回答（ReAct 循环）

这使得 Agent 能够：
1. 先搜索项目，看到结果后决定要不要查详情
2. 查完详情后决定要不要做技术匹配检查
3. 综合所有信息后给出最终推荐
整个过程由 LLM 自主决策，而非人工编写 if/else
"""
import json
import logging
from typing import List, Dict, Any
from .base import BaseNode
from ..state import ConversationState
from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage, ToolMessage
)
from services.function_tools import topic_advisor_tools

logger = logging.getLogger(__name__)

# Agent 最大推理轮数，防止无限循环
MAX_AGENT_ITERATIONS = 5

SYSTEM_PROMPT = """你是毕设商城的智能推荐助手 Agent。你负责处理所有和"推荐商品"相关的需求。

可用工具：
- search_projects: 按关键词/预算/难度搜索项目
- get_project_detail: 查看某个项目的完整详情
- compare_projects: 对比多个项目
- check_tech_stack_match: 检查用户技术能力是否匹配项目
- get_personalized_recommendations: 基于用户浏览历史获取个性化推荐

根据用户需求自动选择策略：
1. 用户带了明确关键词（如"推荐python项目"）→ 直接调 search_projects，返回结果即可
2. 用户没说要什么（如"有什么推荐""猜我喜欢"）→ 调 get_personalized_recommendations 看浏览历史
3. 用户需要帮忙做决策（如"帮我选个适合我的"）→ 多轮搜索 + 查详情 + 技术匹配，给出推荐理由

重要规则：
- 简单需求就简单处理，不要过度调用工具
- 只有用户需要帮忙做决策时，才进行多轮推理
- 推荐时给出理由（技术匹配、难度适中、价格合适等）
- 预算内的项目优先推荐
- 最终回答要简洁"""


class TopicAdvisorNode(BaseNode):
    """智能选题助手 Agent 节点 - 基于 ReAct 循环的真正 Agent"""

    def __init__(self, llm=None):
        super().__init__(llm)
        self.tools = topic_advisor_tools
        self.tool_map = {t.name: t for t in self.tools}
        # bind_tools 让 LLM 知道有哪些工具可以调用
        self.llm_with_tools = llm.bind_tools(self.tools) if llm else None

    def _build_history_str(self, history: List[Dict]) -> str:
        """构建对话历史字符串"""
        if not history:
            return "无"
        return "\n".join([
            f"用户：{turn.get('user', '')}\n助手：{turn.get('assistant', '')}"
            for turn in history[-5:]
        ])

    async def _run_agent_loop_stream(self, messages: list):
        """
        ReAct Agent 核心循环 - 流式版本

        与 _run_agent_loop 的区别：
        - 在关键步骤 yield 状态更新，让前端能看到 Agent 的思考过程
        - 工具调用阶段 yield {"type": "status", "message": "..."}
        - 最终回答 yield {"type": "token", "content": "..."}
        """
        tool_call_log = []

        for iteration in range(MAX_AGENT_ITERATIONS):
            logger.info(f"🔄 Agent 第 {iteration + 1} 轮推理")
            
            # 1. 调用 LLM（带工具绑定）
            response = await self.llm_with_tools.ainvoke(messages)

            # 2. 检查 LLM 是否决定调用工具
            if not response.tool_calls:
                # LLM 没有调用工具 → 它认为信息足够了，直接给出最终回答
                logger.info(f"✅ Agent 在第 {iteration + 1} 轮给出最终回答")
                # 流式输出最终回答
                for char in response.content:
                    yield {"type": "token", "content": char}
                yield {"type": "done", "tool_call_log": tool_call_log}
                return

            # 3. LLM 决定调用工具 → 执行工具并收集结果
            # 先把 LLM 的回复（包含 tool_calls）加入消息历史
            messages.append(response)

            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("args", {})
                tool_call_id = tc.get("id", f"call_{iteration}_{tool_name}")

                # 流式：通知前端正在调用工具
                tool_desc = self._get_tool_description(tool_name, tool_args)
                yield {"type": "status", "message": tool_desc}
                
                logger.info(
                    f"🛠️ Agent 调用工具: {tool_name}, "
                    f"参数: {json.dumps(tool_args, ensure_ascii=False)}"
                )

                try:
                    tool_fn = self.tool_map.get(tool_name)
                    if tool_fn:
                        result = await tool_fn.ainvoke(tool_args)
                    else:
                        result = {"error": f"未知工具: {tool_name}"}
                except Exception as e:
                    logger.error(f"工具执行失败: {tool_name}, 错误: {e}")
                    result = {"error": str(e)}

                tool_call_log.append({
                    "iteration": iteration + 1,
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result
                })

                # 4. 关键步骤：把工具结果作为 ToolMessage 回传给 LLM
                messages.append(ToolMessage(
                    content=json.dumps(result, ensure_ascii=False, default=str),
                    tool_call_id=tool_call_id
                ))

            # 循环继续 → LLM 会看到工具结果，决定是继续调工具还是给最终回答

        # 达到最大轮数，强制让 LLM 总结
        logger.warning(f"⚠️ Agent 达到最大轮数 {MAX_AGENT_ITERATIONS}，强制总结")
        messages.append(HumanMessage(
            content="你已经收集了足够的信息，请直接给出最终推荐，不要再调用工具。"
        ))
        final = await self.llm_with_tools.ainvoke(messages)
        # 流式输出最终回答
        for char in final.content:
            yield {"type": "token", "content": char}
        yield {"type": "done", "tool_call_log": tool_call_log}

    async def _run_agent_loop(self, messages: list) -> tuple[str, list]:
        """
        ReAct Agent 核心循环（非流式版本）

        Returns:
            (final_response, tool_call_log)
        """
        tool_call_log = []

        for iteration in range(MAX_AGENT_ITERATIONS):
            logger.info(f"🔄 Agent 第 {iteration + 1} 轮推理")
            response = await self.llm_with_tools.ainvoke(messages)

            if not response.tool_calls:
                logger.info(f"✅ Agent 在第 {iteration + 1} 轮给出最终回答")
                return response.content, tool_call_log

            messages.append(response)
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("args", {})
                tool_call_id = tc.get("id", f"call_{iteration}_{tool_name}")

                logger.info(f"🛠️ Agent 调用工具: {tool_name}, 参数: {json.dumps(tool_args, ensure_ascii=False)}")
                try:
                    tool_fn = self.tool_map.get(tool_name)
                    result = await tool_fn.ainvoke(tool_args) if tool_fn else {"error": f"未知工具: {tool_name}"}
                except Exception as e:
                    logger.error(f"工具执行失败: {tool_name}, 错误: {e}")
                    result = {"error": str(e)}

                tool_call_log.append({"iteration": iteration + 1, "tool": tool_name, "args": tool_args, "result": result})
                messages.append(ToolMessage(content=json.dumps(result, ensure_ascii=False, default=str), tool_call_id=tool_call_id))

        logger.warning(f"⚠️ Agent 达到最大轮数 {MAX_AGENT_ITERATIONS}，强制总结")
        messages.append(HumanMessage(content="你已经收集了足够的信息，请直接给出最终推荐，不要再调用工具。"))
        final = await self.llm_with_tools.ainvoke(messages)
        return final.content, tool_call_log

    def _get_tool_description(self, tool_name: str, tool_args: dict) -> str:
        """获取工具调用的描述，用于流式状态显示"""
        if tool_name == "search_projects":
            keyword = tool_args.get("keyword", "")
            max_price = tool_args.get("max_price", "")
            return f"🔍 正在搜索项目: {keyword}" + (f" (预算≤{max_price})" if max_price else "") + "..."
        elif tool_name == "get_project_detail":
            return f"📋 正在查看项目详情..."
        elif tool_name == "compare_projects":
            project_ids = tool_args.get("project_ids", [])
            return f"⚖️ 正在对比 {len(project_ids)} 个项目..."
        elif tool_name == "check_tech_stack_match":
            return "🔧 正在分析技术栈匹配度..."
        elif tool_name == "get_personalized_recommendations":
            return "📊 正在分析您的浏览偏好..."
        else:
            return f"🛠️ 正在执行: {tool_name}..."

    async def execute(self, state: ConversationState) -> ConversationState:
        """执行智能选题 Agent"""
        user_message = state.get("user_message", "")
        history = state.get("conversation_history", [])
        user_id = state.get("user_id", "")
        history_str = self._build_history_str(history)

        # 构建初始消息
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=(
                f"用户ID: {user_id}\n"
                f"对话历史：\n{history_str}\n\n"
                f"用户最新消息：{user_message}"
            ))
        ]

        try:
            # 运行 Agent 循环 —— LLM 自主决定调几次工具、查什么信息
            final_response, tool_call_log = await self._run_agent_loop(messages)

            state["response"] = final_response or "请告诉我您的选题需求，比如：我想做一个Java的医疗管理系统，预算500以内"
            state["topic_advisor_tool_results"] = tool_call_log

            # 从工具调用日志中提取搜索到的项目（用于前端展示卡片 + 购买按钮）
            for log_entry in tool_call_log:
                if log_entry["tool"] in ("search_projects", "get_personalized_recommendations"):
                    result = log_entry.get("result", {})
                    projects = result.get("projects", []) or result.get("products", [])
                    if projects:
                        state["topic_advisor_projects"] = projects
                        # 生成商品卡片
                        product_cards = []
                        for p in projects[:5]:
                            product_cards.append({
                                "type": "product",
                                "data": {
                                    "product_id": p.get("id"),
                                    "title": p.get("title"),
                                    "price": p.get("price"),
                                    "rating": p.get("rating"),
                                    "sales_count": p.get("sales_count", 0),
                                    "tech_stack": p.get("tech_stack", []),
                                    "description": p.get("description", "")[:150]
                                }
                            })
                        # 添加购买/购物车按钮（衔接购买流程）
                        for p in projects[:3]:
                            product_title = p.get("title", "")[:12]
                            product_cards.append({
                                "type": "button",
                                "label": f"立即购买: {product_title}",
                                "action": "purchase_flow",
                                "data": {"step": "confirm_product", "product_id": p.get("id")},
                                "icon": "💳"
                            })
                            product_cards.append({
                                "type": "button",
                                "label": f"加入购物车: {product_title}",
                                "action": "add_to_cart",
                                "data": {"product_id": p.get("id"), "product": p},
                                "icon": "🛒"
                            })
                        state["quick_actions"] = product_cards

            logger.info(
                f"🤖 Agent 完成: 共 {len(tool_call_log)} 次工具调用, "
                f"工具链: {' → '.join(l['tool'] for l in tool_call_log) or '无'}"
            )

        except Exception as e:
            logger.error(f"TopicAdvisor Agent 执行失败: {e}", exc_info=True)
            state["response"] = "抱歉，分析您的选题需求时出现了问题，请稍后重试。"

        return state

    async def execute_stream(self, state: ConversationState):
        """
        真正的流式执行 - Agent 完整版
        
        输出格式：
        - {"type": "status", "message": "..."}  - 工具调用状态
        - {"type": "token", "content": "..."}   - 最终回答的token
        - {"type": "done", "tool_call_log": [...]} - 完成，附带工具调用记录
        """
        user_message = state.get("user_message", "")
        history = state.get("conversation_history", [])
        user_id = state.get("user_id", "")
        history_str = self._build_history_str(history)

        # 构建初始消息
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=(
                f"用户ID: {user_id}\n"
                f"对话历史：\n{history_str}\n\n"
                f"用户最新消息：{user_message}"
            ))
        ]

        try:
            tool_call_log = []
            final_response = ""
            
            # 运行流式 Agent 循环
            async for event in self._run_agent_loop_stream(messages):
                if event["type"] == "token":
                    yield event["content"]
                    final_response += event["content"]
                elif event["type"] == "status":
                    # 状态更新，可以 yield 特殊标记让前端显示
                    yield f"\n[{event['message']}]\n"
                elif event["type"] == "done":
                    tool_call_log = event.get("tool_call_log", [])
            
            # 更新 state（供后续使用）
            state["response"] = final_response
            state["topic_advisor_tool_results"] = tool_call_log
            
            # 提取项目信息（与 execute 保持一致）
            for log_entry in tool_call_log:
                if log_entry["tool"] in ("search_projects", "get_personalized_recommendations"):
                    result = log_entry.get("result", {})
                    projects = result.get("projects", []) or result.get("products", [])
                    if projects:
                        state["topic_advisor_projects"] = projects
                        product_cards = []
                        for p in projects[:5]:
                            product_cards.append({
                                "type": "product",
                                "data": {
                                    "product_id": p.get("id"),
                                    "title": p.get("title"),
                                    "price": p.get("price"),
                                    "rating": p.get("rating"),
                                    "sales_count": p.get("sales_count", 0),
                                    "tech_stack": p.get("tech_stack", []),
                                    "description": p.get("description", "")[:150]
                                }
                            })
                        # 添加购买/购物车按钮
                        for p in projects[:3]:
                            product_title = p.get("title", "")[:12]
                            product_cards.append({
                                "type": "button",
                                "label": f"立即购买: {product_title}",
                                "action": "purchase_flow",
                                "data": {"step": "confirm_product", "product_id": p.get("id")},
                                "icon": "💳"
                            })
                            product_cards.append({
                                "type": "button",
                                "label": f"加入购物车: {product_title}",
                                "action": "add_to_cart",
                                "data": {"product_id": p.get("id"), "product": p},
                                "icon": "🛒"
                            })
                        state["quick_actions"] = product_cards

        except Exception as e:
            logger.error(f"TopicAdvisor Agent 流式执行失败: {e}", exc_info=True)
            yield "抱歉，分析您的选题需求时出现了问题，请稍后重试。"
