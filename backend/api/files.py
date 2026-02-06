"""
文件API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import FileUploadResponse
from services.auth_service import AuthService
from services.file_service import FileService

router = APIRouter()
security = HTTPBearer()
auth_service = AuthService()
file_service = FileService()


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


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = "",
    user_id: str = Depends(get_current_user_id)
):
    """上传文件"""
    try:
        result = await file_service.upload_file(file, user_id, session_id)
        return FileUploadResponse(
            file_id=result["file_id"],
            file_name=result["file_name"],
            file_size=result["file_size"],
            file_type=result["file_type"],
            file_path=result["file_path"],
            upload_url=f"/api/files/{result['file_id']}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{file_id}")
async def get_file(
    file_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """获取文件"""
    content = await file_service.get_file(file_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    return Response(content=content, media_type="application/octet-stream")
