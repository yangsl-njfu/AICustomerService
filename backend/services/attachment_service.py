"""
附件服务
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import os

from database.models import Attachment
from config import settings


class AttachmentService:
    """附件服务类"""

    async def save_attachments(
        self,
        db: AsyncSession,
        message_id: str,
        attachments: List
    ) -> List[Attachment]:
        """保存附件"""
        saved_attachments = []

        for att in attachments:
            # 支持 dict 或 Pydantic 对象
            if hasattr(att, 'dict'):
                # Pydantic 对象
                att_data = att.dict()
            elif hasattr(att, 'model_dump'):
                # Pydantic v2
                att_data = att.model_dump()
            else:
                # dict
                att_data = att

            # 使用前端传递的文件路径，如果没有则重新构建
            file_id = att_data.get('file_id', str(uuid.uuid4()))
            file_type = att_data.get('file_type', '')
            file_path = att_data.get('file_path') or os.path.join(settings.UPLOAD_DIR, f"{file_id}.{file_type}")

            attachment = Attachment(
                id=str(uuid.uuid4()),
                message_id=message_id,
                file_name=att_data.get('file_name', ''),
                file_type=file_type,
                file_size=att_data.get('file_size', 0),
                file_path=file_path,
                mime_type=self._get_mime_type(file_type)
            )
            db.add(attachment)
            saved_attachments.append(attachment)

        await db.commit()
        for att in saved_attachments:
            await db.refresh(att)

        return saved_attachments

    def _get_mime_type(self, file_type: str) -> str:
        """根据文件类型获取 MIME 类型"""
        mime_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'md': 'text/markdown',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
        }
        return mime_types.get(file_type.lower(), 'application/octet-stream')

    async def get_message_attachments(
        self,
        db: AsyncSession,
        message_id: str
    ) -> List[Attachment]:
        """获取消息的附件"""
        result = await db.execute(
            select(Attachment)
            .where(Attachment.message_id == message_id)
            .order_by(Attachment.created_at)
        )
        return result.scalars().all()
