"""
问答节点。

这个节点同时承担两类能力：
1. 简单寒暄，直接返回固定回复，避免无意义地调用大模型。
2. 普通问答，按附件优先、知识库补充的方式组织检索增强输入。
"""
from __future__ import annotations

import re

from langchain_core.prompts import ChatPromptTemplate

from config import settings
from services.file_service import FileService
from services.knowledge_retriever import knowledge_retriever

from .base import BaseNode
from ..state import ConversationState

file_service = FileService()

_CHITCHAT_PATTERNS = re.compile(
    r"^(你好|您好|hello|hi|哈喽|在吗|你是谁|你叫什么|谢谢|感谢|好的|ok|再见|拜拜|早上好|晚上好)[!！。.?？]*$",
    re.IGNORECASE,
)

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """你是一个专业的 AI 客服助手。请基于提供的知识库内容和用户上传的附件回答问题。
要求：
1. 优先参考用户上传的附件内容。
2. 如果附件中没有相关信息，再参考知识库内容。
3. 回答要准确、简洁、有帮助。
4. 保持友好、专业的语气。
{conversation_summary_section}""",
        ),
        (
            "human",
            """知识库内容：
{docs}

附件内容：
{attachments}

历史对话：
{history}

用户问题：{question}""",
        ),
    ]
)

SIMPLE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个友好的 AI 客服助手，请简洁回答用户问题。"),
        ("human", "{question}"),
    ]
)


class QANode(BaseNode):
    """问答流程节点。"""

    def _quick_reply_for_chitchat(self, message: str) -> str | None:
        text = message.strip()
        if not text:
            return None

        if re.match(r"^(你好|您好|hello|hi|哈喽|早上好|晚上好)[!！。.?？]*$", text, re.IGNORECASE):
            return "您好，我在。您可以直接告诉我想咨询的问题，或者说出您的需求，我来帮您处理。"
        if re.match(r"^(谢谢|感谢|辛苦了|好的谢谢)[!！。.?？]*$", text, re.IGNORECASE):
            return "不客气，需要我继续帮您处理的话，直接告诉我就行。"
        if re.match(r"^(再见|拜拜)[!！。.?？]*$", text, re.IGNORECASE):
            return "好的，有需要再来找我。"
        return None

    def _is_chitchat(self, message: str, state: ConversationState) -> bool:
        if state.get("continue_previous_task"):
            return False
        text = message.strip()
        return bool(_CHITCHAT_PATTERNS.match(text)) or len(text) <= 4

    async def _prepare_messages(self, state: ConversationState):
        user_message = state["user_message"]

        if self._is_chitchat(user_message, state):
            state["retrieved_docs"] = []
            state["sources"] = []
            return SIMPLE_PROMPT.format_messages(question=user_message)

        attachment_texts = []
        for attachment in state.get("attachments") or []:
            file_path = attachment.get("file_path", "")
            if not file_path:
                continue
            text = file_service.extract_text(file_path)
            if text:
                attachment_texts.append(
                    f"【{attachment.get('file_name', '文件')}】\n{text[:5000]}"
                )

        docs = await knowledge_retriever.retrieve(
            query=user_message,
            collection_name="knowledge_base",
            top_k=settings.RETRIEVAL_TOP_K,
            use_hybrid=settings.RAG_USE_HYBRID_SEARCH,
            use_rerank=settings.RAG_USE_RERANK,
            use_query_rewrite=settings.RAG_USE_QUERY_REWRITE,
        )
        state["retrieved_docs"] = [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
        state["sources"] = [doc.metadata for doc in docs]

        docs_text = "\n\n".join(
            f"文档{i + 1}：{doc.page_content}" for i, doc in enumerate(docs)
        )
        attachment_content = "\n\n".join(attachment_texts) if attachment_texts else "无"
        history_text = "\n".join(
            f"用户：{turn['user']}\n助手：{turn['assistant']}"
            for turn in state["conversation_history"][-3:]
        )

        summary = state.get("conversation_summary", "")
        conversation_summary_section = f"\n对话历史摘要：\n{summary}" if summary else ""

        return RAG_PROMPT.format_messages(
            docs=docs_text,
            attachments=attachment_content,
            history=history_text,
            question=user_message,
            conversation_summary_section=conversation_summary_section,
        )

    async def execute(self, state: ConversationState) -> ConversationState:
        quick_reply = self._quick_reply_for_chitchat(state["user_message"])
        if quick_reply:
            state["retrieved_docs"] = []
            state["sources"] = []
            state["response"] = quick_reply
            return state

        messages = await self._prepare_messages(state)
        response = await self.llm.ainvoke(messages)
        state["response"] = response.content
        return state

    async def execute_stream(self, state: ConversationState):
        quick_reply = self._quick_reply_for_chitchat(state["user_message"])
        if quick_reply:
            state["retrieved_docs"] = []
            state["sources"] = []
            state["response"] = quick_reply
            yield quick_reply
            return

        messages = await self._prepare_messages(state)
        full_response = ""
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                full_response += chunk.content
                yield chunk.content
        state["response"] = full_response
