<template>
  <div class="cart-page">
    <div class="page-header">
      <h1>购物车</h1>
      <p v-if="!loading && items.length > 0">共 {{ totalItems }} 件商品</p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
    
    <div v-else-if="items.length === 0" class="empty-state">
      <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="9" cy="21" r="1"></circle>
        <circle cx="20" cy="21" r="1"></circle>
        <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
      </svg>
      <h3>购物车是空的</h3>
      <p>快去挑选心仪的商品吧</p>
      <button class="browse-btn" @click="$router.push('/products')">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
          <polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>
        去逛逛
      </button>
    </div>

    <div v-else class="cart-content">
      <div class="cart-items">
        <div v-for="item in items" :key="item.id" class="cart-item">
          <div class="item-image">
            <img :src="item.product?.cover_image || '/placeholder.png'" :alt="item.product?.title" />
          </div>
          
          <div class="item-details">
            <h3 class="item-title">{{ item.product?.title }}</h3>
            <p class="item-price">¥{{ (item.product?.price / 100).toFixed(2) }}</p>
            <div class="item-meta">
              <span class="difficulty" :class="`difficulty-${item.product?.difficulty}`">
                {{ getDifficultyText(item.product?.difficulty) }}
              </span>
            </div>
          </div>
          
          <div class="item-actions">
            <div class="quantity-control">
              <button 
                class="qty-btn" 
                @click="updateQuantity(item.product_id, item.quantity - 1)"
                :disabled="item.quantity <= 1"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
              </button>
              <span class="qty-value">{{ item.quantity }}</span>
              <button 
                class="qty-btn" 
                @click="updateQuantity(item.product_id, item.quantity + 1)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
              </button>
            </div>
            
            <div class="item-subtotal">
              ¥{{ ((item.product?.price || 0) / 100 * item.quantity).toFixed(2) }}
            </div>
            
            <button class="remove-btn" @click="removeItem(item.product_id)">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div class="cart-summary">
        <h3>订单摘要</h3>
        
        <div class="summary-details">
          <div class="summary-row">
            <span>商品件数</span>
            <span>{{ totalItems }} 件</span>
          </div>
          <div class="summary-row">
            <span>商品总价</span>
            <span>¥{{ (totalAmount / 100).toFixed(2) }}</span>
          </div>
        </div>
        
        <div class="summary-total">
          <span>总计</span>
          <span class="total-amount">¥{{ (totalAmount / 100).toFixed(2) }}</span>
        </div>
        
        <button class="checkout-btn" @click="handleCheckout">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
            <line x1="1" y1="10" x2="23" y2="10"></line>
          </svg>
          去结算
        </button>
        
        <button class="clear-btn" @click="handleClearCart">
          清空购物车
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '@/stores/cart'
import { useOrderStore } from '@/stores/order'
import { storeToRefs } from 'pinia'

const router = useRouter()
const cartStore = useCartStore()
const orderStore = useOrderStore()
const { items, loading, totalAmount, totalItems } = storeToRefs(cartStore)

onMounted(() => {
  cartStore.fetchCart()
})

function getDifficultyText(difficulty: string | undefined): string {
  const map: Record<string, string> = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return map[difficulty || ''] || difficulty || ''
}

async function updateQuantity(productId: string, quantity: number) {
  try {
    await cartStore.updateQuantity(productId, quantity)
  } catch (error) {
    alert('更新数量失败，请重试')
  }
}

async function removeItem(productId: string) {
  if (confirm('确定要删除这个商品吗？')) {
    try {
      await cartStore.removeFromCart(productId)
    } catch (error) {
      alert('删除失败，请重试')
    }
  }
}

async function handleClearCart() {
  if (confirm('确定要清空购物车吗？')) {
    try {
      await cartStore.clearCart()
    } catch (error) {
      alert('清空失败，请重试')
    }
  }
}

