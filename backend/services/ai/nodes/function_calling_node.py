"""
Function Calling节点 - 使用 LangChain 原生 Tool Binding
"""
import logging
from .base import BaseNode
from ..state import ConversationState
from services.function_tools import all_tools

logger = logging.getLogger(__name__)


class FunctionCallingNode(BaseNode):
    """Function Calling节点 - 使用 llm.bind_tools 让AI主动选择和调用工具"""

    def __init__(self, llm=None):
        super().__init__(llm)
        self.tools = all_tools
        self.llm_with_tools = llm.bind_tools(self.tools) if llm else None
        self.tool_map = {t.name: t for t in self.tools}

    def _build_messages(self, state: ConversationState) -> list:
        """构建发送给 LLM 的消息列表"""
        system_message = (
            "你是一个智能客服助手。根据用户的问题和意图，选择合适的工具来获取所需数据。\n"
            "如果用户问题需要查询实时数据（订单、商品、用户信息、库存、物流、价格等），请调用对应的工具。\n"
            "如果不需要调用工具，直接回复即可。"
        )

        messages = [("system", system_message)]

        # 添加最近的对话历史作为上下文
        for turn in state.get("conversation_history", [])[-3:]:
            messages.append(("human", turn.get("user", "")))
            messages.append(("assistant", turn.get("assistant", "")))

        # 添加当前用户消息，附带意图信息
        intent = state.get("intent", "未知")
        user_msg = f"[用户意图: {intent}] {state['user_message']}"
        messages.append(("human", user_msg))

        return messages

    async def execute(self, state: ConversationState) -> ConversationState:
        """执行Function Calling"""
        # 不需要工具调用的意图，直接跳过
        skip_intents = {"问答", "文档分析", "工单", "购买指导"}
        if state.get("intent") in skip_intents or state.get("confidence", 0) < 0.6:
            state["tool_result"] = None
            state["tool_used"] = None
            logger.info(f"⚡ 跳过工具调用 (意图: {state.get('intent')})")
            return state

        try:
            # 构建消息并调用绑定了工具的 LLM
            messages = self._build_messages(state)
            response = await self.llm_with_tools.ainvoke(messages)

            # 解析 tool_calls
            if response.tool_calls:
                tool_results = []
                for tc in response.tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc["args"]
                    logger.info(f"调用工具: {tool_name}, 参数: {tool_args}")

                    try:
                        tool_fn = self.tool_map.get(tool_name)
                        if tool_fn is None:
                            logger.error(f"工具不存在: {tool_name}")
                            tool_results.append({
                                "tool": tool_name,
                                "error": f"工具不存在: {tool_name}"
                            })
                            continue

                        result = await tool_fn.ainvoke(tool_args)
                        tool_results.append({
                            "tool": tool_name,
                            "result": result
                        })
                        logger.info(f"工具调用成功: {tool_name}")
                    except Exception as e:
                        logger.error(f"工具调用失败: {tool_name}, 错误: {e}")
                        tool_results.append({
                            "tool": tool_name,
                            "error": str(e)
                        })

                state["tool_result"] = tool_results
                state["tool_used"] = ", ".join(
                    tc["name"] for tc in response.tool_calls
                )
            else:
                state["tool_result"] = None
                state["tool_used"] = None

        except Exception as e:
            logger.error(f"Function calling失败: {e}")
            state["tool_result"] = None
            state["tool_used"] = None

        return state
