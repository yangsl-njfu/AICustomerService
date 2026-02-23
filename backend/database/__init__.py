"""
数据库模块
"""
from .connection import engine, async_session, get_db
from .models import Base, User, Session, Message, Attachment, Ticket, TicketHistory, KnowledgeDocument, SystemConfig, AuditLog, Coupon, UserCoupon, Address, RefundRequest, RefundType, RefundStatus, RefundReason

__all__ = [
    "engine",
    "async_session",
    "get_db",
    "Base",
    "User",
    "Session",
    "Message",
    "Attachment",
    "Ticket",
    "TicketHistory",
    "KnowledgeDocument",
    "SystemConfig",
    "AuditLog",
    "Coupon",
    "UserCoupon",
    "Address",
    "RefundRequest",
    "RefundType",
    "RefundStatus",
    "RefundReason",
]
