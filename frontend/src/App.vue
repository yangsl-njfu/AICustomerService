<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// 应用根组件
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  width: 100%;
  height: 100%;
  background: #fafafa;
  color: #1a1a1a;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

:root {
  color-scheme: light;
  /* 主色调 - 柔和蓝 */
  --primary: #2563eb;
  --primary-light: #3b82f6;
  --primary-lighter: #eff6ff;
  --primary-dark: #1d4ed8;
  
  /* 背景色 */
  --bg: #fafafa;
  --bg-light: #ffffff;
  --surface: #ffffff;
  --surface-hover: #f5f5f5;
  --surface-2: #f8f9fa;
  --surface-3: #f0f0f0;
  
  /* 文字颜色 */
  --text: #1a1a1a;
  --text-secondary: #525252;
  --text-muted: #a3a3a3;
  --text-light: #d4d4d4;
  --muted: #737373;
  
  /* 边框 */
  --border: #e5e5e5;
  --border-light: #f0f0f0;
  
  /* 功能色 */
  --success: #16a34a;
  --warning: #ca8a04;
  --danger: #dc2626;
  --info: #2563eb;
  --accent: #2563eb;
  
  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  
  /* 圆角 */
  --radius-sm: 6px;
  --radius: 8px;
  --radius-lg: 12px;
}

#app {
  width: 100vw;
  height: 100vh;
  background: var(--bg);
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #d4d4d4;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a3a3a3;
}

/* Element Plus 覆盖样式 */
.el-button--primary {
  --el-button-bg-color: var(--primary);
  --el-button-border-color: var(--primary);
  --el-button-hover-bg-color: var(--primary-light);
  --el-button-hover-border-color: var(--primary-light);
}

.el-button {
  border-radius: var(--radius);
}

.el-input__wrapper {
  border-radius: var(--radius);
}

.el-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
}

.el-dialog {
  border-radius: var(--radius-lg);
}

.el-message-box {
  border-radius: var(--radius-lg);
}

.el-tabs__item {
  font-weight: 500;
}

.el-tag {
  border-radius: var(--radius-sm);
}
</style>
