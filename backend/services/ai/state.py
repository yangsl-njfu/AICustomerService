"""
对话状态定义
"""
from typing import TypedDict, List, Dict, Optional, Any


class ConversationState(TypedDict):
    """对话状态"""
    # 输入
    user_message: str
    user_id: str
    session_id: str
    attachments: Optional[List[Dict]]
    
    # 上下文
    conversation_history: List[Dict[str, str]]
    user_profile: Dict
    
    # 处理过程
    intent: Optional[str]
    confidence: Optional[float]
    retrieved_docs: Optional[List[Dict]]
    tool_result: Optional[Any]  # Function Calling结果
    tool_used: Optional[str]    # 使用的工具名称
    
    # 输出
    response: str
    sources: Optional[List[Dict]]
    ticket_id: Optional[str]
    recommended_products: Optional[List[str]]
    quick_actions: Optional[List[Dict]]  # 快速操作按钮
    
    # 元数据
    timestamp: str
    processing_time: Optional[float]
