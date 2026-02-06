<template>
  <div class="chat-container">
    <!-- 侧边栏 - 会话列表 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <el-button type="primary" @click="createNewSession" style="width: 100%">
          <el-icon><Plus /></el-icon>
          新建对话
        </el-button>
      </div>

      <div class="session-list">
        <div
          v-for="session in chatStore.sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: chatStore.currentSession?.id === session.id }"
          @click="selectSession(session.id)"
        >
          <div class="session-title">{{ session.title }}</div>
          <div class="session-info">{{ session.message_count }} 条消息</div>
        </div>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="chat-main">
      <div class="chat-header">
        <h3>{{ chatStore.currentSession?.title || '请选择或创建对话' }}</h3>
      </div>

      <div class="message-list" ref="messageListRef">
        <div
          v-for="message in messageList"
          :key="message.id"
          class="message-item"
          :class="message.role"
        >
          <!-- 用户消息 -->
          <template v-if="message.role === 'user'">
            <div class="message-avatar user-avatar">
              <el-icon><User /></el-icon>
            </div>
            <div class="message-content user-content">
              <div class="message-text">{{ message.content }}</div>
              <!-- 附件列表 -->
              <div v-if="message.attachments && message.attachments.length > 0" class="message-attachments">
                <div
                  v-for="(attachment, index) in message.attachments"
                  :key="index"
                  class="attachment-item"
                >
                  <el-icon><Document /></el-icon>
                  <span class="attachment-name">{{ attachment.file_name }}</span>
                  <span class="attachment-size">({{ formatFileSize(attachment.file_size) }})</span>
                </div>
              </div>
              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </template>

          <!-- AI消息 -->
          <template v-else>
            <div class="message-avatar ai-avatar">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <div class="message-content ai-content">
              <!-- 思考过程折叠面板 -->
              <div v-if="message.metadata?.thinking" class="thinking-panel">
                <div class="thinking-header" @click="toggleThinking(message.id)">
                  <el-icon class="thinking-icon"><ArrowRight v-if="!expandedThinking[message.id]" /><ArrowDown v-else /></el-icon>
                  <span class="thinking-title">已思考</span>
                  <span class="thinking-time">用时 {{ calculateThinkingTime(message) }} 秒</span>
                </div>
                <div v-show="expandedThinking[message.id]" class="thinking-content">
                  <pre>{{ message.metadata.thinking }}</pre>
                </div>
              </div>

              <!-- 正在思考状态 -->
              <div v-else-if="chatStore.loading && !message.content" class="thinking-panel">
                <div class="thinking-header">
                  <el-icon class="thinking-icon loading"><Loading /></el-icon>
                  <span class="thinking-title">正在思考</span>
                </div>
              </div>

              <!-- 消息内容 -->
              <div class="message-text" v-if="message.content">
                <MarkdownRenderer :content="message.content" />
              </div>

              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </template>
        </div>
      </div>

      <!-- 已选择的文件预览 -->
      <div v-if="selectedFiles.length > 0" class="selected-files">
        <div class="selected-files-header">
          <span>已选择 {{ selectedFiles.length }} 个文件</span>
          <el-button type="danger" link @click="clearFiles">
            <el-icon><Delete /></el-icon>
            清除
          </el-button>
        </div>
        <div class="file-list">
          <el-tag
            v-for="(file, index) in selectedFiles"
            :key="index"
            closable
            @close="removeFile(index)"
            class="file-tag"
          >
            <el-icon><Document /></el-icon>
            {{ file.name }}
          </el-tag>
        </div>
      </div>

      <div
        class="input-area"
        :class="{ 'drag-over': isDragOver }"
        @dragenter.prevent="handleDragEnter"
        @dragleave.prevent="handleDragLeave"
        @dragover.prevent
        @drop.prevent="handleDrop"
      >
        <!-- 拖拽提示 -->
        <div v-if="isDragOver" class="drag-overlay">
          <el-icon :size="48"><Upload /></el-icon>
          <span>释放文件以上传</span>
        </div>

        <!-- 上传按钮 -->
        <el-upload
          ref="uploadRef"
          action="#"
          :auto-upload="false"
          :on-change="handleFileChange"
          :show-file-list="false"
          :multiple="true"
          accept=".pdf,.doc,.docx,.txt,.md,.png,.jpg,.jpeg"
          class="upload-btn"
        >
          <el-button type="info" circle>
            <el-icon><Paperclip /></el-icon>
          </el-button>
        </el-upload>

        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="输入消息... 或直接拖拽文件到此处"
          @keydown.enter.exact.prevent="handleEnterKey"
        />
        <el-button
          type="primary"
          @click="sendMessage"
          :loading="chatStore.loading || uploading"
          :disabled="chatStore.loading || uploading"
        >
          {{ uploading ? '上传中...' : '发送' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import { Plus, User, ChatDotRound, Document, Paperclip, Delete, Upload, ArrowRight, ArrowDown, Loading } from '@element-plus/icons-vue'
import { apiClient } from '@/api/client'
import { ElMessage } from 'element-plus'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

const chatStore = useChatStore()
const messageList = computed(() => chatStore.messages)
const inputMessage = ref('')
const thinkingStatus = ref('正在分析文档内容...')
const messageListRef = ref<HTMLElement>()
const selectedFiles = ref<File[]>([])
const uploading = ref(false)
const isDragOver = ref(false)
const expandedThinking = ref<Record<string, boolean>>({})

onMounted(async () => {
  await chatStore.fetchSessions()
  if (chatStore.sessions.length > 0) {
    await chatStore.selectSession(chatStore.sessions[0].id)
  }
})

watch(() => messageList.value.length, () => {
  console.log('消息列表变化:', messageList.value.length)
  nextTick(() => {
    scrollToBottom()
  })
})

const createNewSession = async () => {
  await chatStore.createSession()
}

const selectSession = async (sessionId: string) => {
  await chatStore.selectSession(sessionId)
}

// 处理文件选择
const handleFileChange = (file: any) => {
  const rawFile = file.raw

  // 检查文件大小 (10MB)
  if (rawFile.size > 10 * 1024 * 1024) {
    ElMessage.warning(`文件 ${rawFile.name} 超过10MB限制`)
    return
  }

  // 检查是否已存在
  const exists = selectedFiles.value.some(f => f.name === rawFile.name && f.size === rawFile.size)
  if (!exists) {
    selectedFiles.value.push(rawFile)
  }
}

// 移除文件
const removeFile = (index: number) => {
  selectedFiles.value.splice(index, 1)
}

// 清除所有文件
const clearFiles = () => {
  selectedFiles.value = []
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 拖拽处理
const handleDragEnter = () => {
  isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (event: DragEvent) => {
  isDragOver.value = false

  const files = event.dataTransfer?.files
  if (files) {
    for (let i = 0; i < files.length; i++) {
      const file = files[i]

      // 检查文件大小 (10MB)
      if (file.size > 10 * 1024 * 1024) {
        ElMessage.warning(`文件 ${file.name} 超过10MB限制`)
        continue
      }

      // 检查是否已存在
      const exists = selectedFiles.value.some(f => f.name === file.name && f.size === file.size)
      if (!exists) {
        selectedFiles.value.push(file)
      }
    }
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() && selectedFiles.value.length === 0) {
    return
  }

  // 防止重复提交
  if (uploading.value || chatStore.loading) {
    return
  }

  uploading.value = true

  // 设置思考状态
  if (selectedFiles.value.length > 0) {
    thinkingStatus.value = '正在读取文件内容...'
  } else {
    thinkingStatus.value = '正在思考问题...'
  }

  try {
    let attachments: any[] = []

    if (!chatStore.currentSession?.id) {
      const titleSeed = inputMessage.value.trim() || selectedFiles.value[0]?.name || ''
      await chatStore.createSession(titleSeed)
    }

    // 如果有文件，先上传
    if (selectedFiles.value.length > 0) {
      const uploadTasks = selectedFiles.value.map(file => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('session_id', chatStore.currentSession?.id || '')

        return apiClient.post('/files/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
      })

      const responses = await Promise.all(uploadTasks)
      attachments = responses.map(response => ({
        file_id: response.file_id,
        file_name: response.file_name,
        file_type: response.file_type,
        file_size: response.file_size,
        file_path: response.file_path
      }))
    }

    // 保存消息内容并清空输入框（立即执行，不等待流式输出完成）
    const messageContent = inputMessage.value
    inputMessage.value = ''
    
    // 文件上传成功后，立即清空已选择的文件列表
    // 这样用户界面就不会继续显示"已选择 x 个文件"
    selectedFiles.value = []
    uploading.value = false

    // 发送消息（使用流式输出）
    await chatStore.sendMessageStream(messageContent, attachments, (chunk) => {
      console.log('收到内容片段:', chunk)
    })
  } catch (error) {
    console.error('发送失败:', error)
    ElMessage.error('发送失败，请重试')
    uploading.value = false
  }
}

const handleEnterKey = () => {
  // 在 loading 状态下不响应 Enter 键
  if (chatStore.loading || uploading.value) {
    return
  }
  sendMessage()
}

const toggleThinking = (messageId: string) => {
  expandedThinking.value[messageId] = !expandedThinking.value[messageId]
}

const calculateThinkingTime = (message: any) => {
  // 简化计算，返回固定值或基于消息创建时间计算
  return 3
}

const scrollToBottom = () => {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background: var(--bg);
  padding: 20px;
  gap: 20px;
}

.sidebar {
  width: 300px;
  background: var(--surface);
  border-radius: 16px;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border);
}

.sidebar-header {
  padding: 24px;
  background: var(--surface-2);
  border-bottom: 1px solid var(--border);
}

.sidebar-header :deep(.el-button) {
  background: rgba(56, 189, 248, 0.2);
  border: 1px solid rgba(56, 189, 248, 0.4);
  color: var(--text);
  font-weight: 600;
  transition: all 0.3s ease;
}

.sidebar-header :deep(.el-button:hover) {
  background: rgba(56, 189, 248, 0.32);
  border-color: rgba(56, 189, 248, 0.6);
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(2, 6, 23, 0.4);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.session-item {
  padding: 16px 20px;
  margin-bottom: 8px;
  cursor: pointer;
  border-radius: 12px;
  transition: all 0.3s ease;
  background: var(--surface-3);
  border: 1px solid transparent;
  color: var(--muted);
}

.session-item:hover {
  background: rgba(148, 163, 184, 0.12);
  border-color: var(--border);
  transform: translateX(4px);
  box-shadow: 0 8px 20px rgba(2, 6, 23, 0.35);
  color: var(--text);
}

.session-item.active {
  background: rgba(56, 189, 248, 0.2);
  color: var(--text);
  box-shadow: 0 10px 24px rgba(2, 6, 23, 0.4);
  border-color: rgba(56, 189, 248, 0.4);
}

.session-item.active .session-info {
  color: var(--text);
}

.session-title {
  font-weight: 600;
  margin-bottom: 6px;
  font-size: 15px;
}

.session-info {
  font-size: 12px;
  color: var(--muted);
  transition: color 0.3s ease;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-radius: 16px;
  box-shadow: var(--shadow);
  overflow: hidden;
  border: 1px solid var(--border);
}

.chat-header {
  padding: 24px 32px;
  background: var(--surface-2);
  color: var(--text);
  border-bottom: 1px solid var(--border);
}

.chat-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 28px;
  background: var(--surface-3);
}

.message-item {
  display: flex;
  margin-bottom: 24px;
  animation: fadeInUp 0.35s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--surface-2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 16px;
  color: var(--text);
  font-size: 20px;
  box-shadow: 0 8px 20px rgba(2, 6, 23, 0.35);
  transition: transform 0.3s ease;
  border: 1px solid var(--border);
}

.message-avatar:hover {
  transform: scale(1.1);
}

.message-item.user .message-avatar {
  background: rgba(56, 189, 248, 0.25);
  box-shadow: 0 8px 20px rgba(2, 6, 23, 0.4);
  border: 1px solid rgba(56, 189, 248, 0.4);
}

.message-content {
  max-width: 70%;
  background: var(--surface-2);
  padding: 20px 24px;
  border-radius: 16px;
  box-shadow: 0 10px 24px rgba(2, 6, 23, 0.35);
  border: 1px solid var(--border);
  transition: all 0.3s ease;
}

.message-content:hover {
  box-shadow: 0 14px 32px rgba(2, 6, 23, 0.45);
}

.message-item.user .message-content {
  background: rgba(56, 189, 248, 0.22);
  color: var(--text);
  border: 1px solid rgba(56, 189, 248, 0.4);
  box-shadow: 0 10px 24px rgba(2, 6, 23, 0.45);
}

.message-item.user .message-content:hover {
  box-shadow: 0 14px 32px rgba(2, 6, 23, 0.55);
}

.message-text {
  line-height: 1.6;
  font-size: 15px;
}

.message-item.user .message-text {
  white-space: pre-wrap;
}

.message-item.assistant .message-text,
.message-item.system .message-text {
  white-space: normal;
  color: var(--text);
}

.message-attachments {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed rgba(148, 163, 184, 0.3);
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text);
  margin-top: 6px;
  padding: 6px 10px;
  background: rgba(148, 163, 184, 0.12);
  border-radius: 8px;
}

.message-item.user .message-attachments {
  border-top: 1px dashed rgba(56, 189, 248, 0.45);
}

.message-item.user .attachment-item {
  background: rgba(2, 6, 23, 0.35);
  border: 1px solid rgba(56, 189, 248, 0.35);
}

.message-time {
  font-size: 11px;
  color: var(--muted);
  margin-top: 8px;
  font-weight: 500;
}

.message-item.user .message-time {
  color: var(--text);
}

.selected-files {
  padding: 16px 24px;
  border-top: 1px solid var(--border);
  background: var(--surface-2);
}

.selected-files-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  color: var(--text);
  font-weight: 500;
}

.file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.file-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--surface-3);
  border-radius: 999px;
  box-shadow: 0 6px 16px rgba(2, 6, 23, 0.35);
  transition: all 0.3s ease;
  border: 1px solid var(--border);
  color: var(--text);
}

