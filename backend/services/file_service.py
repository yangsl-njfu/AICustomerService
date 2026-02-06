"""
文件服务
"""
import os
import uuid
from typing import Optional
from pathlib import Path
from fastapi import UploadFile
import aiofiles
from pypdf import PdfReader
from docx import Document as DocxDocument
from PIL import Image
from config import settings


class FileService:
    """文件服务类"""
    
    def __init__(self):
        # 确保上传目录存在
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    
    def _get_file_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    def _is_allowed_file(self, filename: str) -> bool:
        """检查文件类型是否允许"""
        ext = self._get_file_extension(filename)
        return ext in settings.allowed_extensions_list
    
    async def upload_file(
        self,
        file: UploadFile,
        user_id: str,
        session_id: str
    ) -> dict:
        """上传文件"""
        # 检查文件类型
        if not self._is_allowed_file(file.filename):
            raise ValueError(f"不支持的文件类型。允许的类型：{', '.join(settings.allowed_extensions_list)}")
        
        # 检查文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        file.file.seek(0)  # 重置到文件开头
        
        if file_size > settings.MAX_FILE_SIZE:
            raise ValueError(f"文件大小超过限制（最大{settings.MAX_FILE_SIZE / 1024 / 1024}MB）")
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        ext = self._get_file_extension(file.filename)
        new_filename = f"{file_id}.{ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, new_filename)
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return {
            "file_id": file_id,
            "file_name": file.filename,
            "file_size": file_size,
            "file_type": ext,
            "file_path": file_path,
            "mime_type": file.content_type
        }
    
    async def get_file(self, file_id: str) -> Optional[bytes]:
        """获取文件内容"""
        # 查找文件
        for filename in os.listdir(settings.UPLOAD_DIR):
            if filename.startswith(file_id):
                file_path = os.path.join(settings.UPLOAD_DIR, filename)
                async with aiofiles.open(file_path, 'rb') as f:
                    return await f.read()
        return None
    
    def extract_text(self, file_path: str) -> str:
        """从文件提取文本"""
        ext = self._get_file_extension(file_path)
        
        try:
            if ext == 'pdf':
                return self._extract_pdf_text(file_path)
            elif ext in ['doc', 'docx']:
                return self._extract_docx_text(file_path)
            elif ext == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return ""
        except Exception as e:
            print(f"提取文本失败：{e}")
            return ""
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """从PDF提取文本"""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def _extract_docx_text(self, file_path: str) -> str:
        """从DOCX提取文本"""
        doc = DocxDocument(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def analyze_image(self, file_path: str) -> dict:
        """分析图片"""
        try:
            img = Image.open(file_path)
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode
            }
        except Exception as e:
            return {"error": str(e)}
