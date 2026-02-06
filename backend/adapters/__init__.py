"""
业务适配器模块
提供统一的业务系统接口抽象
"""
from .base import BusinessAdapter
from .ecommerce import EcommerceAdapter

__all__ = ["BusinessAdapter", "EcommerceAdapter"]
