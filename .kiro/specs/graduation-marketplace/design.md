# 设计文档：智能毕业设计交易平台

## 概述

智能毕业设计交易平台是一个集成了 AI 智能客服的电商平台，专注于毕业设计作品的交易。系统采用前后端分离架构，保留原有 AI 客服系统的核心功能，并扩展电商业务模块。

**核心技术栈：**
- 前端：Vue 3 + TypeScript + Vite + Pinia
- 后端：FastAPI + Python 3.10+
- AI 框架：LangChain 1.2.7 + LangGraph 1.0.7
- 数据库：SQLite/MySQL + Chroma + Redis

**设计原则：**
1. 模块化：电商模块与 AI 模块解耦
2. 可复用：保留原有 AI 客服代码
3. 可扩展：支持新增商品类型和功能
4. 高性能：使用缓存和异步处理
5. 用户友好：简洁直观的界面设计

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    前端层 (Vue 3)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 商品展示 │ │ 购物车   │ │ 订单管理 │ │ AI客服   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 卖家中心 │ │ 用户中心 │ │ 评价系统 │ │ 管理后台 │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                          ↓ HTTP/SSE
┌─────────────────────────────────────────────────────────────┐
│                  API 网关层 (FastAPI)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 商品API  │ │ 订单API  │ │ 支付API  │ │ AI客服API│       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    业务逻辑层                                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  电商核心模块    │  │  AI客服模块      │                │
│  │  - 商品管理      │  │  - LangGraph工作流│               │
│  │  - 订单处理      │  │  - 意图识别      │                │
│  │  - 支付集成      │  │  - 知识库检索    │                │
│  │  - 评价系统      │  │  - 智能推荐      │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    数据存储层                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  SQLite  │ │  Chroma  │ │  Redis   │ │ 文件存储 │       │
│  │(业务数据)│ │(AI知识库)│ │ (缓存)   │ │(商品图片)│       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 数据库设计

### 新增表结构

#### 1. categories 表（商品分类）

```sql
CREATE TABLE categories (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id VARCHAR(36),
    description TEXT,
    icon VARCHAR(200),
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE,
    INDEX idx_parent (parent_id)
);
```

#### 2. products 表（商品）

```sql
CREATE TABLE products (
    id VARCHAR(36) PRIMARY KEY,
    seller_id VARCHAR(36) NOT NULL,
    category_id VARCHAR(36) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2),
    cover_image VARCHAR(500),
    demo_video VARCHAR(500),
    tech_stack JSON,
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    status ENUM('draft', 'pending', 'published', 'rejected', 'sold_out') DEFAULT 'draft',
    view_count INT DEFAULT 0,
    sales_count INT DEFAULT 0,
    rating DECIMAL(3, 2) DEFAULT 0.00,
    review_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    INDEX idx_category (category_id),
    INDEX idx_seller (seller_id),
    INDEX idx_status (status),
    INDEX idx_price (price),
    FULLTEXT idx_search (title, description)
);
```

#### 3. product_images 表（商品图片）

```sql
CREATE TABLE product_images (
    id VARCHAR(36) PRIMARY KEY,
    product_id VARCHAR(36) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_product (product_id)
);
```

#### 4. product_files 表（商品文件）

```sql
CREATE TABLE product_files (
    id VARCHAR(36) PRIMARY KEY,
    product_id VARCHAR(36) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_product (product_id)
);
```

#### 5. cart_items 表（购物车）

```sql
CREATE TABLE cart_items (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_product (user_id, product_id)
);
```

#### 6. orders 表（订单）

```sql
CREATE TABLE orders (
    id VARCHAR(36) PRIMARY KEY,
    order_no VARCHAR(50) UNIQUE NOT NULL,
    buyer_id VARCHAR(36) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('pending', 'paid', 'delivered', 'completed', 'cancelled', 'refunded') DEFAULT 'pending',
    payment_method VARCHAR(50),
    payment_time TIMESTAMP,
    delivery_time TIMESTAMP,
    completion_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES users(id),
    INDEX idx_buyer (buyer_id),
    INDEX idx_status (status),
    INDEX idx_order_no (order_no),
    INDEX idx_created_at (created_at)
);
```

#### 7. order_items 表（订单明细）