async function handleCheckout() {
  if (items.value.length === 0) {
    alert('购物车是空的')
    return
  }

  try {
    loading.value = true
    
    // 获取所有商品ID
    const productIds = items.value.map(item => item.product_id)
    
    console.log('准备创建订单，商品ID:', productIds)
    
    // 创建订单（后端会自动清空购物车）
    const order = await orderStore.createOrder(productIds)
    
    console.log('订单创建成功:', order)
    
    // 跳转到订单页面
    alert(`订单创建成功！订单号：${order.order_no}`)
    
    // 刷新购物车数据
    await cartStore.fetchCart()
    
    router.push('/orders')
    
  } catch (error: any) {
    console.error('结算失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '结算失败，请重试'
    alert(errorMsg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.cart-page {
  min-height: 100%;
  background: var(--bg);
  padding: 24px 32px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 8px 0;
}

.page-header p {
  color: var(--text-secondary);
  font-size: 15px;
  margin: 0;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  gap: 16px;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--border-light);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p {
  color: var(--text-secondary);
  font-size: 16px;
  font-weight: 500;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  gap: 20px;
  background: var(--surface);
  border-radius: 16px;
  border: 1px solid var(--border);
}

.empty-state svg {
  color: var(--text-muted);
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 22px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.empty-state p {
  color: var(--text-secondary);
  font-size: 15px;
  margin: 0;
}

.browse-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 8px;
}

.browse-btn:hover {
  background: var(--primary-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

/* Cart Content */
.cart-content {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.cart-items {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.cart-item:hover {
  box-shadow: var(--shadow);
}

.item-image {
  flex-shrink: 0;
}

.item-image img {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid var(--border-light);
}

.item-details {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.item-price {
  font-size: 20px;
  font-weight: 700;
  color: var(--danger);
  margin: 0 0 8px 0;
}

.item-meta {
  display: flex;
  gap: 8px;
}

.difficulty {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.difficulty-easy {
  background: #e6f7ff;
  color: #1890ff;
}

.difficulty-medium {
  background: #fff7e6;
  color: #fa8c16;
}

.difficulty-hard {
  background: #fff1f0;
  color: #ff4d4f;
}

.item-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.quantity-control {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--bg-light);
  border: 1px solid var(--border);
  border-radius: 24px;
}

.qty-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: var(--surface);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-secondary);
}

.qty-btn:hover:not(:disabled) {
  background: var(--primary);
  color: white;
  transform: scale(1.1);
}

.qty-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.qty-value {
  min-width: 32px;
  text-align: center;
  font-weight: 600;
  color: var(--text);
  font-size: 15px;
}

.item-subtotal {
  min-width: 100px;
  text-align: right;
  font-size: 20px;
  font-weight: 700;
  color: var(--danger);
}

.remove-btn {
  padding: 8px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-muted);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn:hover {
  background: var(--danger);
  border-color: var(--danger);
  color: white;
}

/* Cart Summary */
.cart-summary {
  width: 360px;
  flex-shrink: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 24px;
  border-radius: 12px;
  position: sticky;
  top: 24px;
}

.cart-summary h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 20px 0;
}

.summary-details {
  margin-bottom: 16px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.summary-row:not(:last-child) {
  border-bottom: 1px solid var(--border-light);
}

.summary-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-top: 2px solid var(--border);
  margin-bottom: 20px;
}

.summary-total span:first-child {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.total-amount {
  font-size: 24px;
  font-weight: 700;
  color: var(--danger);
}

.checkout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 12px;
}

.checkout-btn:hover {
  background: var(--primary-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.clear-btn {
  width: 100%;
  padding: 12px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.clear-btn:hover {
  background: var(--danger);
  border-color: var(--danger);
  color: white;
}

/* Responsive */
@media (max-width: 768px) {
  .cart-page {
    padding: 16px;
  }

  .cart-content {
    flex-direction: column;
  }

  .cart-summary {
    width: 100%;
    position: static;
  }

  .cart-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .item-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
