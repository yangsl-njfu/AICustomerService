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
  background: #f5f7fa;
  color: #333;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}

:root {
  color-scheme: light;
  /* 主色调 - 清新蓝 */
  --primary: #1890ff;
  --primary-light: #40a9ff;
  --primary-lighter: #e6f7ff;
  --primary-dark: #096dd9;
  
  /* 背景色 */
  --bg: #f5f7fa;
  --bg-light: #fafbfc;
  --surface: #ffffff;
  --surface-hover: #f8f9fa;
  
  /* 文字颜色 */
  --text: #333333;
  --text-secondary: #666666;
  --text-muted: #999999;
  --text-light: #cccccc;
  
  /* 边框 */
  --border: #e8e8e8;
  --border-light: #f0f0f0;
  
  /* 功能色 */
  --success: #52c41a;
  --warning: #faad14;
  --danger: #ff4d4f;
  --info: #1890ff;
  
  /* 阴影 */
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.06);
  --shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);
  
  /* 渐变 */
  --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-warm: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  --gradient-cool: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

#app {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  width: 100vw;
  height: 100vh;
  background: var(--bg);
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-light);
}

::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-light);
}
</style>