```sql
CREATE TABLE order_items (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    seller_id VARCHAR(36) NOT NULL,
    product_title VARCHAR(200) NOT NULL,
    product_cover VARCHAR(500),
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (seller_id) REFERENCES users(id),
    INDEX idx_order (order_id),
    INDEX idx_seller (seller_id)
);
```

#### 8. reviews 表（评价）

```sql
CREATE TABLE reviews (
    id VARCHAR(36) PRIMARY KEY,
    order_item_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    buyer_id VARCHAR(36) NOT NULL,
    seller_id VARCHAR(36) NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    content TEXT,
    images JSON,
    reply TEXT,
    reply_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_item_id) REFERENCES order_items(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (buyer_id) REFERENCES users(id),
    FOREIGN KEY (seller_id) REFERENCES users(id),
    INDEX idx_product (product_id),
    INDEX idx_buyer (buyer_id),
    INDEX idx_created_at (created_at)
);
```

#### 9. favorites 表（收藏）

```sql
CREATE TABLE favorites (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_product (user_id, product_id)
);
```

#### 10. transactions 表（交易记录）

```sql
CREATE TABLE transactions (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL,
    transaction_no VARCHAR(100) UNIQUE NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status ENUM('pending', 'success', 'failed', 'refunded') DEFAULT 'pending',
    payment_time TIMESTAMP,
    refund_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    INDEX idx_order (order_id),
    INDEX idx_transaction_no (transaction_no)
);
```

## API 接口设计

### 商品相关 API

#### GET /api/products
获取商品列表

**请求参数：**
```python
{
    "category_id": "分类ID（可选）",
    "keyword": "搜索关键词（可选）",
    "min_price": "最低价格（可选）",
    "max_price": "最高价格（可选）",
    "difficulty": "难度（可选）",
    "sort_by": "排序字段（price/sales/rating）",
    "order": "排序方向（asc/desc）",
    "page": 1,
    "page_size": 20
}
```

**响应：**
```python
{
    "products": [
        {
            "id": "product_uuid",
            "title": "基于Vue3的在线商城系统",
            "description": "...",
            "price": 299.00,
            "original_price": 399.00,
            "cover_image": "url",
            "rating": 4.8,
            "sales_count": 156,
            "seller": {
                "id": "user_uuid",
                "username": "seller123"
            }
        }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
}
```

#### GET /api/products/{product_id}
获取商品详情

**响应：**
```python
{
    "id": "product_uuid",
    "title": "基于Vue3的在线商城系统",
    "description": "详细描述...",
    "price": 299.00,
    "original_price": 399.00,
    "cover_image": "url",
    "demo_video": "url",
    "images": ["url1", "url2"],
    "tech_stack": ["Vue3", "Python", "MySQL"],
    "difficulty": "medium",
    "view_count": 1234,
    "sales_count": 156,
    "rating": 4.8,
    "review_count": 89,
    "seller": {
        "id": "user_uuid",
        "username": "seller123",
        "rating": 4.9
    },
    "created_at": "2024-01-01T00:00:00Z"
}
```

#### POST /api/products
发布商品（卖家）

**请求：**
```python
{
    "category_id": "category_uuid",
    "title": "商品标题",
    "description": "商品描述",
    "price": 299.00,
    "original_price": 399.00,
    "cover_image": "url",
    "demo_video": "url",
    "tech_stack": ["Vue3", "Python"],
    "difficulty": "medium"
}
```

### 订单相关 API

#### POST /api/orders
创建订单

**请求：**
```python
{
    "product_ids": ["product_uuid1", "product_uuid2"]
}
```

**响应：**
```python
{
    "order_id": "order_uuid",
    "order_no": "ORD20240101001",
    "total_amount": 598.00,
    "items": [
        {
            "product_id": "product_uuid1",
            "title": "商品1",
            "price": 299.00
        }
    ]
}
```

#### GET /api/orders
获取订单列表

#### GET /api/orders/{order_id}
获取订单详情

#### POST /api/orders/{order_id}/pay
支付订单

### 购物车相关 API

#### GET /api/cart
获取购物车

#### POST /api/cart
添加到购物车

#### DELETE /api/cart/{product_id}
从购物车删除

