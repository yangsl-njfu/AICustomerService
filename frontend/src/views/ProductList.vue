<template>
  <div class="product-list-page">
    <!-- Hero Section -->
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="gradient-text">毕业设计作品</span>
        </h1>
        <p class="hero-subtitle">精选优质项目 · 助力学业成功 · 专业技术支持</p>
        
        <!-- 搜索栏 -->
        <div class="hero-search">
          <input 
            v-model="keyword" 
            type="text" 
            placeholder="搜索你需要的毕业设计项目..."
            @keyup.enter="handleSearch"
          />
          <button @click="handleSearch" class="search-btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            搜索
          </button>
        </div>
      </div>
    </div>

    <!-- 分类快捷选择 -->
    <div class="category-chips">
      <div 
        class="chip"
        :class="{ active: !searchParams.category_id }"
        @click="selectCategory(undefined)"
      >
        全部
      </div>
      <div 
        v-for="category in categories" 
        :key="category.id"
        class="chip"
        :class="{ active: searchParams.category_id === category.id }"
        @click="selectCategory(category.id)"
      >
        {{ category.name }}
      </div>
    </div>

    <!-- 筛选和排序工具栏 -->
    <div class="toolbar">
      <div class="filter-group">
        <div class="filter-item">
          <label>难度</label>
          <select v-model="searchParams.difficulty" @change="handleSort">
            <option :value="undefined">全部</option>
            <option value="easy">简单</option>
            <option value="medium">中等</option>
            <option value="hard">困难</option>
          </select>
        </div>

        <div class="filter-item">
          <label>价格</label>
          <div class="price-inputs">
            <input 
              v-model.number="priceRange.min" 
              type="number" 
              placeholder="最低"
              @change="applyPriceFilter"
            />
            <span>-</span>
            <input 
              v-model.number="priceRange.max" 
              type="number" 
              placeholder="最高"
              @change="applyPriceFilter"
            />
          </div>
        </div>
      </div>

      <div class="sort-group">
        <select v-model="searchParams.sort_by" @change="handleSort" class="sort-select">
          <option value="created_at">最新发布</option>
          <option value="sales_count">销量最高</option>
          <option value="rating">评分最高</option>
          <option value="price">价格排序</option>
        </select>
        <select v-model="searchParams.order" @change="handleSort" class="order-select">
          <option value="desc">↓ 降序</option>
          <option value="asc">↑ 升序</option>
        </select>
        <button class="reset-btn" @click="resetFilters">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
            <path d="M21 3v5h-5"></path>
            <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
            <path d="M3 21v-5h5"></path>
          </svg>
          重置
        </button>
      </div>
    </div>

    <!-- 商品网格 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
    
    <div v-else-if="products.length === 0" class="empty-state">
      <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="11" cy="11" r="8"></circle>
        <path d="m21 21-4.35-4.35"></path>
      </svg>
      <h3>暂无商品</h3>
      <p>试试调整筛选条件或搜索其他关键词</p>
    </div>

    <div v-else class="products-container">
      <div class="product-grid">
        <ProductCard 
          v-for="product in products" 
          :key="product.id" 
          :product="product"
        />
      </div>

      <!-- 分页 -->
      <div class="pagination" v-if="totalPages > 1">
        <button 
          class="page-btn"
          :disabled="searchParams.page === 1" 
          @click="prevPage"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
          上一页
        </button>
        <div class="page-info">
          <span class="current-page">{{ searchParams.page }}</span>
          <span class="separator">/</span>
          <span class="total-pages">{{ totalPages }}</span>
        </div>
        <button 
          class="page-btn"
          :disabled="searchParams.page === totalPages" 
          @click="nextPage"
        >
          下一页
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useProductStore } from '@/stores/product'
import { storeToRefs } from 'pinia'
import ProductCard from '@/components/ProductCard.vue'

