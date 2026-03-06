<template>
  <div class="home-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <div class="logo">
            <el-icon class="logo-icon"><ShoppingBag /></el-icon>
            <h2>电商平台</h2>
          </div>
          <div class="user-info">
            <span class="username">{{ authStore.user?.username }}</span>
            <el-button type="info" plain size="small" @click="handleLogout">退出</el-button>
          </div>
        </div>
      </el-header>
      
      <el-container>
        <el-aside width="220px">
          <el-menu :default-active="activeMenu" router>
            <el-menu-item index="/products">
              <el-icon><ShoppingBag /></el-icon>
              <span>商品列表</span>
            </el-menu-item>
            <el-menu-item index="/cart">
              <el-icon><ShoppingCart /></el-icon>
              <span>购物车</span>
            </el-menu-item>
            <el-menu-item index="/orders">
              <el-icon><Document /></el-icon>
              <span>我的订单</span>
            </el-menu-item>
            <el-menu-item index="/refunds">
              <el-icon><Money /></el-icon>
              <span>我的售后</span>
            </el-menu-item>
            <el-menu-item index="/favorites">
              <el-icon><Star /></el-icon>
              <span>我的收藏</span>
            </el-menu-item>
            <el-menu-item index="/chat">
              <el-icon><ChatDotRound /></el-icon>
              <span>客服助手</span>
            </el-menu-item>
            <el-menu-item index="/tickets">
              <el-icon><Tickets /></el-icon>
              <span>我的工单</span>
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
import { ChatDotRound, Tickets, Setting, Collection, ShoppingBag, ShoppingCart, Document, Star, Money } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const activeMenu = ref(route.path)

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
  overflow: hidden;
}

.home-container :deep(.el-container) {
  height: 100%;
}

.el-header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 32px;
  box-shadow: var(--shadow-sm);
  height: 60px;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  font-size: 24px;
  color: var(--primary);
}

.logo h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
}

.el-aside {
  background: var(--surface);
  border-right: 1px solid var(--border);
}

.el-aside :deep(.el-menu) {
  border-right: none;
  background: transparent;
}

.el-aside :deep(.el-menu-item) {
  margin: 4px 12px;
  border-radius: var(--radius);
  height: 44px;
  line-height: 44px;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.el-aside :deep(.el-menu-item .el-icon) {
  color: var(--text-muted);
}

.el-aside :deep(.el-menu-item:hover) {
  background: var(--surface-hover);
  color: var(--text);
}

.el-aside :deep(.el-menu-item.is-active) {
  background: var(--primary-lighter);
  color: var(--primary);
  font-weight: 500;
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
