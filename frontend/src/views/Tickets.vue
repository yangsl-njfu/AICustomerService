<template>
  <div class="tickets-container">
    <div class="tickets-header">
      <h3>我的工单</h3>
      <el-button type="primary" @click="showCreateDialog = true">创建工单</el-button>
    </div>

    <el-table :data="tickets" style="width: 100%" class="tickets-table">
      <el-table-column prop="id" label="工单号" width="200" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="120">
        <template #default="{ row }">
          <el-tag :type="getPriorityType(row.priority)">
            {{ getPriorityText(row.priority) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建工单对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建工单" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createTicket">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { apiClient } from '@/api/client'
import { ElMessage } from 'element-plus'

const tickets = ref<any[]>([])
const showCreateDialog = ref(false)

const form = reactive({
  title: '',
  description: '',
  priority: 'medium'
})

onMounted(async () => {
  await fetchTickets()
})

const fetchTickets = async () => {
  try {
    tickets.value = await apiClient.get('/tickets')
  } catch (error) {
    console.error('获取工单列表失败:', error)
  }
}

const createTicket = async () => {
  try {
    await apiClient.post('/tickets', form)
    ElMessage.success('工单创建成功')
    showCreateDialog.value = false
    await fetchTickets()
    
    // 重置表单
    form.title = ''
    form.description = ''
    form.priority = 'medium'
  } catch (error) {
    ElMessage.error('工单创建失败')
  }
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    pending: 'warning',
    in_progress: 'primary',
    resolved: 'success',
    closed: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待处理',
    in_progress: '处理中',
    resolved: '已解决',
    closed: '已关闭'
  }
  return texts[status] || status
}

const getPriorityType = (priority: string) => {
  const types: Record<string, any> = {
    low: 'info',
    medium: 'primary',
    high: 'warning',
    urgent: 'danger'
  }
  return types[priority] || 'info'
}

const getPriorityText = (priority: string) => {
  const texts: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  }
  return texts[priority] || priority
}

const formatDate = (date: string) => {
  if (!date) return ''
  const d = new Date(date)
  const year = d.getFullYear()
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hours = d.getHours().toString().padStart(2, '0')
  const minutes = d.getMinutes().toString().padStart(2, '0')
  const seconds = d.getSeconds().toString().padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}
</script>

<style scoped>
.tickets-container {
  padding: 24px;
  background: var(--surface);
  border-radius: 16px;
  box-shadow: var(--shadow);
  min-height: calc(100vh - 120px);
  border: 1px solid var(--border);
}

.tickets-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.tickets-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
}

.tickets-header :deep(.el-button) {
  border-radius: 999px;
  padding: 6px 18px;
  font-weight: 600;
  background: rgba(56, 189, 248, 0.18);
  border: 1px solid rgba(56, 189, 248, 0.45);
  color: var(--text);
  box-shadow: 0 10px 24px rgba(2, 6, 23, 0.4);
}

.tickets-table :deep(.el-table__inner-wrapper) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 24px rgba(2, 6, 23, 0.35);
}

.tickets-table :deep(.el-table) {
  background: var(--surface-2);
  color: var(--text);
}

.tickets-table :deep(.el-table tr) {
  background: var(--surface-2);
}

.tickets-table :deep(.el-table td.el-table__cell) {
  background: var(--surface-2);
  border-bottom: 1px solid var(--border);
  color: var(--text);
}

.tickets-table :deep(.el-table__header th) {
  background: var(--surface-2);
  color: var(--text);
  font-weight: 600;
}

.tickets-table :deep(.el-table__row:hover) {
  background: rgba(148, 163, 184, 0.12);
}

.tickets-container :deep(.el-dialog) {
  border-radius: 16px;
  background: var(--surface-2);
  border: 1px solid var(--border);
}

.tickets-container :deep(.el-dialog__title) {
  color: var(--text);
  font-weight: 600;
}

.tickets-container :deep(.el-dialog__body) {
  color: var(--text);
}

.tickets-container :deep(.el-input__wrapper),
.tickets-container :deep(.el-textarea__inner),
.tickets-container :deep(.el-select__wrapper) {
  background: var(--surface-3);
  border: 1px solid var(--border);
  box-shadow: none;
  color: var(--text);
}

.tickets-container :deep(.el-input__inner),
.tickets-container :deep(.el-textarea__inner) {
  color: var(--text);
}
</style>
