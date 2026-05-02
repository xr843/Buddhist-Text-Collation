/**
 * 对话相关类型定义
 */

export interface ChatMessage {
  id: number
  sessionId: number
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: MessageSource[] // 引用来源
  suggestedActions?: string[] // 建议的后续操作
}

export interface MessageSource {
  documentId: number
  documentName: string
  position: number // 字符位置
  excerpt: string // 引用片段
  confidence?: number
}

export interface ChatSession {
  id: number
  name: string
  createdAt: Date
  updatedAt: Date
  documentIds: number[] // 关联的文档
  messageCount: number
}

export interface SuggestedQuestion {
  id: string
  text: string
  category?: 'analysis' | 'comparison' | 'terminology' | 'background'
}
