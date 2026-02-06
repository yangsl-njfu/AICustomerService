<template>
  <div class="admin-container">
    <h2>管理后台</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 24px">
      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_users }}</div>
            <div class="stat-label">总用户数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_sessions }}</div>
            <div class="stat-label">总会话数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_messages }}</div>
            <div class="stat-label">总消息数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">{{ stats.pending_tickets }}</div>
            <div class="stat-label">待处理工单</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 知识库管理 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>知识库管理</span>
          <el-upload
            :action="`/api/admin/knowledge/upload`"
            :headers="{ Authorization: `Bearer ${authStore.token}` }"
            :on-success="handleUploadSuccess"
            :show-file-list="false"
          >
            <el-button type="primary" size="small">上传文档</el-button>
          </el-upload>
        </div>
      </template>
      <p>知识库文档管理功能</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiClient } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()

const stats = ref({
  total_users: 0,
  total_sessions: 0,
  total_messages: 0,
  total_tickets: 0,
  active_sessions: 0,
  pending_tickets: 0
})

onMounted(async () => {
  await fetchStats()
})

const fetchStats = async () => {
  try {
    stats.value = await apiClient.get('/admin/stats')
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

const handleUploadSuccess = () => {
  ElMessage.success('文档上传成功')
}
</script>

<style scoped>
.admin-container {
  padding: 24px;
  background: var(--surface);
  border-radius: 16px;
  box-shadow: var(--shadow);
  min-height: calc(100vh - 120px);
  border: 1px solid var(--border);
  color: var(--text);
}

.admin-container h2 {
  margin-bottom: 24px;
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: 0.3px;
}

.admin-container :deep(.el-card) {
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: 0 10px 24px rgba(2, 6, 23, 0.35);
  background: var(--surface-2);
}

.admin-container :deep(.el-card__header) {
  padding: 16px 20px;
  font-weight: 600;
  color: var(--text);
}

.stat-card {
  text-align: center;
  padding: 8px 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 6px;
}

.stat-label {
  font-size: 14px;
  color: var(--muted);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header :deep(.el-button) {
  border-radius: 999px;
  padding: 6px 16px;
  font-weight: 600;
  background: rgba(56, 189, 248, 0.18);
  border: 1px solid rgba(56, 189, 248, 0.45);
  color: var(--text);
  box-shadow: 0 10px 24px rgba(2, 6, 23, 0.4);
}
</style>
