"""
问答节点
"""
from .base import BaseNode
from ..state import ConversationState
from langchain_core.prompts import ChatPromptTemplate
from services.knowledge_retriever import knowledge_retriever
from services.file_service import FileService
from config import settings

file_service = FileService()


class QANode(BaseNode):
    """问答流程节点"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行问答流程"""
        # 提取附件内容
        attachment_texts = []
        if state.get("attachments"):
            for att in state["attachments"]:
                file_path = att.get("file_path", "")
                if file_path:
                    text = file_service.extract_text(file_path)
                    if text:
                        attachment_texts.append(f"【附件：{att.get('file_name', '未知文件')}】\n{text[:5000]}")

        # 检索相关文档 - 使用高级RAG
        docs = await knowledge_retriever.retrieve(
            query=state["user_message"],
            collection_name="knowledge_base",
            top_k=settings.RETRIEVAL_TOP_K,
            use_hybrid=settings.RAG_USE_HYBRID_SEARCH,
            use_rerank=settings.RAG_USE_RERANK,
            use_query_rewrite=settings.RAG_USE_QUERY_REWRITE
        )

        state["retrieved_docs"] = [
            {"content": doc.page_content, "metadata": doc.metadata}
            for doc in docs
        ]

        # 生成回答
        docs_text = "\n\n".join([f"文档{i+1}：{doc.page_content}" for i, doc in enumerate(docs)])
        attachment_content = "\n\n".join(attachment_texts) if attachment_texts else "无附件"
        history_str = "\n".join([
            f"用户：{turn['user']}\n助手：{turn['assistant']}"
            for turn in state["conversation_history"][-3:]
        ])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的AI客服助手。基于提供的知识库内容和用户上传的附件回答用户问题。
要求：
1. 优先参考用户上传的附件内容回答问题
2. 如果附件中有相关信息，详细解释附件内容
3. 如果附件中没有相关信息，再参考知识库内容
4. 回答要准确、简洁、有帮助
5. 引用知识库来源或附件名称
6. 保持友好专业的语气"""),
            ("human", """知识库内容：
{docs}

用户上传的附件内容：
{attachments}

历史对话：
{history}

用户问题：{question}

请基于附件和知识库内容回答：""")
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(
                docs=docs_text,
                attachments=attachment_content,
                history=history_str,
                question=state["user_message"]
            )
        )

        state["response"] = response.content
        state["sources"] = [doc.metadata for doc in docs]

        return state
