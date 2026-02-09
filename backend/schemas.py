"""
Pydantic数据模式
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# 枚举类型
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class TicketStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class QuickActionType(str, Enum):
    """快速操作类型"""
    BUTTON = "button"      # 普通按钮
    LINK = "link"          # 链接
    FORM = "form"          # 表单
    PRODUCT = "product"    # 商品卡片


# 用户相关模式
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class AuthToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


# 会话相关模式
class SessionCreate(BaseModel):
    title: Optional[str] = "新对话"


class SessionResponse(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]
    message_count: int = 0
    is_active: bool = True
    
    class Config:
        from_attributes = True


# 消息相关模式
class AttachmentCreate(BaseModel):
    file_id: str
    file_name: str
    file_type: str
    file_size: int
    file_path: Optional[str] = None


class QuickAction(BaseModel):
    """快速操作按钮"""
    type: QuickActionType
    label: str
    action: str
    data: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class MessageCreate(BaseModel):
    session_id: str
    message: str
    attachments: Optional[List[Dict[str, Any]]] = None


class AttachmentResponse(BaseModel):
    id: str
    file_name: str
    file_type: str
    file_size: int
    mime_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default=None, validation_alias="meta", serialization_alias="metadata")
    created_at: datetime
    attachments: Optional[List[AttachmentResponse]] = None

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    message_id: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    intent: Optional[str] = None
    ticket_id: Optional[str] = None
    processing_time: Optional[float] = None
    quick_actions: Optional[List[QuickAction]] = None  # 新增快速操作按钮
    recommended_products: Optional[List[str]] = None   # 推荐商品ID列表


# 工单相关模式
class TicketCreate(BaseModel):
    title: str
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    category: Optional[str] = None


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_to: Optional[str] = None
    comment: Optional[str] = None


class TicketResponse(BaseModel):
    id: str
    user_id: str
    session_id: Optional[str]
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: Optional[str]
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TicketHistoryResponse(BaseModel):
    id: str
    ticket_id: str
    operator_id: Optional[str]
    action: str
    old_value: Optional[str]
    new_value: Optional[str]
    comment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# 文件相关模式
class FileUploadResponse(BaseModel):
    file_id: str
    file_name: str
    file_size: int
    file_type: str
    file_path: str
    file_path: str
    upload_url: str


# 知识库相关模式
class KnowledgeDocumentCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None


class KnowledgeDocumentResponse(BaseModel):
    id: str
    title: str
    description: str = ""
    file_name: str
    file_type: str
    file_size: int
    chunk_count: int
    created_by: str
    status: str = "active"
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# 系统配置相关模式
class SystemConfigUpdate(BaseModel):
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None
    retrieval_top_k: Optional[int] = None


class SystemConfigResponse(BaseModel):
    config_key: str
    config_value: str
    description: Optional[str]
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 管理后台相关模式
class SystemStatsResponse(BaseModel):
    total_users: int
    total_sessions: int
    total_messages: int
    total_tickets: int
    active_sessions: int
    pending_tickets: int


class ConversationSearchParams(BaseModel):
    user_id: Optional[str] = None
    keyword: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 20
    offset: int = 0


# 错误响应模式
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
