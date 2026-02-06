import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/api/client'
import type { Product } from './product'

export interface CartItem {
  id: string
  user_id: string
  product_id: string
  quantity: number
  created_at: string
  product?: Product
}

export interface CartResponse {
  items: CartItem[]
  total_amount: number
  total_items: number
}

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const loading = ref(false)

  const totalAmount = computed(() => {
    return items.value.reduce((sum, item) => {
      const price = item.product?.price || 0
      return sum + price * item.quantity
    }, 0)
  })

  const totalItems = computed(() => {
    return items.value.reduce((sum, item) => sum + item.quantity, 0)
  })

  const itemCount = computed(() => {
    return items.value.length
  })

  async function fetchCart() {
    loading.value = true
    try {
      const response = await apiClient.get<CartResponse>('/cart')
      items.value = response.items
      return response
    } catch (error) {
      console.error('获取购物车失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function addToCart(productId: string, quantity: number = 1) {
    loading.value = true
    try {
      const response = await apiClient.post<CartItem>('/cart', {
        product_id: productId,
        quantity
      })
      
      // 刷新购物车
      await fetchCart()
      
      return response
    } catch (error) {
      console.error('添加到购物车失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function removeFromCart(productId: string) {
    loading.value = true
    try {
      await apiClient.delete(`/cart/${productId}`)
      
      // 从本地列表中移除
      items.value = items.value.filter(item => item.product_id !== productId)
      
      return true
    } catch (error) {
      console.error('从购物车删除失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function updateQuantity(productId: string, quantity: number) {
    if (quantity <= 0) {
      return removeFromCart(productId)
    }

    loading.value = true
    try {
      await apiClient.put(`/cart/${productId}`, {
        quantity
      })
      
      // 更新本地数量
      const item = items.value.find(i => i.product_id === productId)
      if (item) {
        item.quantity = quantity
      }
      
      return true
    } catch (error) {
      console.error('更新数量失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function clearCart() {
    loading.value = true
    try {
      // 删除所有商品
      await Promise.all(
        items.value.map(item => apiClient.delete(`/cart/${item.product_id}`))
      )
      
      items.value = []
      
      return true
    } catch (error) {
      console.error('清空购物车失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  function isInCart(productId: string): boolean {
    return items.value.some(item => item.product_id === productId)
  }

  function getItemQuantity(productId: string): number {
    const item = items.value.find(i => i.product_id === productId)
    return item?.quantity || 0
  }

  return {
    items,
    loading,
    totalAmount,
    totalItems,
    itemCount,
    fetchCart,
    addToCart,
    removeFromCart,
    updateQuantity,
    clearCart,
    isInCart,
    getItemQuantity
  }
})
