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
          <div class="session-content">
            <div class="session-title">{{ session.title }}</div>
            <div class="session-info">{{ session.message_count }} 条消息</div>
          </div>
          <el-button
            class="session-delete-btn"
            type="danger"
            link
            @click.stop="deleteSession(session.id)"
          >
            <el-icon><Close /></el-icon>
          </el-button>
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
              
              <!-- 订单卡片 -->
              <div v-if="message.metadata?.order_card" class="user-order-card">
                <div class="order-card-header">
                  <span class="order-no">{{ message.metadata.order_card.order_no }}</span>
                  <span class="order-status">{{ message.metadata.order_card.status }}</span>
                </div>
                <div class="order-card-body">
                  <div class="product-name">{{ message.metadata.order_card.product_name }}</div>
                  <div class="order-amount">¥{{ message.metadata.order_card.total_amount }}</div>
                </div>
              </div>
              
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
                  <span class="thinking-title">思考过程</span>
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

              <!-- 快速操作按钮 -->
              <div v-if="message.metadata?.quick_actions && message.metadata.quick_actions.length > 0" class="quick-actions">
                <div
                  v-for="(action, index) in message.metadata.quick_actions"
                  :key="index"
                  class="quick-action-item"
                  :class="action.type"
                  @click="handleQuickAction(action)"
                >
                  <!-- 简洁订单卡片样式 -->
                  <template v-if="action.type === 'order_card_simple'">
                    <div class="order-card-simple-content">
                      <div class="order-card-simple-header">
                        <span class="order-no-simple">订单号：{{ action.data.order_no }}</span>
                        <span class="order-status-simple" :class="'status-' + action.data.status">{{ action.data.status_text }}</span>
                      </div>
                      <div class="order-card-simple-body">
                        <span class="product-name-simple">{{ action.data.product_name }}</span>
                      </div>
                      <div class="order-card-simple-footer">
                        <span class="order-amount-simple">¥{{ action.data.total_amount.toFixed(2) }}</span>
                        <span class="order-time-simple">{{ formatOrderTime(action.data.created_at) }}</span>
                      </div>
                    </div>
                    <el-icon class="action-arrow"><ArrowRight /></el-icon>
                  </template>
                  
                  <!-- 订单卡片样式 -->
                  <template v-else-if="action.type === 'order_card'">
                    <div class="order-card-content">
                      <div class="order-card-header">
                        <span class="order-no">订单号: {{ action.data.order_no }}</span>
                        <span class="order-status" :class="'status-' + action.data.status">{{ action.data.status_text }}</span>
                      </div>
                      <div class="order-card-body">
                        <div class="product-info">
                          <span class="product-name">{{ action.data.product_name }}</span>
                          <span v-if="action.data.item_count > 1" class="item-count">等{{ action.data.item_count }}件商品</span>
                        </div>
                        <div class="order-meta">
                          <span class="order-amount">¥{{ action.data.total_amount.toFixed(2) }}</span>
                          <span class="order-time">{{ formatOrderTime(action.data.created_at) }}</span>
                        </div>
                      </div>
                    </div>
                    <el-icon class="action-arrow"><ArrowRight /></el-icon>
                  </template>
                  
                  <!-- 普通按钮样式 -->
                  <template v-else>
                    <span v-if="action.icon" class="action-icon">{{ action.icon }}</span>
                    <span class="action-label">{{ action.label }}</span>
                    <el-icon class="action-arrow"><ArrowRight /></el-icon>
                  </template>
                </div>
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

        <!-- 选择订单按钮 -->
        <el-button type="info" circle @click="showOrderSelector" class="order-btn">
          <el-icon><ShoppingBag /></el-icon>
        </el-button>

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

    <!-- 订单选择弹窗 -->
    <OrderSelector v-model="orderSelectorVisible" @select="handleOrderSelect" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { Plus, User, ChatDotRound, Document, Paperclip, Delete, Upload, ArrowRight, ArrowDown, Loading, ShoppingBag, Close } from '@element-plus/icons-vue'
