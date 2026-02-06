# 实现计划：智能毕业设计交易平台

## 概述

本实现计划将智能毕业设计交易平台的设计转化为可执行的开发任务。系统在原有 AI 客服系统基础上扩展电商功能，保持技术栈不变。

**实现策略：**
1. 扩展数据库表结构
2. 实现电商核心 API
3. 扩展 AI 客服工作流
4. 开发前端页面
5. 集成测试

## 任务列表

### 阶段 1：数据库扩展

- [x] 1. 扩展数据库表结构
  - [x] 1.1 创建商品相关表
    - 创建 categories 表（商品分类）
    - 创建 products 表（商品）
    - 创建 product_images 表（商品图片）
    - 创建 product_files 表（商品文件）
    - _需求：2, 3_
  
  - [x] 1.2 创建交易相关表
    - 创建 cart_items 表（购物车）
    - 创建 orders 表（订单）
    - 创建 order_items 表（订单明细）
    - 创建 transactions 表（交易记录）
    - _需求：5, 6, 7_
  
  - [x] 1.3 创建评价和收藏表
    - 创建 reviews 表（评价）
    - 创建 favorites 表（收藏）
    - _需求：8, 15_
  
  - [x] 1.4 更新数据库初始化脚本
    - 更新 init.sql 文件
    - 添加测试数据
    - _需求：所有_

### 阶段 2：后端数据模型

- [x] 2. 扩展 SQLAlchemy 数据模型
  - [x] 2.1 创建商品模型
    - Category 模型
    - Product 模型
    - ProductImage 模型
    - ProductFile 模型
    - _需求：2, 3_
  
  - [x] 2.2 创建交易模型
    - CartItem 模型
    - Order 模型
    - OrderItem 模型
    - Transaction 模型
    - _需求：5, 6, 7_
  
  - [x] 2.3 创建评价和收藏模型
    - Review 模型
    - Favorite 模型
    - _需求：8, 15_

### 阶段 3：后端业务服务

- [x] 3. 实现商品服务
  - [x] 3.1 实现 ProductService 类
    - create_product() - 创建商品
    - update_product() - 更新商品
    - delete_product() - 删除商品
    - get_product() - 获取商品详情
    - search_products() - 搜索商品
    - _需求：3, 4_
  
  - [x] 3.2 实现 CategoryService 类
    - create_category() - 创建分类
    - get_categories() - 获取分类列表
    - _需求：2_

- [x] 4. 实现购物车服务
  - [x] 4.1 实现 CartService 类
    - add_to_cart() - 添加到购物车
    - remove_from_cart() - 从购物车删除
    - get_cart() - 获取购物车
    - clear_cart() - 清空购物车
    - _需求：5_

- [x] 5. 实现订单服务
  - [x] 5.1 实现 OrderService 类
    - create_order() - 创建订单
    - get_order() - 获取订单详情
    - list_orders() - 获取订单列表
    - update_order_status() - 更新订单状态
    - cancel_order() - 取消订单
    - _需求：6, 7_

- [x] 6. 实现支付服务
  - [x] 6.1 实现 PaymentService 类
    - create_payment() - 创建支付
    - process_payment() - 处理支付（模拟）
    - refund_payment() - 退款
    - _需求：6_

- [x] 7. 实现评价服务
  - [x] 7.1 实现 ReviewService 类
    - create_review() - 创建评价
    - get_reviews() - 获取评价列表
    - reply_review() - 回复评价
    - _需求：8_

- [x] 8. 实现收藏服务
  - [x] 8.1 实现 FavoriteService 类
    - add_favorite() - 添加收藏
    - remove_favorite() - 取消收藏
    - get_favorites() - 获取收藏列表
    - _需求：15_

### 阶段 4：后端 API 路由

- [x] 9. 实现商品 API
  - [x] 9.1 创建 products.py 路由文件
    - GET /api/products - 获取商品列表
    - GET /api/products/{id} - 获取商品详情
    - POST /api/products - 发布商品
    - PUT /api/products/{id} - 更新商品
    - DELETE /api/products/{id} - 删除商品
    - _需求：3, 4_

