"""
Function Calling节点
"""
import logging
import json
from .base import BaseNode
from ..state import ConversationState
from langchain_core.prompts import ChatPromptTemplate
from services.function_tools import function_tool_manager

logger = logging.getLogger(__name__)


class FunctionCallingNode(BaseNode):
    """Function Calling节点 - 让AI主动选择和调用工具"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行Function Calling"""
        # 获取可用工具
        tools_schema = function_tool_manager.get_tools_schema()
        
        # 让LLM选择要调用的工具
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个工具选择助手。根据用户问题和意图，判断是否需要调用工具来获取数据。

可用工具：
{tools}

规则：
1. 如果用户问题需要查询实时数据（订单、商品、用户信息等），选择合适的工具
2. 如果用户问题是一般性咨询或文档分析，不需要调用工具
3. 可以同时调用多个工具（返回工具列表）
4. 仔细提取用户问题中的参数

如果需要调用工具，返回JSON格式：
{{"tools": [{{"tool": "工具名称", "parameters": {{参数}}}}]}}

如果不需要调用工具，返回：
{{"tools": []}}"""),
            ("human", """用户问题：{question}
识别的意图：{intent}
历史对话：{history}

请判断是否需要调用工具：""")
        ])
        
        tools_text = "\n".join([
            f"- {tool['name']}: {tool['description']}\n  参数: {json.dumps(tool['parameters'], ensure_ascii=False)}"
            for tool in tools_schema
        ])
        
        history_str = "\n".join([
            f"用户：{turn['user']}\n助手：{turn['assistant']}"
            for turn in state["conversation_history"][-3:]
        ])
        
        try:
            response = await self.llm.ainvoke(
                prompt.format_messages(
                    tools=tools_text,
                    question=state["user_message"],
                    intent=state.get("intent", "未知"),
                    history=history_str
                )
            )
            
            result = json.loads(response.content)
            tools_to_call = result.get("tools", [])
            
            if tools_to_call:
                # 调用工具
                tool_results = []
                for tool_call in tools_to_call:
                    tool_name = tool_call.get("tool")
                    parameters = tool_call.get("parameters", {})
                    
                    logger.info(f"调用工具: {tool_name}, 参数: {parameters}")
                    
                    try:
                        tool_result = await function_tool_manager.execute(
                            tool_name, **parameters
                        )
                        tool_results.append({
                            "tool": tool_name,
                            "result": tool_result
                        })
                        logger.info(f"工具调用成功: {tool_name}")
                    except Exception as e:
                        logger.error(f"工具调用失败: {tool_name}, 错误: {e}")
                        tool_results.append({
                            "tool": tool_name,
                            "error": str(e)
                        })
                
                state["tool_result"] = tool_results
                state["tool_used"] = ", ".join([t["tool"] for t in tools_to_call])
            else:
                state["tool_result"] = None
                state["tool_used"] = None
        
        except Exception as e:
            logger.error(f"Function calling失败: {e}")
            state["tool_result"] = None
            state["tool_used"] = None
        
        return state
