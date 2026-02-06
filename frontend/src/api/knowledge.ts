import { apiClient } from './client'

export interface KnowledgeDocument {
  id: string
  title: string
  description: string
  file_name: string
  file_type: string
  file_size: number
  chunk_count: number
  created_by: string
  status: string
}

export interface UploadKnowledgeRequest {
  file: File
  title?: string
  description?: string
}

export const knowledgeApi = {
  // 上传知识库文档
  uploadDocument: (data: UploadKnowledgeRequest, onProgress?: (progress: number) => void) => {
    const formData = new FormData()
    formData.append('file', data.file)
    if (data.title) formData.append('title', data.title)
    if (data.description) formData.append('description', data.description)

    return apiClient.post<KnowledgeDocument>('/knowledge/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })
  },

  // 获取文档列表
  getDocuments: () => {
    return apiClient.get<KnowledgeDocument[]>('/knowledge/documents')
  },

  // 删除文档
  deleteDocument: (docId: string) => {
    return apiClient.delete(`/knowledge/documents/${docId}`)
  }
}
