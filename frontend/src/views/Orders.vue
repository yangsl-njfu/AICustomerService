<template>
  <div class="orders-container">
    <h2>我的订单</h2>
    
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="全部" name="all"></el-tab-pane>
      <el-tab-pane label="待支付" name="pending"></el-tab-pane>
      <el-tab-pane label="已支付" name="paid"></el-tab-pane>
      <el-tab-pane label="已完成" name="completed"></el-tab-pane>
      <el-tab-pane label="已取消" name="cancelled"></el-tab-pane>
    </el-tabs>
    
    <div v-loading="loading" class="orders-list">
      <el-empty v-if="orders.length === 0" description="暂无订单" />
      
      <div v-for="order in orders" :key="order.id" class="order-card">
        <div class="order-header">
          <span class="order-no">订单号: {{ order.order_no }}</span>
          <el-tag :type="getStatusType(order.status)">{{ getStatusText(order.status) }}</el-tag>
        </div>
        
        <div class="order-items">
          <div v-for="item in order.items" :key="item.id" class="order-item">
            <img :src="item.product_cover" :alt="item.product_title" />
            <div class="item-info">
              <h4>{{ item.product_title }}</h4>
              <p class="price">¥{{ (item.price / 100).toFixed(2) }}</p>
            </div>
          </div>
        </div>
        
        <div class="order-footer">
          <div class="total">
            <span>总计:</span>
            <span class="amount">¥{{ (order.total_amount / 100).toFixed(2) }}</span>
          </div>
          <div class="actions">
            <el-button v-if="order.status === 'pending'" type="primary" size="small" @click="handlePay(order.id)">
              去支付
            </el-button>
            <el-button v-if="order.status === 'pending'" size="small" @click="handleCancel(order.id)">
              取消订单
            </el-button>
            <el-button v-if="order.status === 'delivered'" type="success" size="small" @click="handleComplete(order.id)">
              确认收货
            </el-button>
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
      @current-change="fetchOrders"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useOrderStore } from '@/stores/order'

const orderStore = useOrderStore()

const activeTab = ref('all')
const loading = ref(false)
const orders = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const fetchOrders = async () => {
  loading.value = true
  try {
    const status = activeTab.value === 'all' ? undefined : activeTab.value
    const result = await orderStore.fetchOrders({
      status,
      page: currentPage.value,
      page_size: pageSize.value
    })
    orders.value = result.items
    total.value = result.total
  } catch (error: any) {
    ElMessage.error(error.message || '获取订单列表失败')
  } finally {
    loading.value = false
  }
}

const handleTabChange = () => {
  currentPage.value = 1
  fetchOrders()
}

const handlePay = async (orderId: string) => {
  try {
    await ElMessageBox.confirm('确认支付此订单？', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const result = await orderStore.payOrder(orderId, 'alipay')
    
    // 检查支付结果
    if (result.success) {
      ElMessage.success(result.message || '支付成功')
    } else {
      ElMessage.error(result.message || '支付失败，请重试')
    }
    
    // 无论成功失败都刷新订单列表
    fetchOrders()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '支付失败')
    }
  }
}

const handleCancel = async (orderId: string) => {
  try {
    await ElMessageBox.confirm('确认取消此订单？', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await orderStore.cancelOrder(orderId)
    ElMessage.success('订单已取消')
    fetchOrders()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '取消订单失败')
    }
  }
}

const handleComplete = async (orderId: string) => {
  try {
    await ElMessageBox.confirm('确认收货？', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info'
    })
    
    await orderStore.confirmDelivery(orderId)
    ElMessage.success('订单已完成')
    fetchOrders()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '操作失败')
    }
  }
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    pending: 'warning',
    paid: 'info',
    delivered: 'primary',
    completed: 'success',
    cancelled: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待支付',
    paid: '已支付',
    delivered: '已发货',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status] || status
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped>
.orders-container {
  padding: 20px;
}

h2 {
  margin-bottom: 20px;
  color: var(--text);
}

.orders-list {
  margin-top: 20px;
  min-height: 400px;
}

.order-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.order-no {
  font-size: 14px;
  color: var(--muted);
}

.order-items {
  margin-bottom: 16px;
}

.order-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
}

.order-item img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
}

.item-info {
  flex: 1;
}

.item-info h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--text);
}

.item-info .price {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--accent);
}

.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.total {
  font-size: 14px;
  color: var(--text);
}

.total .amount {
  font-size: 18px;
  font-weight: 600;
  color: var(--accent);
  margin-left: 8px;
}

.actions {
  display: flex;
  gap: 8px;
}

.el-pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
