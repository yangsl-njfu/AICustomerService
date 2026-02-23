<template>
  <div class="refunds-container">
    <h2>我的售后</h2>
    
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="全部" name="all"></el-tab-pane>
      <el-tab-pane label="处理中" name="processing"></el-tab-pane>
      <el-tab-pane label="已完成" name="completed"></el-tab-pane>
    </el-tabs>
    
    <div v-loading="loading" class="refunds-list">
      <el-empty v-if="refunds.length === 0" description="暂无售后记录" />
      
      <div v-for="refund in refunds" :key="refund.id" class="refund-card">
        <div class="refund-header">
          <span class="refund-no">售后单号: {{ refund.refund_no }}</span>
          <el-tag :type="getStatusType(refund.status)">{{ getStatusText(refund.status) }}</el-tag>
        </div>
        
        <div class="refund-info">
          <div class="info-row">
            <span class="label">订单号:</span>
            <span class="value">{{ refund.order_no }}</span>
          </div>
          <div class="info-row">
            <span class="label">售后类型:</span>
            <span class="value">{{ getTypeText(refund.refund_type) }}</span>
          </div>
          <div class="info-row">
            <span class="label">退款原因:</span>
            <span class="value">{{ refund.reason }}</span>
          </div>
          <div class="info-row">
            <span class="label">退款金额:</span>
            <span class="value amount">¥{{ (refund.refund_amount / 100).toFixed(2) }}</span>
          </div>
          <div v-if="refund.description" class="info-row">
            <span class="label">问题描述:</span>
            <span class="value">{{ refund.description }}</span>
          </div>
          <div class="info-row">
            <span class="label">申请时间:</span>
            <span class="value">{{ formatTime(refund.created_at) }}</span>
          </div>
          <div v-if="refund.reviewed_at" class="info-row">
            <span class="label">审核时间:</span>
            <span class="value">{{ formatTime(refund.reviewed_at) }}</span>
          </div>
          <div v-if="refund.review_note" class="info-row">
            <span class="label">审核备注:</span>
            <span class="value">{{ refund.review_note }}</span>
          </div>
        </div>
        
        <div v-if="refund.evidence_images && refund.evidence_images.length > 0" class="refund-images">
          <p class="images-title">凭证图片:</p>
          <div class="images-list">
            <el-image
              v-for="(img, index) in refund.evidence_images"
              :key="index"
              :src="img"
              :preview-src-list="refund.evidence_images"
              fit="cover"
              class="evidence-image"
            />
          </div>
        </div>
      </div>
    </div>
    
    <el-pagination
      v-if="total > pageSize"
      v-model:current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next"
      @current-change="fetchRefunds"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { apiClient } from '@/api/client'

const activeTab = ref('all')
const loading = ref(false)
const refunds = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const fetchRefunds = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/refunds/', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      }
    })
    refunds.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    console.error('获取售后列表失败:', error)
    ElMessage.error('获取售后列表失败')
  } finally {
    loading.value = false
  }
}

const handleTabChange = () => {
  currentPage.value = 1
  fetchRefunds()
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger',
    'returning': 'primary',
    'refunding': 'primary',
    'completed': 'success',
    'cancelled': 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    'pending': '待审核',
    'approved': '已通过',
    'rejected': '已拒绝',
    'returning': '退货中',
    'refunding': '退款中',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return textMap[status] || status
}

const getTypeText = (type: string) => {
  const textMap: Record<string, string> = {
    'refund_only': '仅退款',
    'return_refund': '退货退款',
    'exchange': '换货'
  }
  return textMap[type] || type
}

const formatTime = (time: string) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  fetchRefunds()
})
</script>

<style scoped>
.refunds-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

h2 {
  margin-bottom: 20px;
  color: #333;
}

.refunds-list {
  margin-top: 20px;
}

.refund-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.refund-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.refund-no {
  font-size: 14px;
  color: #666;
}

.refund-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  align-items: flex-start;
}

.label {
  width: 80px;
  color: #999;
  font-size: 14px;
  flex-shrink: 0;
}

.value {
  flex: 1;
  color: #333;
  font-size: 14px;
}

.value.amount {
  color: #f56c6c;
  font-weight: 600;
  font-size: 16px;
}

.refund-images {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.images-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
}

.images-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.evidence-image {
  width: 100px;
  height: 100px;
  border-radius: 4px;
  cursor: pointer;
}

:deep(.el-pagination) {
  margin-top: 20px;
  justify-content: center;
}
</style>
