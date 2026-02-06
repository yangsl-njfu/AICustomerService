<template>
  <div class="product-detail-page" v-if="currentProduct">
    <div class="product-main">
      <div class="product-gallery">
        <img :src="currentProduct.cover_image || '/placeholder.png'" :alt="currentProduct.title" />
      </div>

      <div class="product-summary">
        <h1>{{ currentProduct.title }}</h1>
        
        <div class="product-rating">
          <span class="rating">⭐ {{ currentProduct.rating.toFixed(1) }}</span>
          <span class="reviews">{{ currentProduct.review_count }} 评价</span>
          <span class="sales">销量 {{ currentProduct.sales_count }}</span>
        </div>

        <div class="product-price">
          <span class="price">¥{{ currentProduct.price.toFixed(2) }}</span>
          <span class="original-price" v-if="currentProduct.original_price">
            ¥{{ currentProduct.original_price.toFixed(2) }}
          </span>
        </div>

        <div class="product-meta">
          <div class="meta-item">
            <span class="label">难度：</span>
            <span class="value">{{ difficultyText }}</span>
          </div>
          <div class="meta-item">
            <span class="label">技术栈：</span>
            <span class="value">{{ currentProduct.tech_stack?.join(', ') }}</span>
          </div>
        </div>

        <div class="product-actions">
          <button class="btn-primary" @click="handleAddToCart">加入购物车</button>
          <button class="btn-secondary" @click="handleBuyNow">立即购买</button>
        </div>
      </div>
    </div>

    <div class="product-details">
      <div class="tabs">
        <div class="tab" :class="{ active: activeTab === 'description' }" @click="activeTab = 'description'">
          商品详情
        </div>
        <div class="tab" :class="{ active: activeTab === 'reviews' }" @click="activeTab = 'reviews'">
          用户评价
        </div>
      </div>

      <div class="tab-content">
        <div v-if="activeTab === 'description'" class="description">
          <p>{{ currentProduct.description }}</p>
        </div>
        <div v-else class="reviews">
          <p>评价列表...</p>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="loading">加载中...</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProductStore } from '@/stores/product'
import { useCartStore } from '@/stores/cart'
import { storeToRefs } from 'pinia'

const route = useRoute()
const router = useRouter()
const productStore = useProductStore()
const cartStore = useCartStore()
const { currentProduct } = storeToRefs(productStore)

const activeTab = ref('description')

const difficultyText = computed(() => {
  const map: Record<string, string> = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return map[currentProduct.value?.difficulty || ''] || currentProduct.value?.difficulty
})

onMounted(async () => {
  const productId = route.params.id as string
  await productStore.fetchProductDetail(productId)
})

async function handleAddToCart() {
  if (!currentProduct.value) return
  try {
    await cartStore.addToCart(currentProduct.value.id)
    alert('已添加到购物车')
  } catch (error) {
    alert('添加失败')
  }
}

async function handleBuyNow() {
  if (!currentProduct.value) return
  await handleAddToCart()
  router.push('/cart')
}
</script>

<style scoped>
.product-detail-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.product-main {
  display: flex;
  gap: 40px;
  margin-bottom: 40px;
  background: white;
  padding: 30px;
  border-radius: 8px;
}

.product-gallery {
  flex: 1;
}

.product-gallery img {
  width: 100%;
  border-radius: 8px;
}

.product-summary {
  flex: 1;
}

.product-summary h1 {
  font-size: 24px;
  margin-bottom: 16px;
}

.product-rating {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  color: #666;
}

.product-price {
  margin-bottom: 24px;
}

.price {
  font-size: 32px;
  color: #ff4d4f;
  font-weight: 600;
}

.original-price {
  font-size: 18px;
  color: #999;
  text-decoration: line-through;
  margin-left: 12px;
}

.product-meta {
  margin-bottom: 32px;
}

.meta-item {
  margin-bottom: 12px;
}

.label {
  color: #666;
  margin-right: 8px;
}

.product-actions {
  display: flex;
  gap: 16px;
}

.btn-primary, .btn-secondary {
  flex: 1;
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

.btn-primary {
  background: #1890ff;
  color: white;
}

.btn-secondary {
  background: #ff4d4f;
  color: white;
}

.product-details {
  background: white;
  padding: 30px;
  border-radius: 8px;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 24px;
}

.tab {
  padding: 12px 24px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}

.tab.active {
  color: #1890ff;
  border-bottom-color: #1890ff;
}

.loading {
  text-align: center;
  padding: 60px;
}
</style>