### 评价相关 API

#### POST /api/reviews
发表评价

#### GET /api/reviews
获取评价列表

## LangGraph 工作流扩展

### 新增意图类型

```python
INTENT_TYPES = {
    # 原有意图
    "问答": "qa_flow",
    "工单": "ticket_flow",
    "文档分析": "document_analysis",
    
    # 新增意图
    "商品推荐": "product_recommendation",
    "商品咨询": "product_inquiry",
    "购买指导": "purchase_guide",
    "订单查询": "order_query"
}
```

### 商品推荐节点

```python
async def product_recommendation_node(state: ConversationState) -> ConversationState:
    """商品推荐流程"""
    # 1. 提取用户需求
    prompt = ChatPromptTemplate.from_messages([
        ("system", """分析用户需求并提取关键信息：
        - 专业/方向
        - 技术栈偏好
        - 预算范围
        - 难度要求
        返回JSON格式"""),
        ("human", "{message}")
    ])
    
    requirements = await llm.ainvoke(prompt.format_messages(
        message=state["user_message"]
    ))
    
    # 2. 检索匹配商品
    products = await product_service.search_products(
        tech_stack=requirements.get("tech_stack"),
        max_price=requirements.get("budget"),
        difficulty=requirements.get("difficulty"),
        limit=5
    )
    
    # 3. 生成推荐理由
    products_text = "\n\n".join([
        f"商品{i+1}：{p.title}\n价格：{p.price}元\n技术栈：{p.tech_stack}\n评分：{p.rating}"
        for i, p in enumerate(products)
    ])
    
    recommendation_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是商品推荐专家，根据用户需求推荐合适的毕业设计作品"),
        ("human", """用户需求：{requirements}
        
可选商品：
{products}

请推荐最合适的商品并说明理由""")
    ])
    
    response = await llm.ainvoke(recommendation_prompt.format_messages(
        requirements=requirements,
        products=products_text
    ))
    
    state["response"] = response.content
    state["recommended_products"] = [p.id for p in products]
    
    return state
```

## 前端组件设计

### 新增页面组件

```
src/views/
├── ProductList.vue      # 商品列表页
├── ProductDetail.vue    # 商品详情页
├── Cart.vue            # 购物车页
├── Checkout.vue        # 结算页
├── Orders.vue          # 订单列表页
├── OrderDetail.vue     # 订单详情页
├── SellerCenter.vue    # 卖家中心
├── UserCenter.vue      # 用户中心
└── Chat.vue            # AI客服（保留）
```

### 新增状态管理

```typescript
// stores/product.ts
export const useProductStore = defineStore('product', () => {
  const products = ref<Product[]>([])
  const currentProduct = ref<Product | null>(null)
  
  const fetchProducts = async (params: SearchParams) => {
    const response = await api.get('/products', { params })
    products.value = response.data.products
  }
  
  const fetchProductDetail = async (id: string) => {
    const response = await api.get(`/products/${id}`)
    currentProduct.value = response.data
  }
  
  return { products, currentProduct, fetchProducts, fetchProductDetail }
})

// stores/cart.ts
export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  
  const addToCart = async (productId: string) => {
    await api.post('/cart', { product_id: productId })
    await fetchCart()
  }
  
  const fetchCart = async () => {
    const response = await api.get('/cart')
    items.value = response.data.items
  }
  
  return { items, addToCart, fetchCart }
})
```

## 部署架构

```
生产环境：
- 前端：Nginx + Vue 3 静态文件
- 后端：Gunicorn + FastAPI
- 数据库：MySQL 8.0
- 缓存：Redis 7
- 文件存储：本地存储 / OSS
```

## 开发计划

### 阶段 1：数据库和基础 API（1-2周）
- 创建新表结构
- 实现商品、订单、购物车 API
- 实现支付模拟

### 阶段 2：AI 客服扩展（1周）
- 扩展 LangGraph 工作流
- 实现商品推荐节点
- 实现商品咨询节点

### 阶段 3：前端开发（2-3周）
- 商品展示页面
- 购物车和订单页面
- 卖家中心
- 用户中心

### 阶段 4：测试和优化（1周）
- 功能测试
- 性能优化
- Bug 修复

总计：5-7周