.file-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(2, 6, 23, 0.45);
}

.input-area {
  display: flex;
  gap: 16px;
  padding: 24px 32px;
  background: var(--surface);
  align-items: flex-start;
  position: relative;
  border-top: 1px solid var(--border);
}

.input-area.drag-over {
  background: rgba(56, 189, 248, 0.1);
  border: 2px dashed rgba(56, 189, 248, 0.6);
}

.drag-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(56, 189, 248, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
  pointer-events: none;
  backdrop-filter: blur(2px);
}

.drag-overlay .el-icon {
  color: var(--accent);
  margin-bottom: 12px;
  font-size: 48px;
}

.drag-overlay span {
  color: var(--text);
  font-size: 18px;
  font-weight: 600;
}

.upload-btn {
  flex-shrink: 0;
}

.upload-btn :deep(.el-button) {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--text);
  font-size: 20px;
  transition: all 0.3s ease;
  box-shadow: 0 8px 20px rgba(2, 6, 23, 0.4);
}

.upload-btn :deep(.el-button:hover) {
  transform: scale(1.05);
  box-shadow: 0 12px 26px rgba(2, 6, 23, 0.55);
}

.input-area :deep(.el-textarea__inner) {
  border-radius: 14px;
  padding: 16px 20px;
  font-size: 15px;
  border: 1px solid var(--border);
  transition: all 0.3s ease;
  background: var(--surface-3);
  color: var(--text);
}

