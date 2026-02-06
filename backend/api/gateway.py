"""
API Gateway
统一的API入口，支持多业务接入
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.loader import config_loader
from adapters import EcommerceAdapter
from plugins import plugin_manager
from services.ai.workflow import ai_workflow

router = APIRouter(prefix="/api/v1/gateway", tags=["gateway"])


class ChatRequest(BaseModel):
    """聊天请求"""
    business_id: str
    user_id: str
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict]] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    message_id: str
    response: str
    quick_actions: Optional[List[Dict]] = None
    intent: Optional[str] = None
    confidence: Optional[float] = None
    sources: Optional[List[Dict]] = None
    recommended_products: Optional[List[str]] = None
    timestamp: str


class BusinessAdapter:
    """业务适配器工厂"""
    
    _adapters: Dict[str, Any] = {}
    
    @classmethod
    def get_adapter(cls, business_id: str):
        """
        获取或创建业务适配器
        
        Args:
            business_id: 业务标识
            
        Returns:
            适配器实例
        """
        # 检查缓存
        if business_id in cls._adapters:
            return cls._adapters[business_id]
        
        # 加载配置
        config = config_loader.get_config(business_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"业务 {business_id} 未配置"
            )
        
        # 创建适配器
        adapter_class_name = config.get("adapter", {}).get("class", "")
        
        if adapter_class_name == "adapters.EcommerceAdapter":
            adapter = EcommerceAdapter(business_id, config)
        else:
            # 默认使用电商适配器
            adapter = EcommerceAdapter(business_id, config)
        
        # 缓存适配器
        cls._adapters[business_id] = adapter
        
        # 设置插件管理器的适配器
        plugin_manager.set_adapter(adapter)
        
        return adapter


@router.post("/chat/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    发送聊天消息
    
    Args:
        request: 聊天请求
        
    Returns:
        聊天响应
    """
    try:
        # 获取业务适配器
        adapter = BusinessAdapter.get_adapter(request.business_id)
        
        # 设置插件管理器的适配器
        plugin_manager.set_adapter(adapter)
        
        # 处理消息
        result = await ai_workflow.process_message(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message,
            attachments=request.attachments
        )
        
        # 构建响应
        message_id = f"msg_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        return ChatResponse(
            message_id=message_id,
            response=result.get("response", ""),
            quick_actions=None,  # TODO: 实现快速操作按钮
            intent=result.get("intent"),
            confidence=result.get("confidence"),
            sources=result.get("sources"),
            recommended_products=result.get("recommended_products"),
            timestamp=result.get("timestamp", datetime.now().isoformat())
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理消息失败: {str(e)}"
        )


@router.get("/businesses")
async def list_businesses():
    """
    列出所有已配置的业务
    
    Returns:
        业务列表
    """
    businesses = []
    for business_id in config_loader.list_businesses():
        config = config_loader.get_config(business_id)
        if config:
            businesses.append({
                "business_id": business_id,
                "business_name": config.get("business_name", ""),
                "business_type": config.get("business_type", ""),
                "features": config.get("features", {})
            })
    
    return {"businesses": businesses}


@router.get("/businesses/{business_id}")
async def get_business_info(business_id: str):
    """
    获取业务信息
    
    Args:
        business_id: 业务标识
        
    Returns:
        业务信息
    """
    config = config_loader.get_config(business_id)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"业务 {business_id} 未配置"
        )
    
    return {
        "business_id": business_id,
        "business_name": config.get("business_name", ""),
        "business_type": config.get("business_type", ""),
        "features": config.get("features", {}),
        "custom_intents": config.get("custom_intents", []),
        "plugins": config.get("plugins", [])
    }


@router.get("/plugins")
async def list_plugins():
    """
    列出所有可用插件
    
    Returns:
        插件列表
    """
    return {"plugins": plugin_manager.list_plugins()}
