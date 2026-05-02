/**
 * 全局状态管理统一导出
 */
export { useDocumentStore } from './documentStore'
export { useChatStore } from './chatStore'
export { useWorkspaceStore } from './workspaceStore'
export { useSettingsStore } from './settingsStore'

// 重新导出类型
export type { Document, DocumentGroup, DocumentMetadata } from '../types/document'
export type { ChatMessage, ChatSession, SuggestedQuestion } from '../types/chat'
export type { StudioOutput, StudioToolType, StudioTool, LayoutConfig } from '../types/studio'
export type { Settings, APIConfig, UIConfig, QuotaConfig } from '../types/settings'
