"""选题顾问智能体节点。"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from services.function_tools import topic_advisor_tools

from ..constants import DIALOGUE_ACT_REJECT, INTENT_RECOMMEND
from ..state import ConversationState
from .base import BaseNode

logger = logging.getLogger(__name__)

MAX_AGENT_ITERATIONS = 5

DEFAULT_SYSTEM_PROMPT = """你是毕业设计商城的智能选题助手智能体。
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
    """基于“推理-行动”风格的推荐智能体。"""

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

        slot_updates = state.get("slot_updates") or {}
        reference_resolution = state.get("reference_resolution") or {}
        active_task = state.get("active_task") or {}
        task_stack = state.get("task_stack") or []
        dialogue_context = (
            f"入口分类器: {state.get('entry_classifier') or 'unknown'}\n"
            f"流程内分类: {state.get('inflow_type') or 'none'}\n"
            f"当前步骤: {state.get('current_step') or 'none'}\n"
            f"本轮对话动作: {state.get('dialogue_act') or 'unknown'}\n"
            f"是否延续上一轮任务: {'是' if state.get('continue_previous_task') else '否'}\n"
            f"补充条件: {json.dumps(slot_updates, ensure_ascii=False)}\n"
            f"引用解析: {json.dumps(reference_resolution, ensure_ascii=False)}\n"
            f"当前任务: {json.dumps(active_task, ensure_ascii=False)}\n"
            f"挂起任务数量: {len(task_stack)}\n"
        )

        return [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(
                content=(
                    f"业务包: {business_id}\n"
                    f"业务名称: {business_name}\n"
                    f"用户ID: {user_id}\n"
                    f"历史对话:\n{history_str}\n\n"
                    f"{dialogue_context}"
                    f"用户最新消息: {state.get('user_message', '')}"
                )
            ),
        ]

    def _get_recommended_product_actions(self, state: ConversationState) -> List[Dict[str, Any]]:
        return [
            action
            for action in (state.get("last_quick_actions") or [])
            if action.get("type") == "product"
        ]

    def _should_refine_preferences(self, state: ConversationState) -> bool:
        active_task = state.get("active_task") or {}
        active_intent = state.get("intent") or active_task.get("intent") or state.get("last_intent")
        if active_intent != INTENT_RECOMMEND:
            return False
        if state.get("dialogue_act") != DIALOGUE_ACT_REJECT:
            return False
        if state.get("slot_updates"):
            return False
        if self._get_recommended_product_actions(state):
            return True
        return bool((active_task.get("slots") or {}).get("rejected_product_ids"))

    def _remember_rejected_products(self, state: ConversationState) -> None:
        active_task = state.get("active_task") or {}
        if not active_task:
            return

        product_ids = [
            action.get("data", {}).get("product_id")
            for action in self._get_recommended_product_actions(state)
            if action.get("data", {}).get("product_id") is not None
        ]
        if not product_ids:
            return

        slots = dict(active_task.get("slots", {}))
        existing = list(slots.get("rejected_product_ids") or [])
        merged = list(dict.fromkeys(existing + product_ids))
        slots["rejected_product_ids"] = merged
        active_task["slots"] = slots
        state["active_task"] = active_task

    def _build_refinement_quick_actions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "button",
                "label": "换简单一点",
                "action": "send_question",
                "data": {"question": "换简单一点的，最好基础一些"},
                "icon": "lightbulb",
            },
            {
                "type": "button",
                "label": "换便宜一点",
                "action": "send_question",
                "data": {"question": "换便宜一点的，预算再低一些"},
                "icon": "wallet",
            },
            {
                "type": "button",
                "label": "换技术栈",
                "action": "send_question",
                "data": {"question": "换个技术栈，我不想要这类技术栈"},
                "icon": "cpu",
            },
            {
                "type": "button",
                "label": "换项目类型",
                "action": "send_question",
                "data": {"question": "换个项目类型，别要管理系统这类"},
                "icon": "grid",
            },
        ]

    def _prepare_refinement_response(self, state: ConversationState) -> None:
        self._remember_rejected_products(state)
        state["topic_advisor_projects"] = []
        state["response"] = (
            "明白了，这一批都不太合适。我先不继续盲目重推。"
            "您更想调整哪一块：技术栈、项目类型、难度还是预算？"
            "也可以直接告诉我，比如“换 Python 的”“别要管理系统”“简单一点”或“500 以内”。"
        )
        state["quick_actions"] = self._build_refinement_quick_actions()
        state["topic_advisor_tool_results"] = []

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
        if self._should_refine_preferences(state):
            self._prepare_refinement_response(state)
            return state
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
        if self._should_refine_preferences(state):
            self._prepare_refinement_response(state)
            yield state["response"]
            return
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
