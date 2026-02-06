<template>
  <div class="product-card" @click="goToDetail">
    <div class="product-image">
      <img :src="product.cover_image || '/placeholder.png'" :alt="product.title" />
      <div class="product-badge" v-if="product.original_price">
        <span class="discount">特惠</span>
      </div>
    </div>
    
    <div class="product-info">
      <h3 class="product-title">{{ product.title }}</h3>
      
      <div class="product-meta">
        <span class="difficulty" :class="`difficulty-${product.difficulty}`">
          {{ difficultyText }}
        </span>
        <span class="tech-stack" v-if="product.tech_stack && product.tech_stack.length > 0">
          {{ product.tech_stack.slice(0, 2).join(', ') }}
          <span v-if="product.tech_stack.length > 2">...</span>
        </span>
      </div>
      
      <div class="product-stats">
        <span class="rating">
          <span class="star">⭐</span>
          {{ product.rating.toFixed(1) }}
        </span>
        <span class="sales">销量 {{ product.sales_count }}</span>
      </div>
      
      <div class="product-footer">
        <div class="price-section">
          <span class="price">¥{{ product.price.toFixed(2) }}</span>
          <span class="original-price" v-if="product.original_price">
            ¥{{ product.original_price.toFixed(2) }}
          </span>
        </div>
        
        <button class="add-cart-btn" @click.stop="handleAddToCart">
          加入购物车
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '@/stores/cart'
import type { Product } from '@/stores/product'

const props = defineProps<{
  product: Product
}>()

const router = useRouter()
const cartStore = useCartStore()

const difficultyText = computed(() => {
  const map: Record<string, string> = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return map[props.product.difficulty] || props.product.difficulty
})

function goToDetail() {
  router.push(`/products/${props.product.id}`)
}

async function handleAddToCart() {
  try {
    await cartStore.addToCart(props.product.id)
    alert('已添加到购物车')
  } catch (error) {
    alert('添加失败，请重试')
  }
}
</script>

<style scoped>
.product-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--surface);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.product-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
  border-color: var(--primary-light);
}

.product-image {
  position: relative;
  width: 100%;
  padding-top: 66.67%; /* 3:2 aspect ratio */
  overflow: hidden;
  background: var(--bg-light);
}

.product-image img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.product-card:hover .product-image img {
  transform: scale(1.05);
}

.product-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 1;
}

.discount {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(245, 87, 108, 0.3);
}

.product-info {
  padding: 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.product-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.5;
  min-height: 45px;
}

.product-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
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

.tech-stack {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 4px 10px;
  background: var(--bg-light);
  border-radius: 12px;
}

.product-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--text-secondary);
}

.rating {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}

.star {
  font-size: 14px;
}

.sales {
  font-weight: 500;
}

.product-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  margin-top: auto;
  border-top: 1px solid var(--border-light);
}

.price-section {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.price {
  font-size: 22px;
  font-weight: 700;
  color: var(--danger);
}

.original-price {
  font-size: 14px;
  color: var(--text-muted);
  text-decoration: line-through;
}

.add-cart-btn {
  padding: 8px 16px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.add-cart-btn:hover {
  background: var(--primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}
</style>
