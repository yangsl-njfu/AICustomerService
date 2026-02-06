<template>
  <div class="home-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h2>AI客服系统</h2>
          <div class="user-info">
            <span>{{ authStore.user?.username }}</span>
            <el-button @click="handleLogout" size="small">退出</el-button>
          </div>
        </div>
      </el-header>
      
      <el-container>
        <el-aside width="200px">
          <el-menu :default-active="activeMenu" router>
            <el-menu-item index="/products">
              <el-icon><ShoppingBag /></el-icon>
              <span>商城</span>
            </el-menu-item>
            <el-menu-item index="/cart">
              <el-icon><ShoppingCart /></el-icon>
              <span>购物车</span>
            </el-menu-item>
            <el-menu-item index="/orders">
              <el-icon><Document /></el-icon>
              <span>我的订单</span>
            </el-menu-item>
            <el-menu-item index="/favorites">
              <el-icon><Star /></el-icon>
              <span>我的收藏</span>
            </el-menu-item>
            <el-menu-item index="/chat">
              <el-icon><ChatDotRound /></el-icon>
              <span>AI助手</span>
            </el-menu-item>
            <el-menu-item index="/tickets">
              <el-icon><Tickets /></el-icon>
              <span>工单</span>
            </el-menu-item>
            <el-menu-item index="/knowledge">
              <el-icon><Collection /></el-icon>
              <span>知识库</span>
            </el-menu-item>
            <el-menu-item v-if="authStore.user?.role === 'admin'" index="/admin">
              <el-icon><Setting /></el-icon>
              <span>管理后台</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ChatDotRound, Tickets, Setting, Collection, ShoppingBag, ShoppingCart, Document, Star } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const activeMenu = ref(route.path)

// 监听路由变化，更新激活菜单
watch(() => route.path, (newPath) => {
  activeMenu.value = newPath
})

onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchUser()
  }
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.home-container {
  height: 100vh;
  background: var(--bg);
}

.el-header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 32px;
  box-shadow: var(--shadow-sm);
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  margin: 0;
  color: var(--text);
  font-size: 20px;
  font-weight: 600;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
  color: var(--text);
}

.user-info span {
  background: var(--primary-lighter);
  color: var(--primary);
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.user-info :deep(.el-button) {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  font-weight: 500;
  border-radius: 20px;
  padding: 0 20px;
  transition: all 0.3s ease;
}

.user-info :deep(.el-button:hover) {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
  transform: translateY(-1px);
  box-shadow: var(--shadow);
}

.el-aside {
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 16px 8px;
}

.el-aside :deep(.el-menu) {
  border-right: none;
  background: transparent;
}

.el-aside :deep(.el-menu-item) {
  margin: 4px 0;
  border-radius: 8px;
  height: 48px;
  line-height: 48px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.3s ease;
}

.el-aside :deep(.el-menu-item .el-icon) {
  color: var(--text-muted);
  font-size: 18px;
}

.el-aside :deep(.el-menu-item:hover) {
  background: var(--surface-hover);
  color: var(--primary);
}

.el-aside :deep(.el-menu-item:hover .el-icon) {
  color: var(--primary);
}

.el-aside :deep(.el-menu-item.is-active) {
  background: var(--primary-lighter);
  color: var(--primary);
  font-weight: 600;
}

.el-aside :deep(.el-menu-item.is-active .el-icon) {
  color: var(--primary);
}

.el-main {
  padding: 0;
  background: var(--bg);
  overflow-y: auto;
  height: calc(100vh - 60px);
}
</style>
