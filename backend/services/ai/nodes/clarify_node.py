"""
澄清意图节点
"""
from .base import BaseNode
from ..state import ConversationState
from langchain_core.prompts import ChatPromptTemplate


class ClarifyNode(BaseNode):
    """澄清意图节点"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行意图澄清"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个友好的AI客服助手。用户的消息意图不够明确，请自然地询问用户需要什么帮助。
要求：
1. 回复要自然、友好，像真人对话
2. 简要列出可能的服务选项（问答、工单、产品咨询）
3. 邀请用户详细说明需求
4. 不要机械地列1、2、3，而是融入对话中"""),
            ("human", """用户消息：{message}
历史对话：{history}

请自然地询问用户需要什么帮助：""")
        ])

        history_str = "\n".join([
            f"用户：{turn['user']}\n助手：{turn['assistant']}"
            for turn in state["conversation_history"][-3:]
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(
                message=state["user_message"],
                history=history_str
            )
        )

        state["response"] = response.content
        return state

    async def execute_stream(self, state: ConversationState):
        """流式执行意图澄清，逐 token yield"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个友好的AI客服助手。用户的消息意图不够明确，请自然地询问用户需要什么帮助。
要求：
1. 回复要自然、友好，像真人对话
2. 简要列出可能的服务选项（问答、工单、产品咨询）
3. 邀请用户详细说明需求
4. 不要机械地列1、2、3，而是融入对话中"""),
            ("human", """用户消息：{message}
历史对话：{history}

请自然地询问用户需要什么帮助：""")
        ])

        history_str = "\n".join([
            f"用户：{turn['user']}\n助手：{turn['assistant']}"
            for turn in state["conversation_history"][-3:]
        ])

        messages = prompt.format_messages(
            message=state["user_message"],
            history=history_str
        )

        full_response = ""
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                full_response += chunk.content
                yield chunk.content

        state["response"] = full_response
