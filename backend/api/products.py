"""
商品API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel
from database.connection import get_db
from services.product_service import ProductService, CategoryService
from services.auth_service import AuthService


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
            status_code=401,
            detail=str(e)
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户完整信息"""
    try:
        user = await auth_service.get_current_user(db, credentials.credentials)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )


# Pydantic模型
class ProductCreate(BaseModel):
    category_id: str
    title: str
    description: str
    price: float
    original_price: Optional[float] = None
    cover_image: Optional[str] = None
    demo_video: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    difficulty: str = "medium"


class ProductUpdate(BaseModel):
    category_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    cover_image: Optional[str] = None
    demo_video: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    difficulty: Optional[str] = None
    status: Optional[str] = None


class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0


# 分类相关API - 必须放在 /products/{product_id} 之前
@router.get("/products/categories")
async def get_categories(
    parent_id: Optional[str] = None,
    include_children: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """获取分类列表"""
    service = CategoryService(db)
    
    try:
        categories = await service.get_categories(
            parent_id=parent_id,
            include_children=include_children
        )
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/categories/{category_id}")
async def get_category(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取分类详情"""
    service = CategoryService(db)
    
    category = await service.get_category(category_id)
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    return category


@router.post("/products/categories")
async def create_category(
    category_data: CategoryCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建分类（管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    service = CategoryService(db)
    
    try:
        category = await service.create_category(**category_data.dict())
        
        return {
            "message": "分类创建成功",
            "category_id": category.id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 商品相关API
@router.get("/products")
async def get_products(
    keyword: Optional[str] = None,
    category_id: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    difficulty: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取商品列表"""
    service = ProductService(db)
    
    try:
        result = await service.search_products(
            keyword=keyword,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            difficulty=difficulty,
            status=status,
            sort_by=sort_by,
            order=order,
            page=page,
            page_size=page_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}")
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取商品详情"""
    service = ProductService(db)
    
    product = await service.get_product(product_id, increment_view=True)
    
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    return product


@router.post("/products")
async def create_product(
    product_data: ProductCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """发布商品（卖家）"""
    service = ProductService(db)
    
    try:
        product = await service.create_product(
            seller_id=user_id,
            **product_data.dict()
        )
        
        return {
            "message": "商品创建成功",
            "product_id": product.id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新商品"""
    service = ProductService(db)
    
    # 验证权限（只有卖家本人或管理员可以更新）
    product = await service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    if product["seller"]["id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权操作此商品")
    
    try:
        # 过滤掉None值
        update_data = {k: v for k, v in product_data.dict().items() if v is not None}
        
        updated_product = await service.update_product(product_id, **update_data)
        
        if not updated_product:
            raise HTTPException(status_code=404, detail="商品不存在")
        
        return {
            "message": "商品更新成功",
            "product_id": updated_product.id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除商品"""
    service = ProductService(db)
    
    # 验证权限
    product = await service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    if product["seller"]["id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权操作此商品")
    
    try:
        success = await service.delete_product(product_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="商品不存在")
        
        return {"message": "商品删除成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/products/{product_id}/seller")
async def get_seller_products(
    seller_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取卖家的商品列表"""
    service = ProductService(db)
    
    try:
        result = await service.search_products(
            seller_id=seller_id,
            status="published",
            page=page,
            page_size=page_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
