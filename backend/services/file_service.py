"""
文件服务
"""
import os
import uuid
import asyncio
from typing import Optional
from pathlib import Path
from fastapi import UploadFile
import aiofiles
from pypdf import PdfReader
from docx import Document as DocxDocument
from PIL import Image
from config import settings
from .paddleocr_service import vision_llm_service


class FileService:
    """文件服务类"""
    
    def __init__(self):
        # 确保上传目录存在
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        # 存储待处理的图片分析任务
        self._pending_analysis: dict[str, asyncio.Task] = {}
    
    def _get_file_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    def _is_allowed_file(self, filename: str) -> bool:
        """检查文件类型是否允许"""
        ext = self._get_file_extension(filename)
        return ext in settings.allowed_extensions_list
    
    def _is_image_file(self, filename: str) -> bool:
        """检查是否为图片文件"""
        ext = self._get_file_extension(filename)
        return ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']
    
    async def upload_file(
        self,
        file: UploadFile,
        user_id: str,
        session_id: str
    ) -> dict:
        """上传文件"""
        print(f"[调试] upload_file 被调用: {file.filename}")
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
        
        # 初始化返回结果
        result = {
            "file_id": file_id,
            "file_name": file.filename,
            "file_size": file_size,
            "file_type": ext,
            "file_path": file_path,
            "mime_type": file.content_type,
            "extracted_text": None,  # 提取的文字内容
            "ocr_used": False,       # 是否使用了 OCR
            "analysis_pending": False  # 是否正在异步分析中
        }
        
        # 如果是图片文件且视觉LLM可用，启动异步分析任务
        is_image = self._is_image_file(file.filename)
        is_available = vision_llm_service.is_available()
        
        if is_image and is_available:
            # 标记为分析中，立即返回，不等待分析完成
            result["analysis_pending"] = True
            # 启动后台任务进行图片分析
            asyncio.create_task(self._analyze_image_async(file_id, file_path))
            print(f"[视觉LLM] 图片分析已启动异步任务: {file_id}")
        elif is_image and not is_available:
            print(f"[视觉LLM] 视觉LLM服务不可用，跳过图片分析")
        
        return result
    
    async def _analyze_image_async(self, file_id: str, file_path: str):
        """异步分析图片（后台任务）"""
        try:
            # 读取图片数据
            async with aiofiles.open(file_path, 'rb') as f:
                image_data = await f.read()
            
            # 分析图片意图和内容
            analysis = await vision_llm_service.analyze_image_intent(image_data)
            
            # 将分析结果保存到文件（可以通过另一个API获取）
            analysis_result = {
                "file_id": file_id,
                "extracted_text": analysis.get("extracted_text", ""),
                "ocr_used": True,
                "image_intent": analysis.get("intent", "其他"),
                "image_description": analysis.get("description", ""),
                "image_reasoning": analysis.get("reasoning", ""),
                "confidence": analysis.get("confidence", 0)
            }
            
            # 保存分析结果到临时文件
            analysis_path = f"{file_path}.analysis.json"
            import json
            async with aiofiles.open(analysis_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(analysis_result, ensure_ascii=False))
            
            print(f"[视觉LLM] 异步分析完成: {file_id}, 意图: {analysis_result['image_intent']}")
        except Exception as e:
            print(f"[视觉LLM] 异步分析失败: {e}")
    
    async def get_image_analysis(self, file_id: str) -> Optional[dict]:
        """获取图片分析结果"""
        # 查找分析结果文件
        for filename in os.listdir(settings.UPLOAD_DIR):
            if filename.startswith(file_id) and filename.endswith('.analysis.json'):
                analysis_path = os.path.join(settings.UPLOAD_DIR, filename)
                try:
                    import json
                    async with aiofiles.open(analysis_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        return json.loads(content)
                except Exception as e:
                    print(f"读取分析结果失败: {e}")
                    return None
        return None
    
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
