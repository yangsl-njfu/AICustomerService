"""
Unified gateway for business-pack based AI access.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from config.loader import config_loader
from database import get_db
from services.ai.runtime import runtime_factory
from services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/gateway", tags=["gateway"])
security = HTTPBearer()
auth_service = AuthService()


class ChatRequest(BaseModel):
    business_id: str
    session_id: str
    message: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class ChatResponse(BaseModel):
    message_id: str
    response: str
    quick_actions: Optional[List[Dict[str, Any]]] = None
    intent: Optional[str] = None
    confidence: Optional[float] = None
    sources: Optional[List[Dict[str, Any]]] = None
    recommended_products: Optional[List[str]] = None
    timestamp: str


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> str:
    try:
        user = await auth_service.get_current_user(db, credentials.credentials)
        return user.id
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.post("/chat/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    authenticated_user_id: str = Depends(get_current_user_id),
):
    if request.user_id and request.user_id != authenticated_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="request user_id does not match the authenticated user",
        )

    try:
        runtime_factory.get_runtime(request.business_id)
        workflow = runtime_factory.get_workflow(request.business_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    try:
        result = await workflow.process_message(
            user_id=authenticated_user_id,
            session_id=request.session_id,
            message=request.message,
            attachments=request.attachments,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI gateway processing failed",
        ) from exc

    return ChatResponse(
        message_id=f"msg_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        response=result.get("response", ""),
        quick_actions=result.get("quick_actions"),
        intent=result.get("intent"),
        confidence=result.get("confidence"),
        sources=result.get("sources"),
        recommended_products=result.get("recommended_products"),
        timestamp=result.get("timestamp", datetime.now().isoformat()),
    )


@router.get("/businesses")
async def list_businesses(user_id: str = Depends(get_current_user_id)):
    businesses = []
    for business_id in config_loader.list_businesses():
        config = config_loader.get_config(business_id)
        if not config:
            continue

        businesses.append(
            {
                "business_id": business_id,
                "business_name": config.get("business_name", ""),
                "business_type": config.get("business_type", ""),
                "features": config.get("features", {}),
            }
        )

    return {"businesses": businesses}


@router.get("/businesses/{business_id}")
async def get_business_info(
    business_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        runtime = runtime_factory.get_runtime(business_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    info = runtime.get_business_info()
    info["plugins"] = runtime.list_plugins()
    return info


@router.get("/plugins")
async def list_plugins(
    business_id: Optional[str] = None,
    group: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
):
    try:
        runtime = runtime_factory.get_runtime(business_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return {
        "business_id": runtime.business_pack.business_id,
        "plugins": runtime.list_plugins(group=group),
    }
