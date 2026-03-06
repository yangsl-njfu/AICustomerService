<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// 应用根组件
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  width: 100%;
  height: 100%;
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

:root {
  color-scheme: light;
  /* 主色调 - 柔和蓝 */
  --primary: #2563eb;
  --primary-light: #3b82f6;
  --primary-lighter: #eaf2ff;
  --primary-dark: #1d4ed8;
  
  --bg: #f5f7fb;
  --bg-light: #ffffff;
  --surface: #ffffff;
  --surface-hover: #f8fafc;
  --surface-2: #f1f5f9;
  --surface-3: #e9eef5;
  
  /* 文字颜色 */
  --text: #0f172a;
  --text-secondary: #334155;
  --text-muted: #64748b;
  --text-light: #cbd5e1;
  --muted: #64748b;
  
  /* 边框 */
  --border: #e2e8f0;
  --border-light: #edf2f7;
  
  /* 功能色 */
  --success: #16a34a;
  --warning: #f59e0b;
  --danger: #ef4444;
  --info: #2563eb;
  --accent: #3b82f6;
  --cta: #f97316;
  
  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 16px 32px rgba(15, 23, 42, 0.12);
  
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
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
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
  transition: all 0.2s ease;
}

.el-input__wrapper {
  border-radius: var(--radius);
  background: var(--surface-2);
  border: 1px solid var(--border);
  box-shadow: none;
}

.el-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}

.el-dialog {
  border-radius: var(--radius-lg);
  background: var(--surface);
}

.el-message-box {
  border-radius: var(--radius-lg);
  background: var(--surface);
}

.el-tabs__item {
  font-weight: 500;
}

.el-tag {
  border-radius: var(--radius-sm);
}

.el-input__wrapper.is-focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.18);
}

.el-button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}
</style>