.input-area :deep(.el-textarea__inner:focus) {
  border-color: rgba(56, 189, 248, 0.7);
  background: var(--surface-2);
  box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.18);
}

.input-area :deep(.el-button--primary) {
  height: 48px;
  padding: 0 32px;
  border-radius: 24px;
  background: rgba(56, 189, 248, 0.25);
  border: 1px solid rgba(56, 189, 248, 0.5);
  font-weight: 600;
  font-size: 15px;
  transition: all 0.3s ease;
  box-shadow: 0 10px 24px rgba(2, 6, 23, 0.45);
  color: var(--text);
}

.input-area :deep(.el-button--primary:hover) {
  transform: translateY(-2px);
  box-shadow: 0 14px 30px rgba(2, 6, 23, 0.55);
}

.input-area :deep(.el-button--primary:active) {
  transform: translateY(0);
}

/* 思考面板样式 */
.thinking-panel {
  background: var(--surface-2);
  border-radius: 12px;
  margin-bottom: 16px;
  overflow: hidden;
  border: 1px solid var(--border);
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--surface-3);
}

.thinking-header:hover {
  background: rgba(148, 163, 184, 0.12);
}

.thinking-icon {
  font-size: 16px;
  color: var(--accent);
  transition: transform 0.3s ease;
}

.thinking-icon.loading {
  animation: spin 1s linear infinite;
  color: var(--accent);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.thinking-title {
  font-size: 14px;
  color: var(--text);
  font-weight: 600;
}

.thinking-time {
  font-size: 12px;
  color: var(--muted);
  margin-left: auto;
  background: rgba(56, 189, 248, 0.16);
  padding: 4px 10px;
  border-radius: 12px;
}

.thinking-content {
  padding: 16px;
  border-top: 1px solid var(--border);
  background: var(--surface-3);
}

.thinking-content pre {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--muted);
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

/* 思考动画 */
.thinking-dots {
  display: inline-flex;
  margin-left: 4px;
}

.thinking-dots .dot {
  animation: thinking-bounce 1.4s infinite ease-in-out both;
  color: var(--accent);
}

.thinking-dots .dot:nth-child(1) {
  animation-delay: -0.32s;
}

.thinking-dots .dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes thinking-bounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.thinking-status {
  font-size: 12px;
  color: var(--muted);
  margin-top: 8px;
  font-style: italic;
}
</style>
