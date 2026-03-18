"""
文档分析节点
"""
import logging
import asyncio
from .base import BaseNode
from ..state import ConversationState
from langchain_core.prompts import ChatPromptTemplate
from services.file_service import FileService
from services.paddleocr_service import vision_llm_service

logger = logging.getLogger(__name__)
file_service = FileService()

IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}


async def _get_attachment_text(att: dict) -> tuple[str, str, dict]:
    """获取附件文本内容，返回“正文、展示名、附加信息”。"""
    file_path = att.get("file_path", "")
    file_name = att.get("file_name", "未知文件")
    file_id = att.get("file_id", "")
    ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''
    metadata = {}

    # 1. 优先使用已提取的文字结果（来自视觉大模型）。
    extracted_text = att.get("extracted_text")
    if extracted_text:
        logger.info(f"使用已提取的图片文字: {file_name}")
        metadata = {
            "image_intent": att.get("image_intent"),
            "image_description": att.get("image_description"),
        }
        return extracted_text[:8000], f"{file_name} (图片文字已提取)", metadata

    # 2. 图片文件：先尝试读取异步分析结果，再兜底调用视觉大模型。
    if ext in IMAGE_EXTENSIONS:
        # 2a. 尝试读取异步分析结果（最多等2秒）
        if file_id:
            for _ in range(4):
                analysis = await file_service.get_image_analysis(file_id)
                if analysis and analysis.get("extracted_text"):
                    logger.info(f"从异步分析结果获取图片文字: {file_name}")
                    metadata = {
                        "image_intent": analysis.get("image_intent"),
                        "image_description": analysis.get("image_description"),
                    }
                    return analysis["extracted_text"][:8000], f"{file_name} (图片文字已提取)", metadata
                await asyncio.sleep(0.5)

        # 2b. 兜底：直接调用视觉大模型提取文字。
        if file_path and vision_llm_service.is_available():
            logger.info(f"直接调用视觉LLM提取图片文字: {file_name}")
            text = await vision_llm_service.extract_text_from_image_file(file_path)
            if text:
                return text[:8000], f"{file_name} (图片文字已提取)", metadata

        logger.warning(f"无法提取图片文字: {file_name}")
        return "", "", metadata

    # 3. 非图片文件：直接提取
    if file_path:
        text = file_service.extract_text(file_path)
        if text:
            return text[:8000], file_name, metadata

    return "", "", metadata


class DocumentNode(BaseNode):
    """文档分析节点"""

    SYSTEM_PROMPT = """你是一个智能客服助手，服务于一个软件/毕业设计项目销售平台。
用户上传了文件或图片，请结合平台业务场景来分析和回复。

平台业务：销售各类软件项目、毕业设计、课程设计源码（Java、Python、Vue、SpringBoot等技术栈）。

回复策略：
- 如果是商品截图/商品页面：识别出商品信息，主动介绍该商品的特点，询问用户是否需要了解更多详情或购买
- 如果是订单截图/支付截图：识别订单信息，询问用户遇到了什么问题，主动提供帮助
- 如果是错误截图/bug截图：分析错误内容，提供可能的解决方案或建议提交工单
- 如果是技术文档/代码截图：结合平台商品进行解读，看是否与某个项目相关
- 如果是其他类型文档：提取关键信息并给出专业解读

要求：
1. 回复要贴合客服场景，不要做纯粹的文档分析报告
2. 主动引导用户下一步操作（如查看商品、下单、提交工单等）
3. 语言亲切专业，像真人客服一样交流
4. 如果能识别出具体商品，主动关联平台商品信息"""

    def _build_prompt(self, file_names, content, user_message, image_context):
        """构建发送给模型的消息列表。"""
        human_msg = f"用户上传的文件：{file_names}\n\n文件内容：\n{content}"
        if user_message:
            human_msg = f"用户消息：{user_message}\n\n{human_msg}"
        if image_context:
            human_msg += f"\n\n图片分析参考：{image_context}"
        human_msg += "\n\n请结合平台业务场景回复用户："

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", human_msg)
        ])
        return prompt.format_messages()

    async def execute(self, state: ConversationState) -> ConversationState:
        """执行文档分析"""
        logger.info(f"文档分析节点: attachments={len(state.get('attachments', []))}")

        attachment_texts = []
        attachment_names = []
        image_context_parts = []

        if state.get("attachments"):
            for att in state["attachments"]:
                text, name, metadata = await _get_attachment_text(att)
                if text:
                    attachment_texts.append(text)
                    attachment_names.append(name)
                if metadata.get("image_intent"):
                    image_context_parts.append(
                        f"意图={metadata['image_intent']}, 描述={metadata.get('image_description', '')}"
                    )

        if not attachment_texts:
            state["response"] = "我注意到您上传了文件，但无法读取文件内容。请确保文件格式正确（支持 PDF、Word、TXT、图片等格式）。"
            return state

        all_content = "\n\n---\n\n".join(attachment_texts)
        user_message = state.get("user_message", "").strip()
        image_context = "; ".join(image_context_parts) if image_context_parts else ""

        messages = self._build_prompt(
            ", ".join(attachment_names), all_content, user_message, image_context
        )
        response = await self.llm.ainvoke(messages)

        state["response"] = response.content
        state["sources"] = [{"type": "attachment", "files": attachment_names}]
        return state

    async def execute_stream(self, state: ConversationState):
        """以流式方式执行文档分析，逐字输出结果。"""
        logger.info(f"文档分析节点(流式): attachments={len(state.get('attachments', []))}")

        attachment_texts = []
        attachment_names = []
        image_context_parts = []

        if state.get("attachments"):
            for att in state["attachments"]:
                text, name, metadata = await _get_attachment_text(att)
                if text:
                    attachment_texts.append(text)
                    attachment_names.append(name)
                if metadata.get("image_intent"):
                    image_context_parts.append(
                        f"意图={metadata['image_intent']}, 描述={metadata.get('image_description', '')}"
                    )

        if not attachment_texts:
            state["response"] = "我注意到您上传了文件，但无法读取文件内容。请确保文件格式正确（支持 PDF、Word、TXT、图片等格式）。"
            yield state["response"]
            return

        all_content = "\n\n---\n\n".join(attachment_texts)
        user_message = state.get("user_message", "").strip()
        image_context = "; ".join(image_context_parts) if image_context_parts else ""

        messages = self._build_prompt(
            ", ".join(attachment_names), all_content, user_message, image_context
        )

        full_response = ""
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                full_response += chunk.content
                yield chunk.content

        state["response"] = full_response
        state["sources"] = [{"type": "attachment", "files": attachment_names}]

