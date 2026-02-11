"""
文档分析节点
"""
import logging
from .base import BaseNode
from ..state import ConversationState
from langchain_core.prompts import ChatPromptTemplate
from services.file_service import FileService

logger = logging.getLogger(__name__)
file_service = FileService()


class DocumentNode(BaseNode):
    """文档分析节点"""
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行文档分析"""
        logger.info(f"文档分析节点: attachments={len(state.get('attachments', []))}")
        
        attachment_texts = []
        attachment_names = []

        if state.get("attachments"):
            for att in state["attachments"]:
                file_path = att.get("file_path", "")
                file_name = att.get("file_name", "未知文件")
                if file_path:
                    text = file_service.extract_text(file_path)
                    if text:
                        attachment_texts.append(text[:8000])
                        attachment_names.append(file_name)

        if not attachment_texts:
            state["response"] = "我注意到您上传了文件，但无法读取文件内容。请确保文件格式正确（支持 PDF、Word、TXT 等格式）。"
            return state

        all_content = "\n\n---\n\n".join(attachment_texts)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的文档分析助手。用户上传了文档，请主动分析并提供详细的解读。

分析要求：
1. 首先介绍文档的类型和大致内容
2. 提取文档的核心要点和关键信息
3. 总结文档的主要结论或建议
4. 如果文档有结构（如标题、章节），请按结构组织回答
5. 使用清晰的格式（标题、 bullet points 等）
6. 语言友好、专业，像在向用户汇报分析结果

不要等待用户提问，主动提供全面的文档解读。"""),
            ("human", """用户上传的文档：{file_names}

文档内容：
{content}

请提供详细的文档分析和解读：""")
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(
                file_names=", ".join(attachment_names),
                content=all_content
            )
        )

        state["response"] = response.content
        state["sources"] = [{"type": "attachment", "files": attachment_names}]

        return state

    async def execute_stream(self, state: ConversationState):
        """流式执行文档分析，逐 token yield"""
        logger.info(f"文档分析节点(流式): attachments={len(state.get('attachments', []))}")

        attachment_texts = []
        attachment_names = []

        if state.get("attachments"):
            for att in state["attachments"]:
                file_path = att.get("file_path", "")
                file_name = att.get("file_name", "未知文件")
                if file_path:
                    text = file_service.extract_text(file_path)
                    if text:
                        attachment_texts.append(text[:8000])
                        attachment_names.append(file_name)

        if not attachment_texts:
            state["response"] = "我注意到您上传了文件，但无法读取文件内容。请确保文件格式正确（支持 PDF、Word、TXT 等格式）。"
            yield state["response"]
            return

        all_content = "\n\n---\n\n".join(attachment_texts)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的文档分析助手。用户上传了文档，请主动分析并提供详细的解读。

分析要求：
1. 首先介绍文档的类型和大致内容
2. 提取文档的核心要点和关键信息
3. 总结文档的主要结论或建议
4. 如果文档有结构（如标题、章节），请按结构组织回答
5. 使用清晰的格式（标题、 bullet points 等）
6. 语言友好、专业，像在向用户汇报分析结果

不要等待用户提问，主动提供全面的文档解读。"""),
            ("human", """用户上传的文档：{file_names}

文档内容：
{content}

请提供详细的文档分析和解读：""")
        ])

        messages = prompt.format_messages(
            file_names=", ".join(attachment_names),
            content=all_content
        )

        full_response = ""
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                full_response += chunk.content
                yield chunk.content

        state["response"] = full_response
        state["sources"] = [{"type": "attachment", "files": attachment_names}]

