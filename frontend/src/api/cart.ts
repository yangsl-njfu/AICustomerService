import { apiClient } from './client'
import type { CartItem, CartResponse } from '@/stores/cart'

export const cartApi = {
  // 获取购物车
  async getCart(): Promise<CartResponse> {
    return apiClient.get<CartResponse>('/cart')
  },

  // 添加到购物车
  async addToCart(productId: string, quantity: number = 1): Promise<CartItem> {
    return apiClient.post<CartItem>('/cart', {
      product_id: productId,
      quantity
    })
  },

  // 从购物车删除
  async removeFromCart(productId: string): Promise<void> {
    return apiClient.delete<void>(`/cart/${productId}`)
  }
}