const productStore = useProductStore()
const { products, categories, loading, searchParams, totalPages } = storeToRefs(productStore)

const keyword = ref('')
const priceRange = reactive({ min: undefined, max: undefined })

onMounted(async () => {
  await productStore.fetchCategories()
  await productStore.fetchProducts()
})

function selectCategory(categoryId: string | undefined) {
  searchParams.value.category_id = categoryId
  searchParams.value.page = 1
  productStore.fetchProducts()
}

function applyPriceFilter() {
  searchParams.value.min_price = priceRange.min
  searchParams.value.max_price = priceRange.max
  searchParams.value.page = 1
  productStore.fetchProducts()
}

function handleSearch() {
  productStore.searchProducts(keyword.value)
}

function handleSort() {
  productStore.fetchProducts()
}

function resetFilters() {
  productStore.resetSearch()
  keyword.value = ''
  priceRange.min = undefined
  priceRange.max = undefined
  productStore.fetchProducts()
}

function nextPage() {
  productStore.nextPage()
}

function prevPage() {
  productStore.prevPage()
}
</script>

<style scoped>
.product-list-page {
  min-height: 100%;
  background: var(--bg);
  padding: 24px 32px;
}

/* Hero Section */
.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 48px 40px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-lg);
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
}

.hero-title {
  font-size: 42px;
  font-weight: 700;
  margin-bottom: 12px;
  letter-spacing: -0.02em;
}

.gradient-text {
  color: white;
}

.hero-subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 28px;
  font-weight: 400;
}

.hero-search {
  display: flex;
  gap: 12px;
  max-width: 600px;
  margin: 0 auto;
}

.hero-search input {
  flex: 1;
  padding: 14px 20px;
  background: white;
  border: none;
  border-radius: 12px;
  color: var(--text);
  font-size: 15px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.hero-search input:focus {
  outline: none;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.hero-search input::placeholder {
  color: var(--text-muted);
}

.search-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  background: white;
  border: none;
  border-radius: 12px;
  color: #667eea;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.search-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

/* Category Chips */
.category-chips {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.chip {
  padding: 10px 20px;
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: 24px;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.chip:hover {
  border-color: var(--primary);
  color: var(--primary);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.chip.active {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
  box-shadow: var(--shadow);
}

/* Toolbar */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 16px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  align-items: center;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.filter-item select,
.sort-select,
.order-select {
  padding: 8px 16px;
  background: var(--bg-light);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-item select:hover,
.sort-select:hover,
.order-select:hover {
  border-color: var(--primary);
}

.filter-item select:focus,
.sort-select:focus,
.order-select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-lighter);
}

.price-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.price-inputs input {
  width: 90px;
  padding: 8px 12px;
  background: var(--bg-light);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 14px;
}

.price-inputs input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-lighter);
}

.price-inputs span {
  color: var(--text-muted);
}

.sort-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.reset-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.reset-btn:hover {
  background: var(--danger);
  border-color: var(--danger);
  color: white;
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
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
  gap: 16px;
}

.empty-state svg {
  color: var(--text-muted);
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.empty-state p {
  color: var(--text-secondary);
  font-size: 15px;
  margin: 0;
}

/* Products Container */
.products-container {
  margin-bottom: 40px;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  padding: 32px 0;
}

.page-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  font-weight: 600;
}

.current-page {
  color: var(--primary);
  font-size: 18px;
}

.separator {
  color: var(--text-muted);
  font-size: 16px;
}

.total-pages {
  color: var(--text-secondary);
  font-size: 16px;
}

/* Responsive */
@media (max-width: 768px) {
  .product-list-page {
    padding: 16px;
  }

  .hero-section {
    padding: 32px 24px;
  }

  .hero-title {
    font-size: 28px;
  }

  .hero-subtitle {
    font-size: 14px;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group,
  .sort-group {
    width: 100%;
    justify-content: space-between;
  }

  .product-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 16px;
  }
}
</style>
