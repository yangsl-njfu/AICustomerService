import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/api/client'
import type { Product } from './product'

export interface OrderItem {
  id: string
  order_id: string
  product_id: string
  product_title: string
  product_cover: string
  quantity: number
  price: number
  subtotal: number
  product?: Product
}

export interface Order {
  id: string
  order_no: string
  buyer_id: string
  seller_id: string
  total_amount: number
  status: 'pending' | 'paid' | 'delivered' | 'completed' | 'cancelled' | 'refunded'
  payment_method?: string
  payment_time?: string
  delivery_time?: string
  completion_time?: string
  cancellation_time?: string
  cancellation_reason?: string
  created_at: string
  updated_at?: string
  items?: OrderItem[]
  seller?: {
    id: string
    username: string
  }
}

export interface CreateOrderRequest {
  product_ids: string[]
  payment_method?: string
}

export interface OrderListResponse {
  items: Order[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const useOrderStore = defineStore('order', () => {
  const orders = ref<Order[]>([])
  const currentOrder = ref<Order | null>(null)
  const loading = ref(false)
  const page = ref(1)
  const pageSize = ref(20)
  const total = ref(0)
  const totalPages = ref(0)

  const hasMore = computed(() => {
    return page.value < totalPages.value
  })

  async function createOrder(productIds: string[], paymentMethod?: string) {
    loading.value = true
    try {
      const response = await apiClient.post<Order>('/orders', {
        product_ids: productIds,
        payment_method: paymentMethod
      })
      
      currentOrder.value = response
      
      return response
    } catch (error) {
      console.error('创建订单失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchOrders(params?: { status?: string; page?: number; page_size?: number }) {
    loading.value = true
    try {
      if (params?.page) page.value = params.page
      if (params?.page_size) pageSize.value = params.page_size
      
      const response = await apiClient.get<OrderListResponse>('/orders', {
        params: {
          status: params?.status,
          page: page.value,
          page_size: pageSize.value
        }
      })
      
      orders.value = response.items
      total.value = response.total
      totalPages.value = response.total_pages
      
      return response
    } catch (error) {
      console.error('获取订单列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchOrderDetail(orderId: string) {
    loading.value = true
    try {
      const order = await apiClient.get<Order>(`/orders/${orderId}`)
      currentOrder.value = order
      return order
    } catch (error) {
      console.error('获取订单详情失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function payOrder(orderId: string, paymentMethod: string) {
    loading.value = true
    try {
      const response = await apiClient.post<{ success: boolean; message: string; order: Order }>(
        `/orders/${orderId}/pay`,
        { payment_method: paymentMethod }
      )
      
      // 更新当前订单
      if (currentOrder.value?.id === orderId) {
        currentOrder.value = response.order
      }
      
      // 更新列表中的订单
      if (orders.value && Array.isArray(orders.value)) {
        const index = orders.value.findIndex(o => o.id === orderId)
        if (index !== -1) {
          orders.value[index] = response.order
        }
      }
      
      return response
    } catch (error) {
      console.error('支付订单失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function cancelOrder(orderId: string, reason?: string) {
    loading.value = true
    try {
      const response = await apiClient.post<{ success: boolean; message: string; order: Order }>(
        `/orders/${orderId}/cancel`,
        { reason }
      )
      
      // 更新当前订单
      if (currentOrder.value?.id === orderId) {
        currentOrder.value = response.order
      }
      
      // 更新列表中的订单
      if (orders.value && Array.isArray(orders.value)) {
        const index = orders.value.findIndex(o => o.id === orderId)
        if (index !== -1) {
          orders.value[index] = response.order
        }
      }
      
      return response
    } catch (error) {
      console.error('取消订单失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function confirmDelivery(orderId: string) {
    loading.value = true
    try {
      const response = await apiClient.post<{ success: boolean; message: string; order: Order }>(
        `/orders/${orderId}/complete`
      )
      
      // 更新当前订单
      if (currentOrder.value?.id === orderId) {
        currentOrder.value = response.order
      }
      
      // 更新列表中的订单
      if (orders.value && Array.isArray(orders.value)) {
        const index = orders.value.findIndex(o => o.id === orderId)
        if (index !== -1) {
          orders.value[index] = response.order
        }
      }
      
      return response
    } catch (error) {
      console.error('确认收货失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  function getOrderStatusText(status: string): string {
    const statusMap: Record<string, string> = {
      pending: '待支付',
      paid: '已支付',
      delivered: '已交付',
      completed: '已完成',
      cancelled: '已取消',
      refunded: '已退款'
    }
    return statusMap[status] || status
  }

  function getOrderStatusColor(status: string): string {
    const colorMap: Record<string, string> = {
      pending: 'warning',
      paid: 'info',
      delivered: 'primary',
      completed: 'success',
      cancelled: 'default',
      refunded: 'error'
    }
    return colorMap[status] || 'default'
  }

  function nextPage() {
    if (hasMore.value) {
      page.value += 1
      fetchOrders()
    }
  }

  function prevPage() {
    if (page.value > 1) {
      page.value -= 1
      fetchOrders()
    }
  }

  return {
    orders,
    currentOrder,
    loading,
    page,
    pageSize,
    total,
    totalPages,
    hasMore,
    createOrder,
    fetchOrders,
    fetchOrderDetail,
    payOrder,
    cancelOrder,
    confirmDelivery,
    getOrderStatusText,
    getOrderStatusColor,
    nextPage,
    prevPage
  }
})