- [x] 10. 实现购物车 API
  - [x] 10.1 创建 cart.py 路由文件
    - GET /api/cart - 获取购物车
    - POST /api/cart - 添加到购物车
    - DELETE /api/cart/{product_id} - 从购物车删除
    - _需求：5_

- [x] 11. 实现订单 API
  - [x] 11.1 创建 orders.py 路由文件
    - POST /api/orders - 创建订单
    - GET /api/orders - 获取订单列表
    - GET /api/orders/{id} - 获取订单详情
    - POST /api/orders/{id}/pay - 支付订单
    - POST /api/orders/{id}/cancel - 取消订单
    - _需求：6, 7_

- [x] 12. 实现评价 API
  - [x] 12.1 创建 reviews.py 路由文件
    - POST /api/reviews - 发表评价
    - GET /api/reviews - 获取评价列表
    - POST /api/reviews/{id}/reply - 回复评价
    - _需求：8_

- [x] 13. 实现收藏 API
  - [x] 13.1 创建 favorites.py 路由文件
    - POST /api/favorites - 添加收藏
    - GET /api/favorites - 获取收藏列表
    - DELETE /api/favorites/{product_id} - 取消收藏
    - _需求：15_

### 阶段 5：AI 客服扩展

- [x] 14. 扩展 LangGraph 工作流
  - [x] 14.1 添加商品推荐节点
    - 实现 product_recommendation_node
    - 提取用户需求（专业、技术栈、预算）
    - 检索匹配商品
    - 生成推荐理由
    - _需求：9_
  
  - [x] 14.2 添加商品咨询节点
    - 实现 product_inquiry_node
    - 从商品信息中提取答案
    - 解释技术栈和难度
    - 说明交付内容
    - _需求：10_
  
  - [x] 14.3 添加购买指导节点
    - 实现 purchase_guide_node
    - 说明购买步骤
    - 介绍支付方式
    - 说明退款政策
    - _需求：11_
  
  - [x] 14.4 添加订单查询节点
    - 实现 order_query_node
    - 查询订单信息
    - 返回订单状态
    - 提供处理建议
    - _需求：12_
  
  - [x] 14.5 更新意图识别
    - 扩展意图类型
    - 更新路由决策
    - _需求：9, 10, 11, 12_

- [x] 15. 扩展知识库
  - [x] 15.1 添加商品信息到 Chroma
    - 商品标题、描述、技术栈
    - 商品评价
    - _需求：9, 10_
  
  - [x] 15.2 添加平台规则到知识库
    - 购买流程
    - 退款政策
    - 常见问题
    - _需求：11_

### 阶段 6：前端状态管理

- [x] 16. 创建商品状态管理
  - [x] 16.1 实现 product.ts store
    - products 状态
    - currentProduct 状态
    - fetchProducts() 方法
    - fetchProductDetail() 方法
    - searchProducts() 方法
    - _需求：4_

- [x] 17. 创建购物车状态管理
  - [x] 17.1 实现 cart.ts store
    - items 状态
    - totalAmount 计算属性
    - addToCart() 方法
    - removeFromCart() 方法
    - fetchCart() 方法
    - _需求：5_

- [x] 18. 创建订单状态管理
  - [x] 18.1 实现 order.ts store
    - orders 状态
    - currentOrder 状态
    - createOrder() 方法
    - fetchOrders() 方法
    - payOrder() 方法
    - _需求：6, 7_

### 阶段 7：前端页面开发

- [x] 19. 实现商品展示页面
  - [x] 19.1 创建 ProductList.vue
    - 商品列表展示
    - 搜索和筛选
    - 分页
    - _需求：4_
  
  - [x] 19.2 创建 ProductDetail.vue
    - 商品详情展示
    - 图片轮播
    - 添加购物车按钮
    - 评价列表
    - _需求：4, 8_
  
  - [x] 19.3 创建 ProductCard.vue 组件
    - 商品卡片展示
    - 价格、评分、销量
    - _需求：4_

- [x] 20. 实现购物车页面
  - [x] 20.1 创建 Cart.vue
    - 购物车商品列表
    - 删除商品
    - 总价计算
    - 结算按钮
    - _需求：5_

