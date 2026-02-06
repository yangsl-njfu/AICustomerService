import { apiClient } from './client'
import type { Product, Category, ProductSearchParams, ProductListResponse } from '@/stores/product'

export const productApi = {
  // 获取商品列表
  async getProducts(params?: ProductSearchParams): Promise<ProductListResponse> {
    return apiClient.get<ProductListResponse>('/products', { params })
  },

  // 获取商品详情
  async getProduct(id: string): Promise<Product> {
    return apiClient.get<Product>(`/products/${id}`)
  },

  // 创建商品
  async createProduct(data: any): Promise<Product> {
    return apiClient.post<Product>('/products', data)
  },

  // 更新商品
  async updateProduct(id: string, data: any): Promise<Product> {
    return apiClient.put<Product>(`/products/${id}`, data)
  },

  // 删除商品
  async deleteProduct(id: string): Promise<void> {
    return apiClient.delete<void>(`/products/${id}`)
  },

  // 获取分类列表
  async getCategories(): Promise<Category[]> {
    return apiClient.get<Category[]>('/products/categories')
  },

  // 上传商品图片
  async uploadImage(file: File, onProgress?: (progress: number) => void): Promise<{ url: string }> {
    return apiClient.upload<{ url: string }>('/files/upload', file, onProgress)
  }
}
