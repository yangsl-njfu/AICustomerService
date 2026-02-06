import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/api/client'

export interface Product {
  id: string
  title: string
  description: string
  price: number
  original_price?: number
  cover_image?: string
  demo_video?: string
  tech_stack: string[]
  difficulty: 'easy' | 'medium' | 'hard'
  status: string
  view_count: number
  sales_count: number
  rating: number
  review_count: number
  created_at: string
  updated_at?: string
  seller?: {
    id: string
    username: string
  }
  category?: {
    id: string
    name: string
  }
  images?: Array<{
    id: string
    url: string
    sort_order: number
  }>
  files?: Array<{
    id: string
    name: string
    type: string
    size: number
    description?: string
  }>
}

export interface Category {
  id: string
  name: string
  parent_id?: string
  description?: string
  icon?: string
  sort_order: number
  created_at: string
  children?: Category[]
}

export interface ProductSearchParams {
  keyword?: string
  category_id?: string
  min_price?: number
  max_price?: number
  difficulty?: string
  tech_stack?: string[]
  sort_by?: 'created_at' | 'price' | 'sales' | 'rating'
  order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

export interface ProductListResponse {
  products: Product[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const useProductStore = defineStore('product', () => {
  const products = ref<Product[]>([])
  const currentProduct = ref<Product | null>(null)
  const categories = ref<Category[]>([])
  const loading = ref(false)
  const searchParams = ref<ProductSearchParams>({
    page: 1,
    page_size: 20,
    sort_by: 'created_at',
    order: 'desc'
  })
  const totalPages = ref(0)
  const total = ref(0)

  const hasMore = computed(() => {
    return searchParams.value.page! < totalPages.value
  })

  async function fetchProducts(params?: ProductSearchParams) {
    loading.value = true
    try {
      if (params) {
        searchParams.value = { ...searchParams.value, ...params }
      }
      
      const response = await apiClient.get<ProductListResponse>('/products', {
        params: searchParams.value
      })
      
      products.value = response.products
      total.value = response.total
      totalPages.value = response.total_pages
      
      return response
    } catch (error) {
      console.error('获取商品列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchProductDetail(productId: string) {
    loading.value = true
    try {
      const product = await apiClient.get<Product>(`/products/${productId}`)
      currentProduct.value = product
      return product
    } catch (error) {
      console.error('获取商品详情失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function searchProducts(keyword: string, params?: ProductSearchParams) {
    return fetchProducts({
      ...params,
      keyword,
      page: 1
    })
  }

  async function fetchCategories() {
    try {
      categories.value = await apiClient.get<Category[]>('/products/categories')
      return categories.value
    } catch (error) {
      console.error('获取分类列表失败:', error)
      throw error
    }
  }

  async function createProduct(productData: any) {
    loading.value = true
    try {
      const product = await apiClient.post<Product>('/products', productData)
      return product
    } catch (error) {
      console.error('创建商品失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function updateProduct(productId: string, productData: any) {
    loading.value = true
    try {
      const product = await apiClient.put<Product>(`/products/${productId}`, productData)
      
      // 更新当前商品
      if (currentProduct.value?.id === productId) {
        currentProduct.value = product
      }
      
      // 更新列表中的商品
      const index = products.value.findIndex(p => p.id === productId)
      if (index !== -1) {
        products.value[index] = product
      }
      
      return product
    } catch (error) {
      console.error('更新商品失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function deleteProduct(productId: string) {
    loading.value = true
    try {
      await apiClient.delete(`/products/${productId}`)
      
      // 从列表中移除
      products.value = products.value.filter(p => p.id !== productId)
      
      // 清空当前商品
      if (currentProduct.value?.id === productId) {
        currentProduct.value = null
      }
      
      return true
    } catch (error) {
      console.error('删除商品失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  function resetSearch() {
    searchParams.value = {
      page: 1,
      page_size: 20,
      sort_by: 'created_at',
      order: 'desc'
    }
  }

  function nextPage() {
    if (hasMore.value) {
      searchParams.value.page = (searchParams.value.page || 1) + 1
      fetchProducts()
    }
  }

  function prevPage() {
    if (searchParams.value.page && searchParams.value.page > 1) {
      searchParams.value.page -= 1
      fetchProducts()
    }
  }

  return {
    products,
    currentProduct,
    categories,
    loading,
    searchParams,
    total,
    totalPages,
    hasMore,
    fetchProducts,
    fetchProductDetail,
    searchProducts,
    fetchCategories,
    createProduct,
    updateProduct,
    deleteProduct,
    resetSearch,
    nextPage,
    prevPage
  }
})
