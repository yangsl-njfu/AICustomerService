# 导航系统说明

## 🧭 路由结构

项目采用嵌套路由结构，Home 组件作为主布局容器，包含侧边栏导航和内容区域。

### 路由层级

```
/
├── /login (登录页)
├── /register (注册页)
└── / (Home 主布局)
    ├── /products (商品列表) - 默认页
    ├── /products/:id (商品详情)
    ├── /cart (购物车)
    ├── /orders (我的订单)
    ├── /favorites (我的收藏)
    ├── /chat (AI 助手)
    ├── /tickets (工单)
    ├── /knowledge (知识库)
    └── /admin (管理后台) - 仅管理员
```

## 📱 侧边栏导航

### 导航菜单项

| 图标 | 名称 | 路径 | 说明 |
|------|------|------|------|
| 🛍️ | 商城 | /products | 浏览所有商品 |
| 🛒 | 购物车 | /cart | 查看购物车 |
| 📄 | 我的订单 | /orders | 订单管理 |
| ⭐ | 我的收藏 | /favorites | 收藏的商品 |
| 💬 | AI助手 | /chat | 智能客服对话 |
| 🎫 | 工单 | /tickets | 工单系统 |
| 📚 | 知识库 | /knowledge | 知识库管理 |
| ⚙️ | 管理后台 | /admin | 系统管理（管理员） |

### 导航特点

1. **响应式高亮** - 当前页面对应的菜单项会高亮显示
2. **图标 + 文字** - 清晰的视觉标识
3. **悬停效果** - 鼠标悬停时背景变色
4. **权限控制** - 管理后台仅管理员可见

## 🎨 导航样式

### 默认状态
- 背景：透明
- 文字：灰色 (#666)
- 图标：浅灰 (#999)

### 悬停状态
- 背景：浅灰 (#f8f9fa)
- 文字：蓝色 (#1890ff)
- 图标：蓝色 (#1890ff)

### 激活状态
- 背景：浅蓝 (#e6f7ff)
- 文字：蓝色 (#1890ff)
- 图标：蓝色 (#1890ff)
- 字重：600（加粗）

## 🔧 技术实现

### 路由配置

```typescript
{
  path: '/',
  component: Home,
  redirect: '/products',  // 默认跳转到商品列表
  children: [
    { path: '/products', component: ProductList },
    { path: '/cart', component: Cart },
    // ... 其他子路由
  ]
}
```

### 菜单组件

```vue
<el-menu :default-active="activeMenu" router>
  <el-menu-item index="/products">
    <el-icon><ShoppingBag /></el-icon>
    <span>商城</span>
  </el-menu-item>
  <!-- ... 其他菜单项 -->
</el-menu>
```

### 激活状态管理

```typescript
const activeMenu = ref(route.path)

// 监听路由变化
watch(() => route.path, (newPath) => {
  activeMenu.value = newPath
})
```

## 🚀 使用方法

### 1. 点击导航
直接点击侧边栏的任意菜单项即可跳转到对应页面。

### 2. 编程式导航
在代码中使用 router 进行跳转：

```typescript
import { useRouter } from 'vue-router'

const router = useRouter()

// 跳转到商品详情
router.push(`/products/${productId}`)

// 跳转到购物车
router.push('/cart')
```

### 3. 声明式导航
使用 router-link 组件：

```vue
<router-link to="/products">查看商品</router-link>
<router-link :to="`/products/${id}`">商品详情</router-link>
```

## 🔐 权限控制

### 路由守卫

```typescript
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // 需要登录
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  }
  // 需要管理员权限
  else if (to.meta.requiresAdmin && authStore.user?.role !== 'admin') {
    next('/')
  }
  else {
    next()
  }
})
```

### 菜单权限

```vue
<!-- 仅管理员可见 -->
<el-menu-item 
  v-if="authStore.user?.role === 'admin'" 
  index="/admin"
>
  <el-icon><Setting /></el-icon>
  <span>管理后台</span>
</el-menu-item>
```

## 📱 响应式设计

### 桌面端
- 侧边栏固定宽度：200px
- 始终显示

### 移动端（未来优化）
- 可折叠侧边栏
- 汉堡菜单按钮
- 全屏抽屉式导航

## 🎯 最佳实践

1. **保持一致性** - 所有页面都使用相同的导航结构
2. **清晰的视觉反馈** - 当前页面高亮显示
3. **快速访问** - 常用功能放在顶部
4. **权限分离** - 根据用户角色显示不同菜单

## 🐛 常见问题

### Q: 为什么侧边栏不显示？
A: 确保路由配置正确，所有页面都是 Home 的子路由。

### Q: 菜单项不高亮？
A: 检查 `activeMenu` 是否正确设置为当前路由路径。

### Q: 如何添加新菜单项？
A: 
1. 在 router/index.ts 中添加路由
2. 在 Home.vue 中添加 el-menu-item
3. 导入对应的图标组件

### Q: 管理后台菜单不显示？
A: 确保当前用户的 role 为 'admin'。

## 🔄 更新日志

### v2.0.0 (2026-02-06)
- ✅ 修复路由结构，改为嵌套路由
- ✅ 添加路由监听，自动更新激活状态
- ✅ 优化导航样式，适配新主题
- ✅ 改进权限控制逻辑

### v1.0.0
- 初始版本

---

**最后更新**: 2026-02-06
**维护者**: AI Assistant
