"""
知识库API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database import get_db
from schemas import KnowledgeDocumentResponse, KnowledgeDocumentCreate
from services.auth_service import AuthService
from services.knowledge_service import knowledge_service

router = APIRouter()
security = HTTPBearer()
auth_service = AuthService()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> str:
    """获取当前用户ID"""
    try:
        user = await auth_service.get_current_user(db, credentials.credentials)
        return user.id
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/upload", response_model=KnowledgeDocumentResponse)
async def upload_knowledge_document(
    file: UploadFile = File(..., description="知识库文档文件（支持 pdf, doc, docx, txt, md）"),
    title: Optional[str] = Form(None, description="文档标题"),
    description: Optional[str] = Form(None, description="文档描述"),
    user_id: str = Depends(get_current_user_id)
):
    """
    上传文档到知识库

    支持格式：PDF、Word、TXT、Markdown
    文件会被自动解析、分割并添加到向量数据库
    """
    try:
        result = await knowledge_service.upload_document(
            file=file,
            user_id=user_id,
            title=title,
            description=description
        )

        return KnowledgeDocumentResponse(
            id=result["doc_id"],
            title=result["title"],
            description=result["description"],
            file_name=result["file_name"],
            file_type=result["file_type"],
            file_size=result["file_size"],
            chunk_count=result["chunk_count"],
            created_by=user_id,
            status="active"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败：{str(e)}"
        )


@router.get("/documents", response_model=List[KnowledgeDocumentResponse])
async def list_knowledge_documents(
    user_id: str = Depends(get_current_user_id)
):
    """获取知识库文档列表"""
    try:
        documents = await knowledge_service.list_documents()

        return [
            KnowledgeDocumentResponse(
                id=doc["doc_id"],
                title=doc["file_name"],
                description="",
                file_name=doc["file_name"],
                file_type=doc["file_type"],
                file_size=doc["file_size"],
                chunk_count=0,
                created_by=user_id,
                status="active"
            )
            for doc in documents
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档列表失败：{str(e)}"
        )


@router.delete("/documents/{doc_id}")
async def delete_knowledge_document(
    doc_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """删除知识库文档"""
    try:
        success = await knowledge_service.delete_document(doc_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在或删除失败"
            )

        return {"message": "文档删除成功", "doc_id": doc_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败：{str(e)}"
        )
