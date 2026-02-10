"""
问答节点
"""
import re
from .base import BaseNode
from ..state import ConversationState
from langchain_core.prompts import ChatPromptTemplate
from services.knowledge_retriever import knowledge_retriever
from services.file_service import FileService
from config import settings

file_service = FileService()

# 闲聊/打招呼关键词，不需要 RAG
_CHITCHAT_PATTERNS = re.compile(
    r'^(你好|hello|hi|嗨|在吗|在不在|你是谁|你叫什么|谢谢|感谢|好的|ok|再见|拜拜|嗯|哦)[\?？!！。~～.]*$',
    re.IGNORECASE
)

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的AI客服助手。基于提供的知识库内容和用户上传的附件回答用户问题。
要求：
1. 优先参考用户上传的附件内容回答问题
2. 如果附件中没有相关信息，再参考知识库内容
3. 回答要准确、简洁、有帮助
4. 保持友好专业的语气"""),
    ("human", """知识库内容：
{docs}

附件内容：
{attachments}

历史对话：
{history}

用户问题：{question}""")
])

SIMPLE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一个友好的AI客服助手，简洁回答用户问题。"),
    ("human", "{question}")
])


class QANode(BaseNode):
    """问答流程节点"""

    def _is_chitchat(self, message: str) -> bool:
        """判断是否是闲聊/打招呼"""
        return bool(_CHITCHAT_PATTERNS.match(message.strip())) or len(message.strip()) <= 4

    async def _prepare_messages(self, state: ConversationState):
        """准备 LLM 消息：闲聊走简单 prompt，其他走 RAG"""
        user_message = state["user_message"]

        if self._is_chitchat(user_message):
            state["retrieved_docs"] = []
            state["sources"] = []
            return SIMPLE_PROMPT.format_messages(question=user_message)

        # 提取附件
        attachment_texts = []
        if state.get("attachments"):
            for att in state["attachments"]:
                file_path = att.get("file_path", "")
                if file_path:
                    text = file_service.extract_text(file_path)
                    if text:
                        attachment_texts.append(f"【{att.get('file_name', '文件')}】\n{text[:5000]}")

        # RAG 检索
        docs = await knowledge_retriever.retrieve(
            query=user_message,
            collection_name="knowledge_base",
            top_k=settings.RETRIEVAL_TOP_K,
            use_hybrid=settings.RAG_USE_HYBRID_SEARCH,
            use_rerank=settings.RAG_USE_RERANK,
            use_query_rewrite=settings.RAG_USE_QUERY_REWRITE
        )
        state["retrieved_docs"] = [{"content": d.page_content, "metadata": d.metadata} for d in docs]
        state["sources"] = [d.metadata for d in docs]

        docs_text = "\n\n".join([f"文档{i+1}：{d.page_content}" for i, d in enumerate(docs)])
        attachment_content = "\n\n".join(attachment_texts) if attachment_texts else "无"
        history_str = "\n".join([
            f"用户：{t['user']}\n助手：{t['assistant']}"
            for t in state["conversation_history"][-3:]
        ])

        return RAG_PROMPT.format_messages(
            docs=docs_text, attachments=attachment_content,
            history=history_str, question=user_message
        )

    async def execute(self, state: ConversationState) -> ConversationState:
        """非流式执行"""
        messages = await self._prepare_messages(state)
        response = await self.llm.ainvoke(messages)
        state["response"] = response.content
        return state

    async def execute_stream(self, state: ConversationState):
        """流式执行，逐 token yield"""
        messages = await self._prepare_messages(state)
        full_response = ""
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                full_response += chunk.content
                yield chunk.content
        state["response"] = full_response
