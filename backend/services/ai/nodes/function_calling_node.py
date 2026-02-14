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
        user_id = state.get("user_id", "")
        
        system_message = (
            "你是一个智能客服助手。根据用户的问题和意图，选择合适的工具来获取所需数据。\n"
            "【意图与工具的对应关系】：\n"
            "- 如果用户想要【个性化推荐】（根据我的浏览、猜我喜欢、有什么推荐），使用 get_personalized_recommendations 工具\n"
            "- 如果用户想要【商品推荐】或【搜索商品】（推荐python、推荐java项目、找一个vue项目），使用 search_products 工具，keyword参数填入技术关键词（如python、java、vue）\n"
            "- 如果用户想【查询订单】或【物流】，使用 query_order 或 get_logistics 工具\n"
            "- 如果用户想【获取用户信息】，使用 get_user_info 工具\n"
            "- 如果用户想【检查库存】或【计算价格】，使用 check_inventory 或 calculate_price 工具\n"
            "- 其他情况如果不需要调用工具，直接回复即可\n"
            f"当前用户ID: {user_id} (如果需要调用工具且需要用户ID，请使用此ID)"
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
        skip_intents = {"问答", "文档分析", "工单", "购买指导", "个性化推荐"}
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
                        if tool_name == "search_products":
                            logger.info(f"🎯 搜索结果: {len(result.get('products', []))} 个商品")
                            for p in result.get("products", [])[:3]:
                                logger.info(f"   - {p.get('title', '')[:30]} | tech: {p.get('tech_stack', [])}")
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
