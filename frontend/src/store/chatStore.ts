/**
 * 对话状态管理
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ChatMessage, ChatSession, SuggestedQuestion } from '../types/chat'

interface ChatState {
  // 状态
  sessions: ChatSession[]
  currentSessionId: number | null
  messages: ChatMessage[]
  suggestedQuestions: SuggestedQuestion[]
  isLoading: boolean
  nextSessionId: number
  nextMessageId: number

  // 会话操作
  createSession: (name?: string, documentIds?: number[]) => ChatSession
  switchSession: (sessionId: number) => void
  updateSession: (sessionId: number, updates: Partial<ChatSession>) => void
  deleteSession: (sessionId: number) => void
  getCurrentSession: () => ChatSession | undefined

  // 消息操作
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  getMessagesBySession: (sessionId: number) => ChatMessage[]
  clearMessages: (sessionId: number) => void

  // 建议问题
  setSuggestedQuestions: (questions: SuggestedQuestion[]) => void
  clearSuggestedQuestions: () => void

  // 加载状态
  setLoading: (loading: boolean) => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      // 初始状态
      sessions: [],
      currentSessionId: null,
      messages: [],
      suggestedQuestions: [],
      isLoading: false,
      nextSessionId: 1,
      nextMessageId: 1,

      // 会话操作
      createSession: (name, documentIds = []) => {
        const now = new Date()
        const newSession: ChatSession = {
          id: get().nextSessionId,
          name: name || `对话 ${get().nextSessionId}`,
          createdAt: now,
          updatedAt: now,
          documentIds,
          messageCount: 0,
        }
        set((state) => ({
          sessions: [...state.sessions, newSession],
          currentSessionId: newSession.id,
          nextSessionId: state.nextSessionId + 1,
        }))
        return newSession
      },

      switchSession: (sessionId) => {
        set({ currentSessionId: sessionId })
      },

      updateSession: (sessionId, updates) => {
        set((state) => ({
          sessions: state.sessions.map((session) =>
            session.id === sessionId
              ? { ...session, ...updates, updatedAt: new Date() }
              : session
          ),
        }))
      },

      deleteSession: (sessionId) => {
        set((state) => ({
          sessions: state.sessions.filter((s) => s.id !== sessionId),
          messages: state.messages.filter((m) => m.sessionId !== sessionId),
          currentSessionId:
            state.currentSessionId === sessionId
              ? state.sessions[0]?.id || null
              : state.currentSessionId,
        }))
      },

      getCurrentSession: () => {
        const { sessions, currentSessionId } = get()
        return sessions.find((s) => s.id === currentSessionId)
      },

      // 消息操作
      addMessage: (message) => {
        const newMessage: ChatMessage = {
          ...message,
          id: get().nextMessageId,
          timestamp: new Date(),
        }
        set((state) => ({
          messages: [...state.messages, newMessage],
          nextMessageId: state.nextMessageId + 1,
        }))

        // 更新会话的消息计数
        if (message.sessionId) {
          get().updateSession(message.sessionId, {
            messageCount: get().getMessagesBySession(message.sessionId).length + 1,
          })
        }
      },

      getMessagesBySession: (sessionId) => {
        return get().messages.filter((m) => m.sessionId === sessionId)
      },

      clearMessages: (sessionId) => {
        set((state) => ({
          messages: state.messages.filter((m) => m.sessionId !== sessionId),
        }))
        get().updateSession(sessionId, { messageCount: 0 })
      },

      // 建议问题
      setSuggestedQuestions: (questions) => {
        set({ suggestedQuestions: questions })
      },

      clearSuggestedQuestions: () => {
        set({ suggestedQuestions: [] })
      },

      // 加载状态
      setLoading: (loading) => {
        set({ isLoading: loading })
      },
    }),
    {
      name: 'buddhist-chat',
      partialize: (state) => ({
        sessions: state.sessions,
        currentSessionId: state.currentSessionId,
        messages: state.messages,
        nextSessionId: state.nextSessionId,
        nextMessageId: state.nextMessageId,
      }),
    }
  )
)
