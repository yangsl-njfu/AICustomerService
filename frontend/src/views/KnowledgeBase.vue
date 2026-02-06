<template>
  <div class="knowledge-base">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>知识库管理</h2>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon>
            上传文档
          </el-button>
        </div>
      </template>

      <!-- 文档列表 -->
      <el-table :data="documents" v-loading="loading" style="width: 100%">
        <el-table-column prop="title" label="文档标题" min-width="200">
          <template #default="{ row }">
            <div class="doc-title">
              <el-icon class="doc-icon">
                <Document v-if="row.file_type === 'pdf'" />
                <DocumentCopy v-else-if="['doc', 'docx'].includes(row.file_type)" />
                <DocumentChecked v-else />
              </el-icon>
              <span>{{ row.title || row.file_name }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="file_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.file_type.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="file_size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>

        <el-table-column prop="chunk_count" label="分块数" width="100">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.chunk_count }} 块</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'warning'" size="small">
              {{ row.status === 'active' ? '可用' : '处理中' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <el-empty v-if="!loading && documents.length === 0" description="暂无知识库文档">
        <el-button type="primary" @click="showUploadDialog = true">上传第一个文档</el-button>
      </el-empty>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传知识库文档"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="文档文件" required>
          <el-upload
            ref="uploadRef"
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :limit="1"
            accept=".pdf,.doc,.docx,.txt,.md"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF、Word、TXT、Markdown 格式，文件大小不超过 10MB
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="文档标题">
          <el-input
            v-model="uploadForm.title"
            placeholder="请输入文档标题（可选，默认为文件名）"
          />
        </el-form-item>

        <el-form-item label="文档描述">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入文档描述（可选）"
          />
        </el-form-item>
      </el-form>

      <!-- 上传进度 -->
      <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
        <el-progress :percentage="uploadProgress" :status="uploadStatus" />
      </div>

      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleUpload"
          :loading="uploading"
          :disabled="!selectedFile"
        >
          {{ uploading ? '上传中...' : '开始上传' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Document, DocumentCopy, DocumentChecked, Delete } from '@element-plus/icons-vue'
import { knowledgeApi, type KnowledgeDocument } from '@/api/knowledge'

const loading = ref(false)
const documents = ref<KnowledgeDocument[]>([])
const showUploadDialog = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const selectedFile = ref<File | null>(null)

const uploadForm = ref({
  title: '',
  description: ''
})

// 获取文档列表
const fetchDocuments = async () => {
  loading.value = true
  try {
    documents.value = await knowledgeApi.getDocuments()
  } catch (error) {
    console.error('获取文档列表失败:', error)
    ElMessage.error('获取文档列表失败')
  } finally {
    loading.value = false
  }
}

// 文件选择变化
const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
  // 如果没有填写标题，自动使用文件名
  if (!uploadForm.value.title && file.name) {
    uploadForm.value.title = file.name.replace(/\.[^/.]+$/, '')
  }
}

// 文件移除
const handleFileRemove = () => {
  selectedFile.value = null
  uploadForm.value.title = ''
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 上传文档
const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = ''

  try {
    await knowledgeApi.uploadDocument(
      {
        file: selectedFile.value,
        title: uploadForm.value.title,
        description: uploadForm.value.description
      },
      (progress) => {
        uploadProgress.value = progress
      }
    )

    uploadStatus.value = 'success'
    ElMessage.success('文档上传成功')
    showUploadDialog.value = false

    // 重置表单
    uploadForm.value = { title: '', description: '' }
    selectedFile.value = null

    // 刷新列表
    fetchDocuments()
  } catch (error: any) {
    uploadStatus.value = 'exception'
    console.error('上传失败:', error)
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

// 删除文档
const handleDelete = async (doc: KnowledgeDocument) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${doc.title || doc.file_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await knowledgeApi.deleteDocument(doc.id)
    ElMessage.success('删除成功')
    fetchDocuments()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchDocuments()
})
</script>

<style scoped>
.knowledge-base {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
}

.doc-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-icon {
  font-size: 20px;
  color: #409eff;
}

.upload-progress {
  margin-top: 20px;
  padding: 0 20px;
}

:deep(.el-upload__tip) {
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
}
</style>
