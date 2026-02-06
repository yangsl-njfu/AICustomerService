import { apiClient } from './client'
import type { Order, OrderListResponse } from '@/stores/order'

export const orderApi = {
  // 创建订单
  async createOrder(productIds: string[], paymentMethod?: string): Promise<Order> {
    return apiClient.post<Order>('/orders', {
      product_ids: productIds,
      payment_method: paymentMethod
    })
  },

  // 获取订单列表
  async getOrders(params?: { status?: string; page?: number; page_size?: number }): Promise<OrderListResponse> {
    return apiClient.get<OrderListResponse>('/orders', { params })
  },

  // 获取订单详情
  async getOrder(id: string): Promise<Order> {
    return apiClient.get<Order>(`/orders/${id}`)
  },

  // 支付订单
  async payOrder(id: string, paymentMethod: string): Promise<{ success: boolean; message: string; order: Order }> {
    return apiClient.post(`/orders/${id}/pay`, { payment_method: paymentMethod })
  },

  // 取消订单
  async cancelOrder(id: string, reason?: string): Promise<{ success: boolean; message: string; order: Order }> {
    return apiClient.post(`/orders/${id}/cancel`, { reason })
  }
}