- [x] 21. 实现订单页面
  - [x] 21.1 创建 Checkout.vue
    - 订单确认
    - 支付方式选择
    - 提交订单
    - _需求：6_
  
  - [x] 21.2 创建 Orders.vue
    - 订单列表
    - 订单状态筛选
    - _需求：7_
  
  - [x] 21.3 创建 OrderDetail.vue
    - 订单详情
    - 支付按钮
    - 取消订单按钮
    - _需求：7_

- [x] 22. 实现卖家中心
  - [x] 22.1 创建 SellerCenter.vue
    - 商品管理
    - 订单管理
    - 收入统计
    - _需求：13_
  
  - [x] 22.2 创建 ProductForm.vue
    - 商品发布表单
    - 图片上传
    - 文件上传
    - _需求：3_

- [x] 23. 实现用户中心
  - [x] 23.1 创建 UserCenter.vue
    - 个人信息
    - 我的订单
    - 我的收藏
    - _需求：7, 15_

- [x] 24. 实现评价功能
  - [x] 24.1 创建 ReviewForm.vue
    - 评分选择
    - 评论输入
    - 图片上传
    - _需求：8_
  
  - [x] 24.2 创建 ReviewList.vue
    - 评价列表展示
    - 卖家回复
    - _需求：8_

- [x] 25. 优化 AI 客服界面
  - [x] 25.1 创建 ChatWidget.vue
    - 悬浮窗口
    - 最小化/展开
    - 商品推荐卡片
    - _需求：9, 10, 11, 12_

### 阶段 8：管理后台扩展

- [x] 26. 扩展管理后台
  - [x] 26.1 添加商品审核功能
    - 待审核商品列表
    - 审核通过/拒绝
    - _需求：14_
  
  - [x] 26.2 添加数据统计
    - 商品统计
    - 订单统计
    - 收入统计
    - _需求：14, 17_
  
  - [x] 26.3 添加用户管理
    - 用户列表
    - 用户详情
    - 禁用/启用用户
    - _需求：14_

### 阶段 9：测试和优化

- [x] 27. 功能测试
  - [x] 27.1 测试商品流程
    - 发布商品
    - 搜索商品
    - 查看商品详情
    - _需求：3, 4_
  
  - [x] 27.2 测试购买流程
    - 添加购物车
    - 创建订单
    - 支付订单
    - _需求：5, 6, 7_
  
  - [x] 27.3 测试 AI 客服
    - 商品推荐
    - 商品咨询
    - 购买指导
    - 订单查询
    - _需求：9, 10, 11, 12_

- [x] 28. 性能优化
  - [x] 28.1 优化数据库查询
    - 添加索引
    - 优化复杂查询
    - _需求：19_
  
  - [x] 28.2 添加缓存
    - 商品列表缓存
    - 商品详情缓存
    - _需求：19_
  
  - [x] 28.3 优化前端性能
    - 图片懒加载
    - 路由懒加载
    - 组件懒加载
    - _需求：19, 20_

- [x] 29. 文档编写
  - [x] 29.1 编写 API 文档
    - 商品 API
    - 订单 API
    - 支付 API
    - _需求：所有_
  
  - [x] 29.2 编写用户手册
    - 买家使用指南
    - 卖家使用指南
    - AI 客服使用指南
    - _需求：所有_
  
  - [x] 29.3 编写部署文档
    - 环境配置
    - 部署步骤
    - 常见问题
    - _需求：所有_

## 注意事项

- 保留原有 AI 客服系统的所有功能
- 新增功能与原有功能解耦，便于维护
- 优先实现核心功能，再完善细节
- 每个阶段完成后进行测试
- 及时更新文档

## 预计时间

- 阶段 1-2：数据库和模型（3-5天）
- 阶段 3-4：后端服务和 API（1-2周）
- 阶段 5：AI 客服扩展（3-5天）
- 阶段 6-7：前端开发（2-3周）
- 阶段 8：管理后台（3-5天）
- 阶段 9：测试和优化（1周）

**总计：5-7周**
