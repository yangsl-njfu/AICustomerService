# 项目启动指南

## ✅ 已完成的修复和改进

### 1. 后端 API 路由修复
- **问题**: `/api/products/categories` 被错误地匹配到 `/api/products/{product_id}`
- **解决**: 重新组织路由顺序，将分类路由放在商品详情路由之前
- **修改文件**: `backend/api/products.py`

### 2. 前端界面全新设计
- **改进**: 采用现代化深色主题设计
- **特点**:
  - 渐变色彩和流畅动画
  - 响应式布局
  - 优雅的加载和空状态
  - 现代化的搜索和筛选界面
- **修改文件**: `frontend/src/views/ProductList.vue`

### 3. 数据库初始化
- **完成**: 已初始化测试数据
- **包含**: 8个商品、3个分类、4个测试用户

## 🚀 启动步骤

### 使用虚拟环境 AICustomService

项目使用虚拟环境 **AICustomService**（项目根目录下 `AICustomService` 文件夹）。  
后端请使用该环境内的 Python，避免与系统 Python 混用。

**一键启动（推荐）**：在项目根目录执行
```powershell
.\start.ps1
```
脚本会自动用 AICustomService 的 Python 启动后端，并另开窗口启动前端。

### 1. 手动启动后端服务

```powershell
cd backend
# 使用虚拟环境 AICustomService 的 Python
& ..\AICustomService\Scripts\python.exe main.py
```

或先激活虚拟环境再启动：
```powershell
..\AICustomService\Scripts\Activate.ps1
cd backend
python main.py
```

**后端地址**: http://localhost:8000  
**API 文档**: http://localhost:8000/api/docs

### 2. 启动前端服务

```bash
cd frontend
npm run dev
```

**前端地址**: http://localhost:5173

## 👤 测试账户

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 买家 | buyer1 | buyer123 |
| 卖家1 | seller1 | seller123 |
| 卖家2 | seller2 | seller123 |

## 📦 测试商品

系统已预置 8 个测试商品：

1. **基于Vue3的在线商城系统** - ¥299.00
2. **Python数据分析系统** - ¥199.00
3. **React Native移动应用** - ¥399.00
4. **企业人事管理系统** - ¥249.00
5. **智能家居控制系统** - ¥349.00
6. **微信小程序商城** - ¥279.00
7. **在线教育平台** - ¥359.00
8. **图书管理系统** - ¥159.00

## 🎨 设计特点

### 颜色方案
- **背景**: 深色主题 (#0b1020)
- **主色调**: 青色渐变 (#38bdf8 → #22d3ee)
- **成功色**: 绿色 (#34d399)
- **危险色**: 粉红色 (#fb7185)

### 界面元素
- **Hero Section**: 大标题 + 搜索栏
- **分类筛选**: 圆角芯片式设计
- **工具栏**: 难度、价格筛选 + 排序
- **商品网格**: 响应式卡片布局
- **分页**: 现代化翻页控件

## 🔧 技术栈

### 后端
- FastAPI
- SQLAlchemy (SQLite)
- Redis
- LangChain + LangGraph
- Chroma 向量数据库

### 前端
- Vue 3 + TypeScript
- Pinia 状态管理
- Element Plus UI
- Axios

## 📝 API 端点

### 商品相关
- `GET /api/products` - 获取商品列表
- `GET /api/products/{id}` - 获取商品详情
- `GET /api/products/categories` - 获取分类列表
- `POST /api/products` - 创建商品（需登录）
- `PUT /api/products/{id}` - 更新商品（需登录）
- `DELETE /api/products/{id}` - 删除商品（需登录）

### 购物车
- `GET /api/cart` - 获取购物车
- `POST /api/cart` - 添加到购物车
- `PUT /api/cart/{id}` - 更新购物车项
- `DELETE /api/cart/{id}` - 删除购物车项

### 订单
- `GET /api/orders` - 获取订单列表
- `POST /api/orders` - 创建订单
- `GET /api/orders/{id}` - 获取订单详情

## 🐛 已修复的问题

1. ✅ 路由冲突导致分类接口404
2. ✅ 前端布局问题
3. ✅ 深色主题样式不统一
4. ✅ 商品列表显示"暂无商品"

## 📱 响应式设计

- **桌面**: 完整功能，多列网格布局
- **平板**: 自适应布局，2-3列网格
- **手机**: 单列布局，堆叠式筛选

## 🎯 下一步建议

1. **功能增强**
   - 添加商品详情页
   - 实现购物车功能
   - 完善订单流程
   - 集成支付接口

2. **UI/UX 优化**
   - 添加骨架屏加载
   - 优化移动端体验
   - 添加更多动画效果
   - 实现暗色/亮色主题切换

3. **性能优化**
   - 图片懒加载
   - 虚拟滚动
   - Redis 缓存优化
   - CDN 加速

## 💡 使用提示

1. **搜索功能**: 在顶部搜索栏输入关键词，按回车搜索
2. **分类筛选**: 点击分类芯片快速筛选
3. **价格筛选**: 输入价格区间后自动应用
4. **排序**: 使用右上角下拉菜单排序
5. **重置**: 点击"重置"按钮清除所有筛选条件

## 🔗 相关文档

- [项目总结](PROJECT_SUMMARY.md)
- [安装指南](SETUP.md)
- [AI 学习指南](AI_LEARNING_GUIDE.md)
- [快速参考](AI_QUICK_REFERENCE.md)

---

**最后更新**: 2026-02-06
**版本**: 1.0.0
