"""Topic advisor agent node."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from services.function_tools import topic_advisor_tools

from ..state import ConversationState
from .base import BaseNode

logger = logging.getLogger(__name__)

MAX_AGENT_ITERATIONS = 5

DEFAULT_SYSTEM_PROMPT = """你是毕业设计商城的智能选题助手 Agent。
你的目标是帮助用户完成选题、项目对比、技术栈匹配和个性化推荐。

可用工具包括：
- search_projects: 搜索项目
- get_project_detail: 查看单个项目详情
- compare_projects: 对比多个项目
- check_tech_stack_match: 分析技能匹配度
- get_personalized_recommendations: 基于浏览历史推荐

规则：
1. 简单需求直接给结果，不要过度调用工具。
2. 如果用户需要帮助决策，再做多轮搜索和比较。
3. 最终回复必须简洁，给出明确推荐理由。
4. 优先推荐预算合适、难度匹配的项目。"""


class TopicAdvisorNode(BaseNode):
    """ReAct-style recommendation agent."""

    def __init__(self, llm=None, runtime=None):
        super().__init__(llm=llm, runtime=runtime)
        self.tools = []
        self.tool_map = {}
        self.llm_with_tools = None
        self._refresh_tools()

    def _refresh_tools(self, execution_context=None):
        tools = []
        if self.runtime is not None:
            tools = self.runtime.get_langchain_tools(
                "topic_advisor",
                execution_context=execution_context,
            )
        if not tools:
            tools = list(topic_advisor_tools)

        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}
        self.llm_with_tools = self.llm.bind_tools(self.tools) if self.llm and self.tools else None

    def _build_history_str(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return "无"
        return "\n".join(
            f"用户: {turn.get('user', '')}\n助手: {turn.get('assistant', '')}"
            for turn in history[-5:]
        )

    def _get_system_prompt(self) -> str:
        if self.runtime is None:
            return DEFAULT_SYSTEM_PROMPT
        return self.runtime.get_prompt("topic_advisor_system_prompt", DEFAULT_SYSTEM_PROMPT)

    def _build_messages(self, state: ConversationState) -> List[Any]:
        history_str = self._build_history_str(state.get("conversation_history", []))
        user_id = state.get("user_id", "")
        business_id = state.get("business_id") or "default"
        business_name = business_id
        execution_context = state.get("execution_context") or {}
        if isinstance(execution_context, dict):
            business_name = execution_context.get("business_name", business_name)

        return [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(
                content=(
                    f"业务包: {business_id}\n"
                    f"业务名称: {business_name}\n"
                    f"用户ID: {user_id}\n"
                    f"历史对话:\n{history_str}\n\n"
                    f"用户最新消息: {state.get('user_message', '')}"
                )
            ),
        ]

    async def _run_agent_loop_stream(self, messages: list):
        tool_call_log = []

        for iteration in range(MAX_AGENT_ITERATIONS):
            logger.info("Topic advisor iteration=%s", iteration + 1)
            response = await self.llm_with_tools.ainvoke(messages)

            if not response.tool_calls:
                for char in response.content:
                    yield {"type": "token", "content": char}
                yield {"type": "done", "tool_call_log": tool_call_log}
                return

            messages.append(response)
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call.get("args", {})
                tool_call_id = tool_call.get("id", f"call_{iteration}_{tool_name}")

                yield {"type": "status", "message": self._get_tool_description(tool_name, tool_args)}

                try:
                    tool = self.tool_map.get(tool_name)
                    result = await tool.ainvoke(tool_args) if tool else {"error": f"未知工具: {tool_name}"}
                except Exception as exc:
                    logger.error("Topic advisor tool failed: %s error=%s", tool_name, exc)
                    result = {"error": str(exc)}

                tool_call_log.append(
                    {
                        "iteration": iteration + 1,
                        "tool": tool_name,
                        "args": tool_args,
                        "result": result,
                    }
                )
                messages.append(
                    ToolMessage(
                        content=json.dumps(result, ensure_ascii=False, default=str),
                        tool_call_id=tool_call_id,
                    )
                )

        logger.warning("Topic advisor reached max iterations, forcing final summary")
        messages.append(HumanMessage(content="请直接给出最终推荐结论，不要再调用工具。"))
        final = await self.llm_with_tools.ainvoke(messages)
        for char in final.content:
            yield {"type": "token", "content": char}
        yield {"type": "done", "tool_call_log": tool_call_log}

    async def _run_agent_loop(self, messages: list) -> tuple[str, list]:
        tool_call_log = []

        for iteration in range(MAX_AGENT_ITERATIONS):
            logger.info("Topic advisor iteration=%s", iteration + 1)
            response = await self.llm_with_tools.ainvoke(messages)

            if not response.tool_calls:
                return response.content, tool_call_log

            messages.append(response)
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call.get("args", {})
                tool_call_id = tool_call.get("id", f"call_{iteration}_{tool_name}")

                try:
                    tool = self.tool_map.get(tool_name)
                    result = await tool.ainvoke(tool_args) if tool else {"error": f"未知工具: {tool_name}"}
                except Exception as exc:
                    logger.error("Topic advisor tool failed: %s error=%s", tool_name, exc)
                    result = {"error": str(exc)}

                tool_call_log.append(
                    {
                        "iteration": iteration + 1,
                        "tool": tool_name,
                        "args": tool_args,
                        "result": result,
                    }
                )
                messages.append(
                    ToolMessage(
                        content=json.dumps(result, ensure_ascii=False, default=str),
                        tool_call_id=tool_call_id,
                    )
                )

        logger.warning("Topic advisor reached max iterations, forcing final summary")
        messages.append(HumanMessage(content="请直接给出最终推荐结论，不要再调用工具。"))
        final = await self.llm_with_tools.ainvoke(messages)
        return final.content, tool_call_log

    def _get_tool_description(self, tool_name: str, tool_args: dict) -> str:
        if tool_name == "search_projects":
            keyword = tool_args.get("keyword", "")
            max_price = tool_args.get("max_price")
            if max_price:
                return f"正在搜索项目: {keyword} (预算 <= {max_price})..."
            return f"正在搜索项目: {keyword}..."
        if tool_name == "get_project_detail":
            return "正在查看项目详情..."
        if tool_name == "compare_projects":
            return f"正在对比 {len(tool_args.get('project_ids', []))} 个项目..."
        if tool_name == "check_tech_stack_match":
            return "正在分析技术栈匹配度..."
        if tool_name == "get_personalized_recommendations":
            return "正在分析用户偏好并生成个性化推荐..."
        return f"正在执行工具: {tool_name}..."

    def _inject_project_actions(self, state: ConversationState, tool_call_log: List[Dict[str, Any]]):
        for log_entry in tool_call_log:
            if log_entry["tool"] not in ("search_projects", "get_personalized_recommendations"):
                continue

            result = log_entry.get("result", {})
            projects = result.get("projects", []) or result.get("products", [])
            if not projects:
                continue

            state["topic_advisor_projects"] = projects
            quick_actions = []

            for project in projects[:5]:
                quick_actions.append(
                    {
                        "type": "product",
                        "data": {
                            "product_id": project.get("id"),
                            "title": project.get("title"),
                            "price": project.get("price"),
                            "rating": project.get("rating"),
                            "sales_count": project.get("sales_count", 0),
                            "tech_stack": project.get("tech_stack", []),
                            "description": project.get("description", "")[:150],
                        },
                    }
                )

            for project in projects[:3]:
                product_title = project.get("title", "")[:12]
                quick_actions.append(
                    {
                        "type": "button",
                        "label": f"立即购买: {product_title}",
                        "action": "purchase_flow",
                        "data": {"step": "confirm_product", "product_id": project.get("id")},
                        "icon": "📦",
                    }
                )
                quick_actions.append(
                    {
                        "type": "button",
                        "label": f"加入购物车: {product_title}",
                        "action": "add_to_cart",
                        "data": {"product_id": project.get("id"), "product": project},
                        "icon": "🛒",
                    }
                )

            state["quick_actions"] = quick_actions
            return

    async def execute(self, state: ConversationState) -> ConversationState:
        self._refresh_tools(execution_context=state.get("execution_context"))
        messages = self._build_messages(state)

        try:
            final_response, tool_call_log = await self._run_agent_loop(messages)
            state["response"] = (
                final_response
                or "请告诉我您的选题需求，例如：我想做一个 Java 医疗管理系统，预算 500 元以内。"
            )
            state["topic_advisor_tool_results"] = tool_call_log
            self._inject_project_actions(state, tool_call_log)
        except Exception as exc:
            logger.error("Topic advisor failed: %s", exc, exc_info=True)
            state["response"] = "抱歉，分析您的选题需求时出现了问题，请稍后重试。"

        return state

    async def execute_stream(self, state: ConversationState):
        self._refresh_tools(execution_context=state.get("execution_context"))
        messages = self._build_messages(state)

        try:
            final_response = ""
            tool_call_log = []
            async for event in self._run_agent_loop_stream(messages):
                if event["type"] == "token":
                    final_response += event["content"]
                    yield event["content"]
                elif event["type"] == "status":
                    yield f"\n[{event['message']}]\n"
                elif event["type"] == "done":
                    tool_call_log = event.get("tool_call_log", [])

            state["response"] = final_response
            state["topic_advisor_tool_results"] = tool_call_log
            self._inject_project_actions(state, tool_call_log)
        except Exception as exc:
            logger.error("Topic advisor stream failed: %s", exc, exc_info=True)
            yield "抱歉，分析您的选题需求时出现了问题，请稍后重试。"
