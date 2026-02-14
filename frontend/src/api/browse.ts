import { apiClient } from './client'

const api = apiClient

export const browseAPI = {
  recordBrowse(productId: string, viewDuration: number = 0) {
    return api.client.post('/browse', {
      product_id: productId,
      view_duration: viewDuration
    })
  },

  getBrowseHistory(page: number = 1, pageSize: number = 20) {
    return api.client.get('/browse', {
      params: { page, page_size: pageSize }
    })
  },

  getUserInterests() {
    return api.client.get('/browse/interests')
  },

  deleteBrowseRecord(productId: string) {
    return api.client.delete(`/browse/${productId}`)
  },

  clearBrowseHistory() {
    return api.client.delete('/browse')
  },

  getRecommendations(limit: number = 10, excludeIds?: string[]) {
    return api.client.get('/browse/recommendations', {
      params: {
        limit,
        exclude_ids: excludeIds?.join(',')
      }
    })
  },

  getSimilarProducts(productId: string, limit: number = 5) {
    return api.client.get(`/browse/recommendations/similar/${productId}`, {
      params: { limit }
    })
  }
}
