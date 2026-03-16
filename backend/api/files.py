"""File upload and secure retrieval endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import FileUploadResponse
from services.auth_service import AuthService
from services.file_service import FileService

router = APIRouter()
security = HTTPBearer(auto_error=False)
auth_service = AuthService()
file_service = FileService()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> str:
    try:
        auth_token = token or (credentials.credentials if credentials else None)
        if not auth_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing authentication token",
            )
        user = await auth_service.get_current_user(db, auth_token)
        return user.id
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = "",
    user_id: str = Depends(get_current_user_id),
):
    try:
        result = await file_service.upload_file(file, user_id, session_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return FileUploadResponse(
        file_id=result["file_id"],
        file_name=result["file_name"],
        file_size=result["file_size"],
        file_type=result["file_type"],
        upload_url=f"/api/files/{result['file_id']}",
        extracted_text=result.get("extracted_text"),
        ocr_used=result.get("ocr_used", False),
        analysis_pending=result.get("analysis_pending", False),
    )


@router.get("/{file_id}")
async def get_file(
    file_id: str,
    session_id: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
):
    content = await file_service.get_file(file_id, user_id=user_id, session_id=session_id)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="file not found",
        )

    return Response(content=content, media_type="application/octet-stream")


@router.get("/{file_id}/analysis")
async def get_file_analysis(
    file_id: str,
    session_id: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
):
    analysis = await file_service.get_image_analysis(file_id, user_id=user_id, session_id=session_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="analysis result not found",
        )
    return analysis
