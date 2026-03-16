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
  items?: Product[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

type ProductListAPIResponse = Partial<ProductListResponse> & {
  products?: Product[]
  items?: Product[]
}

type CategoryAPIResponse = Category[] | {
  categories?: Category[]
}

const DEFAULT_SEARCH_PARAMS: ProductSearchParams = {
  page: 1,
  page_size: 20,
  sort_by: 'created_at',
  order: 'desc'
}

export const useProductStore = defineStore('product', () => {
  const products = ref<Product[]>([])
  const currentProduct = ref<Product | null>(null)
  const categories = ref<Category[]>([])
  const loading = ref(false)
  const searchParams = ref<ProductSearchParams>({ ...DEFAULT_SEARCH_PARAMS })
  const totalPages = ref(0)
  const total = ref(0)

  const hasMore = computed(() => {
    return searchParams.value.page! < totalPages.value
  })

  function normalizeSearchParams(params?: ProductSearchParams): ProductSearchParams {
    const merged = {
      ...DEFAULT_SEARCH_PARAMS,
      ...searchParams.value,
      ...(params || {})
    }

    return Object.fromEntries(
      Object.entries(merged).filter(([, value]) => value !== undefined && value !== null && value !== '')
    ) as ProductSearchParams
  }

  async function fetchProducts(params?: ProductSearchParams) {
    loading.value = true
    try {
      searchParams.value = normalizeSearchParams(params)
      
      const response = await apiClient.get<ProductListAPIResponse>('/products', {
        params: searchParams.value
      })

      const normalizedProducts = response.products ?? response.items ?? []
      const normalizedPage = response.page ?? searchParams.value.page ?? 1
      const normalizedPageSize = response.page_size ?? searchParams.value.page_size ?? 20
      const normalizedTotal = response.total ?? normalizedProducts.length
      const normalizedTotalPages =
        response.total_pages ?? Math.max(1, Math.ceil(normalizedTotal / normalizedPageSize))

      const normalizedResponse: ProductListResponse = {
        products: normalizedProducts,
        items: normalizedProducts,
        total: normalizedTotal,
        page: normalizedPage,
        page_size: normalizedPageSize,
        total_pages: normalizedTotalPages
      }

      products.value = normalizedResponse.products
      total.value = normalizedResponse.total
      totalPages.value = normalizedResponse.total_pages

      return normalizedResponse
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
      const response = await apiClient.get<CategoryAPIResponse>('/products/categories')
      categories.value = Array.isArray(response) ? response : response.categories ?? []
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
    searchParams.value = { ...DEFAULT_SEARCH_PARAMS }
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