import { apiClient } from '@/api/client'
import { ElMessage } from 'element-plus'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import OrderSelector from '@/components/OrderSelector.vue'

const router = useRouter()
const chatStore = useChatStore()
const messageList = computed(() => chatStore.messages)
const inputMessage = ref('')
const thinkingStatus = ref('正在分析文档内容...')
const messageListRef = ref<HTMLElement>()
const selectedFiles = ref<File[]>([])
const uploading = ref(false)
const isDragOver = ref(false)
const expandedThinking = ref<Record<string, boolean>>({})
const orderSelectorVisible = ref(false)

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

const deleteSession = async (sessionId: string) => {
  const success = await chatStore.deleteSession(sessionId)
  if (success) {
    ElMessage.success('会话已删除')
  } else {
    ElMessage.error('删除失败')
  }
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
      attachments = responses.map((response: any) => ({
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

const scrollToBottom = () => {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

const formatTime = (time: string) => {
  if (!time) return ''
  const date = new Date(time)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

const formatOrderTime = (time: string) => {
  if (!time) return ''
  const date = new Date(time)
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}`
}

// 显示订单选择器
const showOrderSelector = () => {
  orderSelectorVisible.value = true
}

// 处理订单选择 - 将订单信息以卡片形式插入到消息中
const handleOrderSelect = async (order: any) => {
  // 显示订单卡片消息
  const orderCardMessage = {
    id: Date.now().toString(),
    role: 'user' as const,
    content: `我要咨询订单 ${order.order_no}`,
    created_at: new Date().toISOString(),
    metadata: {
      order_card: {
        order_no: order.order_no,
        status: getOrderStatusText(order.status),
        product_name: getOrderProductName(order),
        total_amount: (order.total_amount / 100).toFixed(2),
        item_count: order.items?.length || 1
      }
    }
  }
  
  // 添加到消息列表
  chatStore.messages.push(orderCardMessage)
  
  // 直接调用后端API，不通过 sendMessageStream（避免重复添加用户消息）
  const sessionId = chatStore.currentSession?.id
  if (!sessionId) return
  
  chatStore.loading = true
  
  try {
    // 创建AI消息（空内容）
    const assistantMessageId = Date.now().toString() + '_assistant'
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant' as const,
      content: '',
      created_at: new Date().toISOString(),
      metadata: {}
    }
    chatStore.messages.push(assistantMessage)

    // 使用流式API（直连后端，绕过 Vite 代理的 SSE 缓冲）
    const token = localStorage.getItem('access_token')
    const response = await fetch('http://localhost:8000/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        session_id: sessionId,
        message: `我要咨询订单 ${order.order_no}`,
        attachments: []
      })
    })

    if (!response.ok) {
      throw new Error('Stream request failed')
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    let fullContent = ''

    if (reader) {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.type === 'intent') {
                const msgIndex = chatStore.messages.findIndex(m => m.id === assistantMessageId)
                if (msgIndex !== -1) {
                  chatStore.messages[msgIndex].metadata = { ...chatStore.messages[msgIndex].metadata, intent: data.intent }
                }
              } else if (data.type === 'thinking') {
                const msgIndex = chatStore.messages.findIndex(m => m.id === assistantMessageId)
                if (msgIndex !== -1) {
                  chatStore.messages[msgIndex].metadata = { ...chatStore.messages[msgIndex].metadata, thinking: data.content }
                }
              } else if (data.type === 'content') {
                fullContent += data.delta
                const msgIndex = chatStore.messages.findIndex(m => m.id === assistantMessageId)
                if (msgIndex !== -1) {
                  chatStore.messages[msgIndex].content = fullContent
                }
              } else if (data.type === 'end') {
                const msgIndex = chatStore.messages.findIndex(m => m.id === assistantMessageId)
                if (msgIndex !== -1) {
                  chatStore.messages[msgIndex].metadata = { 
                    ...chatStore.messages[msgIndex].metadata, 
                    sources: data.sources,
                    quick_actions: data.quick_actions
                  }
                }
              }
            } catch (e) {
              console.error('解析流式数据失败:', e)
            }
          }
        }
      }
    }

    // 更新会话列表
    await chatStore.fetchSessions()
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送失败，请重试')
  } finally {
    chatStore.loading = false
  }
}

const getOrderStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待支付',
    paid: '已支付',
    shipped: '已发货',
    delivered: '已送达',
    completed: '已完成',
    cancelled: '已取消'
  }
  return statusMap[status] || '未知'
}

const getOrderProductName = (order: any) => {
  if (!order.items || !Array.isArray(order.items) || order.items.length === 0) {
    return '商品'
  }
  return order.items[0]?.product_title || '商品'
}

// 处理快速操作按钮点击
const handleQuickAction = (action: any) => {
  console.log('=== 快速操作 ===')
  console.log('action.type:', action.type)
  console.log('action.action:', action.action)
  console.log('完整action:', action)
  
  if (action.type === 'product') {
    // 商品卡片 - 跳转到商品详情
    if (action.data?.product_id) {
      window.open(`/products/${action.data.product_id}`, '_blank')
    }
  } else if (action.type === 'order_card_simple') {
    // 简洁订单卡片 - 直接发送订单信息
    console.log('点击了简洁订单卡片')
    const orderCardMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: `【发订单】`,
      created_at: new Date().toISOString(),
      metadata: {
        order_card: {
          order_no: action.data.order_no,
          status: action.data.status_text,
          product_name: action.data.product_name,
          total_amount: action.data.total_amount.toFixed(2),
          item_count: 1
        }
      }
    }
    
    // 添加到消息列表
    chatStore.messages.push(orderCardMessage)
    
    // 自动发送订单咨询
    inputMessage.value = `我要咨询订单 ${action.data.order_no}`
    sendMessage()
  } else if (action.type === 'order_card') {
    // 完整订单卡片 - 直接发送订单信息
    console.log('点击了完整订单卡片')
    const orderCardMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: `【发订单】`,
      created_at: new Date().toISOString(),
      metadata: {
        order_card: {
          order_no: action.data.order_no,
          status: action.data.status_text,
          product_name: action.data.product_name,
          total_amount: action.data.total_amount.toFixed(2),
          item_count: action.data.item_count || 1
        }
      }
    }
    
    // 添加到消息列表
    chatStore.messages.push(orderCardMessage)
    
    // 自动发送订单咨询
    inputMessage.value = `我要咨询订单 ${action.data.order_no}`
    sendMessage()
  } else if (action.type === 'button') {
    // 普通按钮 - 根据action类型处理
    console.log('点击了普通按钮, action.action:', action.action)
    if (action.action === 'send_question' && action.data?.question) {
      // 发送预设问题
      inputMessage.value = action.data.question
      sendMessage()
    } else if (action.action === 'select_order') {
      // 选择订单 - 发送订单信息
      const orderNo = action.data?.order_no || ''
      inputMessage.value = `我要咨询订单 ${orderNo}`
      sendMessage()
    } else if (action.action === 'open_order_selector') {
      // 打开订单选择弹窗
      console.log('打开订单选择弹窗')
      orderSelectorVisible.value = true
    } else if (action.action === 'navigate') {
      // 页面跳转
      const path = action.data?.path
      if (path) {
        router.push(path)
      }
    } else if (action.action === 'view_all_recommendations') {
      inputMessage.value = '查看全部推荐'
      sendMessage()
    } else if (action.action === 'refresh_recommendations') {
      inputMessage.value = '换一批推荐'
      sendMessage()
    } else if (action.data?.question) {
      // 兼容旧格式
      inputMessage.value = action.data.question
      sendMessage()
    }
  } else if (action.type === 'link') {
    // 链接 - 打开URL
    if (action.data?.url) {
      window.open(action.data.url, '_blank')
    }
  }
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
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.session-content {
  flex: 1;
  min-width: 0;
}

.session-delete-btn {
  opacity: 0;
  transition: opacity 0.2s ease;
  flex-shrink: 0;
  margin-left: 8px;
}

.session-item:hover .session-delete-btn {
  opacity: 1;
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

/* 用户发送的订单卡片样式 */
.user-order-card {
  margin-top: 12px;
  padding: 12px;
  background: rgba(2, 6, 23, 0.3);
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 10px;
}

.user-order-card .order-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px dashed rgba(56, 189, 248, 0.3);
}

.user-order-card .order-no {
  font-size: 12px;
  color: var(--text);
  font-family: monospace;
  opacity: 0.8;
}

.user-order-card .order-status {
  font-size: 12px;
  padding: 2px 8px;
  background: rgba(56, 189, 248, 0.2);
  border-radius: 8px;
  color: var(--text);
}

.user-order-card .order-card-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-order-card .product-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.user-order-card .order-amount {
  font-size: 14px;
  font-weight: 700;
  color: #ef4444;
}

/* 快速操作按钮样式 */
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.quick-action-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--surface-3);
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text);
  font-size: 14px;
}

.quick-action-item:hover {
  background: rgba(56, 189, 248, 0.15);
  border-color: rgba(56, 189, 248, 0.4);
  transform: translateX(4px);
  box-shadow: 0 6px 16px rgba(2, 6, 23, 0.35);
}

/* 订单卡片样式 */
.quick-action-item.order_card,
.quick-action-item.order_card_simple {
  padding: 16px;
  background: var(--surface-2);
  border: 1px solid var(--border);
}

.quick-action-item.order_card:hover,
.quick-action-item.order_card_simple:hover {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.5);
  box-shadow: 0 8px 20px rgba(2, 6, 23, 0.4);
}

/* 简洁订单卡片内容 */
.order-card-simple-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.order-card-simple-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

.order-no-simple {
  font-size: 12px;
  color: var(--muted);
  font-family: monospace;
}

.order-status-simple {
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
}

.order-status-simple.status-pending {
  background: rgba(251, 191, 36, 0.2);
  color: #f59e0b;
}

.order-status-simple.status-paid {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.order-status-simple.status-shipped {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.order-status-simple.status-delivered,
.order-status-simple.status-completed {
  background: rgba(168, 85, 247, 0.2);
  color: #a855f7;
}

.order-status-simple.status-cancelled {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.order-card-simple-body {
  padding: 4px 0;
}

.product-name-simple {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.order-card-simple-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-amount-simple {
  font-size: 16px;
  font-weight: 700;
  color: #ef4444;
}

.order-time-simple {
  font-size: 12px;
  color: var(--muted);
}

/* 原订单卡片样式 */
.order-card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.order-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-no {
  font-size: 13px;
  color: var(--muted);
  font-family: monospace;
}

.order-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.order-status.status-pending {
  background: rgba(251, 191, 36, 0.2);
  color: #f59e0b;
}

.order-status.status-paid {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.order-status.status-shipped {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.order-status.status-delivered,
.order-status.status-completed {
  background: rgba(168, 85, 247, 0.2);
  color: #a855f7;
}

.order-status.status-cancelled {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.order-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.product-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.product-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.item-count {
  font-size: 12px;
  color: var(--muted);
  padding: 2px 8px;
  background: rgba(148, 163, 184, 0.15);
  border-radius: 8px;
}

.order-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-amount {
  font-size: 16px;
  font-weight: 700;
  color: #ef4444;
}

.order-time {
  font-size: 12px;
  color: var(--muted);
}

/* 商品卡片样式 */
.quick-action-item.product {
  background: rgba(56, 189, 248, 0.1);
  border-color: rgba(56, 189, 248, 0.3);
}

.quick-action-item.product:hover {
  background: rgba(56, 189, 248, 0.2);
  border-color: rgba(56, 189, 248, 0.5);
}

.action-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.action-label {
  flex: 1;
  font-weight: 500;
}

.action-arrow {
  font-size: 16px;
  color: var(--muted);
  transition: transform 0.3s ease;
}

.quick-action-item:hover .action-arrow {
  transform: translateX(4px);
  color: var(--accent);
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

.order-btn {
  flex-shrink: 0;
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

.order-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 12px 26px rgba(2, 6, 23, 0.55);
  background: rgba(56, 189, 248, 0.15);
  border-color: rgba(56, 189, 248, 0.4);
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
