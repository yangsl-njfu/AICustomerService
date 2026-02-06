<template>
  <div class="favorites-container">
    <h2>我的收藏</h2>
    
    <div v-loading="loading" class="favorites-grid">
      <el-empty v-if="favorites.length === 0" description="暂无收藏" />
      
      <div v-for="item in favorites" :key="item.favorite_id" class="favorite-card">
        <div class="product-image" @click="goToDetail(item.product_id)">
          <img :src="item.cover_image" :alt="item.title" />
        </div>
        <div class="product-info">
          <h3 @click="goToDetail(item.product_id)">{{ item.title }}</h3>
          <p class="description">{{ item.description }}</p>
          <div class="footer">
            <span class="price">¥{{ item.price.toFixed(2) }}</span>
            <div class="actions">
              <el-button type="primary" size="small" @click="addToCart(item.product_id)">
                加入购物车
              </el-button>
              <el-button size="small" @click="removeFavorite(item.product_id)">
                取消收藏
              </el-button>
            </div>
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
      @current-change="fetchFavorites"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiClient } from '@/api/client'

const router = useRouter()

const loading = ref(false)
const favorites = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)

const fetchFavorites = async () => {
  loading.value = true
  try {
    console.log('[DEBUG] 开始请求收藏列表...')
    const response = await apiClient.get('/favorites', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      }
    })
    console.log('[DEBUG] 收到响应:', response)
    
    // axios 返回的数据在 response.data 中，但如果 apiClient 已经处理过，可能直接在 response 中
    const data = response.data || response
    console.log('[DEBUG] 响应数据:', data)
    
    if (!data) {
      console.error('[ERROR] 响应数据为空')
      ElMessage.error('服务器返回数据为空')
      favorites.value = []
      total.value = 0
      return
    }
    
    if (!data.items) {
      console.error('[ERROR] 响应数据中没有 items 字段:', data)
      ElMessage.error('数据格式错误：缺少 items 字段')
      favorites.value = []
      total.value = 0
      return
    }
    
    favorites.value = data.items || []
    total.value = data.total || 0
    console.log('[DEBUG] 设置收藏列表成功，共', favorites.value.length, '条')
  } catch (error: any) {
    console.error('[ERROR] 请求失败:', error)
    ElMessage.error(error.message || '获取收藏列表失败')
    favorites.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const goToDetail = (productId: string) => {
  router.push(`/products/${productId}`)
}

const addToCart = async (productId: string) => {
  try {
    await apiClient.post('/cart', { product_id: productId })
    ElMessage.success('已加入购物车')
  } catch (error: any) {
    ElMessage.error(error.message || '加入购物车失败')
  }
}

const removeFavorite = async (productId: string) => {
  try {
    await ElMessageBox.confirm('确认取消收藏？', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await apiClient.delete(`/favorites/${productId}`)
    ElMessage.success('已取消收藏')
    fetchFavorites()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '取消收藏失败')
    }
  }
}

onMounted(() => {
  fetchFavorites()
})
</script>

<style scoped>
.favorites-container {
  padding: 20px;
}

h2 {
  margin-bottom: 20px;
  color: var(--text);
}

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  min-height: 400px;
}

.favorite-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.favorite-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.product-image {
  width: 100%;
  height: 200px;
  overflow: hidden;
  cursor: pointer;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.product-image:hover img {
  transform: scale(1.05);
}

.product-info {
  padding: 16px;
}

.product-info h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: var(--text);
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-info h3:hover {
  color: var(--accent);
}

.description {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--muted);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.price {
  font-size: 20px;
  font-weight: 600;
  color: var(--accent);
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
