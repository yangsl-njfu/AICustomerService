"""Standalone AI module HTTP app.

Run with:
    uvicorn ai_module.app:app --host 0.0.0.0 --port 8090 --reload
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel

from .engine import ai_engine


class AIChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    business_id: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    purchase_flow: Optional[Dict[str, Any]] = None
    aftersales_flow: Optional[Dict[str, Any]] = None


class AIChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    sources: Optional[List[Dict[str, Any]]] = None
    quick_actions: Optional[List[Dict[str, Any]]] = None
    recommended_products: Optional[List[str]] = None
    timestamp: str


router = APIRouter(prefix="/ai", tags=["ai-module"])


@router.get("/health")
async def health():
    return {"status": "healthy", "module": "ai"}


@router.post("/chat", response_model=AIChatResponse)
async def chat(request: AIChatRequest):
    try:
        result = await ai_engine.process_message(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message,
            attachments=request.attachments,
            purchase_flow=request.purchase_flow,
            aftersales_flow=request.aftersales_flow,
            business_id=request.business_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI module processing failed",
        ) from exc

    return AIChatResponse(
        response=result.get("response", ""),
        intent=result.get("intent"),
        confidence=result.get("confidence"),
        sources=result.get("sources"),
        quick_actions=result.get("quick_actions"),
        recommended_products=result.get("recommended_products"),
        timestamp=result.get("timestamp", datetime.now().isoformat()),
    )


@router.get("/businesses")
async def list_businesses():
    return {"businesses": ai_engine.list_businesses()}


@router.get("/businesses/{business_id}")
async def get_business_info(business_id: str):
    try:
        return ai_engine.get_business_info(business_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/plugins")
async def list_plugins(business_id: Optional[str] = None, group: Optional[str] = None):
    try:
        return ai_engine.list_plugins(business_id=business_id, group=group)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


app = FastAPI(
    title="AI Module Service",
    version="1.0.0",
    description="Standalone AI module endpoints",
)
app.include_router(router)

