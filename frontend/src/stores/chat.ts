import { defineStore } from 'pinia'
import { ref, nextTick } from 'vue'
import { apiClient } from '@/api/client'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
  metadata?: any
  attachments?: any[]
}

interface Session {
  id: string
  title: string
  created_at: string
  message_count: number
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<Session[]>([])
  const currentSession = ref<Session | null>(null)
  const messages = ref<Message[]>([])
  const loading = ref(false)

  const buildSessionTitle = (seed?: string, attachments?: any[]) => {
    const trimmed = seed?.replace(/\s+/g, ' ').trim()
    if (trimmed) {
      return trimmed.length > 20 ? `${trimmed.slice(0, 20)}...` : trimmed
    }
    const firstAttachmentName = attachments?.[0]?.file_name as string | undefined
    if (firstAttachmentName) {
      const baseName = firstAttachmentName.replace(/\.[^/.]+$/, '')
      const normalized = baseName.replace(/\s+/g, ' ').trim()
      if (normalized) {
        return normalized.length > 20 ? `${normalized.slice(0, 20)}...` : normalized
      }
    }
    const timestamp = new Date().toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
    return `新对话 ${timestamp}`
  }

  async function fetchSessions() {
    try {
      sessions.value = await apiClient.get<Session[]>('/chat/sessions')
    } catch (error) {
      console.error('获取会话列表失败:', error)
    }
  }

  async function createSession(title?: string) {
    try {
      const finalTitle = buildSessionTitle(title)
      const session = await apiClient.post<Session>('/chat/session', { title: finalTitle })
      sessions.value.unshift(session)
      currentSession.value = session
      messages.value = []
      return session
    } catch (error) {
      console.error('创建会话失败:', error)
      return null
    }
  }

  async function selectSession(sessionId: string) {
    try {
      const session = sessions.value.find(s => s.id === sessionId)
      if (session) {
        currentSession.value = session
        await fetchMessages(sessionId)
      }
    } catch (error) {
      console.error('选择会话失败:', error)
    }
  }

  async function fetchMessages(sessionId: string) {
    try {
      messages.value = await apiClient.get<Message[]>(`/chat/session/${sessionId}/messages`)
    } catch (error) {
      console.error('获取消息失败:', error)
    }
  }

  async function sendMessage(content: string, attachments?: any[]) {
    console.log('========== sendMessage 开始 ==========')
    console.log('content:', content)
    console.log('attachments:', attachments)
    
    let sessionId = currentSession.value?.id
    console.log('currentSessionId:', sessionId)
    
    // 如果没有会话，先创建
    if (!sessionId) {
      console.log('没有会话，创建新会话...')
      const newSession = await createSession(buildSessionTitle(content, attachments))
      if (!newSession) return
      sessionId = newSession.id
      console.log('新会话创建成功:', sessionId)
    }

    loading.value = true
    console.log('loading 设置为 true')

    try {
      console.log('进入 try 块')
      // 添加用户消息到界面
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content,
        created_at: new Date().toISOString(),
        attachments
      }
      messages.value = [...messages.value, userMessage]
      console.log('用户消息已添加:', messages.value)

      // 发送消息到后端
      console.log('发送消息到后端:', { session_id: sessionId, message: content, attachments })
      const response = await apiClient.post<any>('/chat/message', {
        session_id: sessionId,
        message: content,
        attachments
      })
      console.log('收到后端响应:', response)

      // 添加AI回复到界面
      const assistantMessage: Message = {
        id: response.message_id,
        role: 'assistant',
        content: response.content,
        created_at: new Date().toISOString(),
        metadata: {
          intent: response.intent,
          sources: response.sources
        }
      }
      console.log('准备添加AI消息:', assistantMessage)
      messages.value = [...messages.value, assistantMessage]
      console.log('AI消息已添加, 当前消息数:', messages.value.length)
      
      // 更新会话列表（不切换当前会话）
      try {
        const updatedSessions = await apiClient.get<Session[]>('/chat/sessions')
        // 只更新会话列表，不改变当前会话和消息
        const currentSessionId = currentSession.value?.id
        sessions.value = updatedSessions
        // 更新当前会话的标题等信息
        if (currentSessionId) {
          const updatedCurrentSession = updatedSessions.find(s => s.id === currentSessionId)
          if (updatedCurrentSession) {
            // 只更新标题和消息数，保持其他状态
            currentSession.value = {
              ...currentSession.value,
              ...updatedCurrentSession
            }
          }
        }
      } catch (e) {
        console.error('更新会话列表失败:', e)
      }
    } catch (error) {
      console.error('发送消息失败:', error)
    } finally {
      loading.value = false
    }
  }

  async function sendMessageStream(content: string, attachments?: any[], onChunk?: (chunk: string) => void) {
    console.log('========== sendMessageStream 开始 ==========')
    
    let sessionId = currentSession.value?.id
    
    // 如果没有会话，先创建
    if (!sessionId) {
      const newSession = await createSession(buildSessionTitle(content, attachments))
      if (!newSession) return
      sessionId = newSession.id
    }

    loading.value = true

    try {
      // 添加用户消息到界面
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content,
        created_at: new Date().toISOString(),
        attachments
      }
      messages.value = [...messages.value, userMessage]

      // 创建AI消息（空内容）
      const assistantMessageId = Date.now().toString() + '_assistant'
      const assistantMessage: Message = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString(),
        metadata: {}
      }
      messages.value = [...messages.value, assistantMessage]

      // 使用 EventSource 接收流式数据
      const token = localStorage.getItem('access_token')
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: content,
          attachments
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
                console.log('收到流式数据:', data)

                if (data.type === 'intent') {
                  // 更新意图
                  const msgIndex = messages.value.findIndex(m => m.id === assistantMessageId)
                  if (msgIndex !== -1) {
                    messages.value[msgIndex].metadata = { ...messages.value[msgIndex].metadata, intent: data.intent }
                  }
                } else if (data.type === 'thinking') {
                  // 更新思考过程
                  const msgIndex = messages.value.findIndex(m => m.id === assistantMessageId)
                  if (msgIndex !== -1) {
                    messages.value[msgIndex].metadata = { ...messages.value[msgIndex].metadata, thinking: data.content }
                  }
                } else if (data.type === 'content') {
                  // 追加内容
                  fullContent += data.delta
                  const msgIndex = messages.value.findIndex(m => m.id === assistantMessageId)
                  if (msgIndex !== -1) {
                    messages.value[msgIndex].content = fullContent
                  }
                  if (onChunk) {
                    onChunk(data.delta)
                  }
                } else if (data.type === 'end') {
                  // 结束
                  const msgIndex = messages.value.findIndex(m => m.id === assistantMessageId)
                  if (msgIndex !== -1) {
                    messages.value[msgIndex].metadata = { 
                      ...messages.value[msgIndex].metadata, 
                      sources: data.sources 
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
      await fetchSessions()
      // 更新当前会话标题
      if (currentSession.value) {
        const updatedSession = sessions.value.find(s => s.id === currentSession.value?.id)
        if (updatedSession) {
          currentSession.value = { ...currentSession.value, ...updatedSession }
        }
      }
    } catch (error) {
      console.error('流式发送消息失败:', error)
    } finally {
      loading.value = false
    }
  }

  return {
    sessions,
    currentSession,
    messages,
    loading,
    fetchSessions,
    createSession,
    selectSession,
    fetchMessages,
    sendMessage,
    sendMessageStream
  }
})
