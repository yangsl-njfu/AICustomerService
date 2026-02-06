"""
初始化测试数据脚本
"""
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import engine, Base
from database.models import User, Category, Product, ProductDifficulty, ProductStatus
from services.auth_service import AuthService
from datetime import datetime

auth_service = AuthService()


async def init_database():
    """初始化数据库表"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建成功")


async def create_test_users(session: AsyncSession):
    """创建测试用户"""
    users_data = [
        {"username": "admin", "password": "admin123", "email": "admin@example.com", "role": "admin"},
        {"username": "buyer1", "password": "buyer123", "email": "buyer1@example.com", "role": "user"},
        {"username": "seller1", "password": "seller123", "email": "seller1@example.com", "role": "user"},
        {"username": "seller2", "password": "seller123", "email": "seller2@example.com", "role": "user"},
    ]
    
    created_users = {}
    for user_data in users_data:
        # 检查用户是否已存在
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == user_data["username"])
        )
        existing_user = result.scalar_one_or_none()
        
        if not existing_user:
            password_hash = auth_service.hash_password(user_data["password"])
            user = User(
                id=str(uuid.uuid4()),
                username=user_data["username"],
                password_hash=password_hash,
                email=user_data["email"],
                role=user_data["role"],
                is_active=True
            )
            session.add(user)
            created_users[user_data["username"]] = user
            print(f"✅ 创建用户: {user_data['username']}")
        else:
            created_users[user_data["username"]] = existing_user
            print(f"ℹ️  用户已存在: {user_data['username']}")
    
    await session.commit()
    return created_users


async def create_test_categories(session: AsyncSession):
    """创建测试分类"""
    categories_data = [
        {"name": "计算机类", "description": "计算机相关毕业设计", "icon": "computer", "sort_order": 1},
        {"name": "电子类", "description": "电子工程相关毕业设计", "icon": "electronics", "sort_order": 2},
        {"name": "管理类", "description": "管理系统相关毕业设计", "icon": "management", "sort_order": 3},
    ]
    
    created_categories = {}
    for cat_data in categories_data:
        from sqlalchemy import select
        result = await session.execute(
            select(Category).where(Category.name == cat_data["name"])
        )
        existing_cat = result.scalar_one_or_none()
        
        if not existing_cat:
            category = Category(
                id=str(uuid.uuid4()),
                name=cat_data["name"],
                description=cat_data["description"],
                icon=cat_data["icon"],
                sort_order=cat_data["sort_order"]
            )
            session.add(category)
            created_categories[cat_data["name"]] = category
            print(f"✅ 创建分类: {cat_data['name']}")
        else:
            created_categories[cat_data["name"]] = existing_cat
            print(f"ℹ️  分类已存在: {cat_data['name']}")
    
    await session.commit()
    return created_categories


async def create_test_products(session: AsyncSession, users: dict, categories: dict):
    """创建测试商品"""
    products_data = [
        {
            "title": "基于Vue3的在线商城系统",
            "description": "完整的电商平台，包含前后端代码、数据库设计、部署文档。技术栈：Vue3 + TypeScript + FastAPI + MySQL。功能包括：用户注册登录、商品浏览、购物车、订单管理、支付集成、后台管理等。",
            "price": 29900,  # 299.00元，存储为分
            "original_price": 39900,
            "cover_image": "https://picsum.photos/400/300?random=1",
            "tech_stack": ["Vue3", "TypeScript", "FastAPI", "MySQL"],
            "difficulty": ProductDifficulty.MEDIUM,
            "status": ProductStatus.PUBLISHED,
            "seller": "seller1",
            "category": "计算机类",
            "view_count": 1234,
            "sales_count": 156,
            "rating": 480,  # 4.80，存储为 rating * 100
            "review_count": 89
        },
        {
            "title": "Python数据分析系统",
            "description": "基于Python的数据分析平台，包含数据采集、清洗、可视化等功能。技术栈：Python + Pandas + Matplotlib + Django。支持多种数据源导入，提供丰富的图表展示。",
            "price": 19900,
            "original_price": 29900,
            "cover_image": "https://picsum.photos/400/300?random=2",
            "tech_stack": ["Python", "Pandas", "Matplotlib", "Django"],
            "difficulty": ProductDifficulty.EASY,
            "status": ProductStatus.PUBLISHED,
            "seller": "seller1",
            "category": "计算机类",
            "view_count": 856,
            "sales_count": 98,
            "rating": 460,
            "review_count": 67
        },
        {
            "title": "React Native移动应用",
            "description": "跨平台移动应用开发，包含iOS和Android版本。技术栈：React Native + Redux + Node.js。实现了用户认证、数据同步、推送通知等核心功能。",
            "price": 39900,
            "original_price": 49900,
            "cover_image": "https://picsum.photos/400/300?random=3",
            "tech_stack": ["React Native", "Redux", "Node.js"],
            "difficulty": ProductDifficulty.HARD,
            "status": ProductStatus.PUBLISHED,
            "seller": "seller2",
            "category": "计算机类",
            "view_count": 2341,
            "sales_count": 234,
            "rating": 490,
            "review_count": 178
        },
        {
            "title": "企业人事管理系统",
            "description": "完整的人事管理系统，包含员工管理、考勤、薪资等模块。技术栈：Spring Boot + Vue + MySQL。支持组织架构管理、权限控制、报表导出等功能。",
            "price": 24900,
            "original_price": 34900,
            "cover_image": "https://picsum.photos/400/300?random=4",
            "tech_stack": ["Spring Boot", "Vue", "MySQL"],
            "difficulty": ProductDifficulty.MEDIUM,
            "status": ProductStatus.PUBLISHED,
            "seller": "seller2",
            "category": "管理类",
            "view_count": 1567,
            "sales_count": 123,
            "rating": 470,
            "review_count": 95
        },
        {
            "title": "智能家居控制系统",
            "description": "基于物联网的智能家居系统，包含硬件设计和软件开发。技术栈：Arduino + Python + MQTT。可控制灯光、温度、安防等设备，支持语音控制和远程管理。",
            "price": 34900,
            "original_price": 44900,
            "cover_image": "https://picsum.photos/400/300?random=5",
            "tech_stack": ["Arduino", "Python", "MQTT"],
            "difficulty": ProductDifficulty.HARD,
            "status": ProductStatus.PUBLISHED,
            "seller": "seller1",
            "category": "电子类",
            "view_count": 987,
            "sales_count": 67,
            "rating": 450,
            "review_count": 45
        },
        {
            "title": "微信小程序商城",
            "description": "完整的微信小程序电商解决方案，包含商品展示、购物车、订单、支付等功能。技术栈：微信小程序 + Node.js + MongoDB。",
            "price": 27900,
            "original_price": 37900,
            "cover_image": "https://picsum.photos/400/300?random=6",
            "tech_stack": ["微信小程序", "Node.js", "MongoDB"],
            "difficulty": ProductDifficulty.MEDIUM,
            "status": ProductStatus.PUBLISHED,
            "seller": "seller1",
            "category": "计算机类",
            "view_count": 1456,
            "sales_count": 189,
            "rating": 475,
            "review_count": 112
        },
        {
            "title": "在线教育平台",
            "description": "功能完善的在线教育系统，支持视频课程、直播教学、作业提交、考试测评等。技术栈：Vue3 + Spring Boot + MySQL + Redis。",
            "price": 35900,
            "original_price": 45900,
            "cover_image": "https://picsum.photos/400/300?random=7",
            "tech_stack": ["Vue3", "Spring Boot", "MySQL", "Redis"],
            "difficulty": ProductDifficulty.HARD,
            "status": ProductStatus.PUBLISHED,
            "seller": "seller2",
            "category": "管理类",
            "view_count": 2103,
            "sales_count": 267,
            "rating": 485,
            "review_count": 201
        },
        {
            "title": "图书管理系统",
            "description": "简洁实用的图书管理系统，包含图书借阅、归还、查询、统计等功能。技术栈：Java + JSP + MySQL。适合初学者学习。",
            "price": 15900,
            "original_price": 25900,
            "cover_image": "https://picsum.photos/400/300?random=8",
            "tech_stack": ["Java", "JSP", "MySQL"],
            "difficulty": ProductDifficulty.EASY,
            "status": ProductStatus.PUBLISHED,
            "seller": "seller1",
            "category": "管理类",
            "view_count": 678,
            "sales_count": 87,
            "rating": 440,
            "review_count": 56
        }
    ]
    
    for prod_data in products_data:
        from sqlalchemy import select
        result = await session.execute(
            select(Product).where(Product.title == prod_data["title"])
        )
        existing_prod = result.scalar_one_or_none()
        
        if not existing_prod:
            product = Product(
                id=str(uuid.uuid4()),
                seller_id=users[prod_data["seller"]].id,
                category_id=categories[prod_data["category"]].id,
                title=prod_data["title"],
                description=prod_data["description"],
                price=prod_data["price"],
                original_price=prod_data["original_price"],
                cover_image=prod_data["cover_image"],
                tech_stack=prod_data["tech_stack"],
                difficulty=prod_data["difficulty"],
                status=prod_data["status"],
                view_count=prod_data["view_count"],
                sales_count=prod_data["sales_count"],
                rating=prod_data["rating"],
                review_count=prod_data["review_count"]
            )
            session.add(product)
            print(f"✅ 创建商品: {prod_data['title']}")
        else:
            print(f"ℹ️  商品已存在: {prod_data['title']}")
    
    await session.commit()


async def main():
    """主函数"""
    print("开始初始化数据库...")
    
    # 初始化数据库表
    await init_database()
    
    # 创建会话
    from database.connection import async_session
    async with async_session() as session:
        # 创建测试用户
        users = await create_test_users(session)
        
        # 创建测试分类
        categories = await create_test_categories(session)
        
        # 创建测试商品
        await create_test_products(session, users, categories)
    
    print("\n✅ 所有测试数据初始化完成！")
    print("\n可用的测试账户：")
    print("  管理员: admin / admin123")
    print("  买家: buyer1 / buyer123")
    print("  卖家: seller1 / seller123")
    print("  卖家: seller2 / seller123")


if __name__ == "__main__":
    asyncio.run(main())
