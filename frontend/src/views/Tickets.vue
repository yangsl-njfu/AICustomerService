<template>
  <AppLayout>
    <div class="tickets-page container">
      <div class="state-card">
        <strong>工单模块已下线</strong>
        <p>请使用 AI 助手或售后服务入口处理问题。</p>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
</script>

<style scoped>
.tickets-page {
  padding: 32px 0;
}

.state-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 32px;
  text-align: center;
}

.state-card strong {
  font-size: 18px;
  color: var(--text);
}

.state-card p {
  margin-top: 8px;
  color: var(--text-muted);
}
</style>
