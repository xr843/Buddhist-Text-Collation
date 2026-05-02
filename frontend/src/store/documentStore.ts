/**
 * 文档状态管理 - 全局文档库
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Document, DocumentGroup } from '../types/document'

interface DocumentState {
  // 状态
  documents: Document[]
  groups: DocumentGroup[]
  selectedDocIds: number[]
  nextDocId: number
  nextGroupId: number

  // 文档操作
  addDocument: (doc: Omit<Document, 'id' | 'createdAt' | 'updatedAt'>) => Document
  updateDocument: (id: number, updates: Partial<Document>) => void
  removeDocument: (id: number) => void
  getDocument: (id: number) => Document | undefined

  // 选择操作
  selectDocument: (id: number) => void
  deselectDocument: (id: number) => void
  toggleSelectDocument: (id: number) => void
  selectAll: () => void
  deselectAll: () => void
  getSelectedDocuments: () => Document[]

  // 分组操作
  createGroup: (name: string, description?: string) => DocumentGroup
  updateGroup: (id: number, updates: Partial<DocumentGroup>) => void
  removeGroup: (id: number) => void
  addDocumentToGroup: (docId: number, groupId: number) => void
  removeDocumentFromGroup: (docId: number, groupId: number) => void

  // 工具方法
  getDocumentsByGroup: (groupId: number) => Document[]
  getUngroupedDocuments: () => Document[]
  searchDocuments: (query: string) => Document[]
}

export const useDocumentStore = create<DocumentState>()(
  persist(
    (set, get) => ({
      // 初始状态
      documents: [],
      groups: [],
      selectedDocIds: [],
      nextDocId: 1,
      nextGroupId: 1,

      // 文档操作
      addDocument: (doc) => {
        const now = new Date()
        const newDoc: Document = {
          ...doc,
          id: get().nextDocId,
          createdAt: now,
          updatedAt: now,
        }
        set((state) => ({
          documents: [...state.documents, newDoc],
          nextDocId: state.nextDocId + 1,
        }))
        return newDoc
      },

      updateDocument: (id, updates) => {
        set((state) => ({
          documents: state.documents.map((doc) =>
            doc.id === id
              ? { ...doc, ...updates, updatedAt: new Date() }
              : doc
          ),
        }))
      },

      removeDocument: (id) => {
        set((state) => ({
          documents: state.documents.filter((doc) => doc.id !== id),
          selectedDocIds: state.selectedDocIds.filter((docId) => docId !== id),
          // 从所有分组中移除
          groups: state.groups.map((group) => ({
            ...group,
            documentIds: group.documentIds.filter((docId) => docId !== id),
          })),
        }))
      },

      getDocument: (id) => {
        return get().documents.find((doc) => doc.id === id)
      },

      // 选择操作
      selectDocument: (id) => {
        set((state) => ({
          selectedDocIds: state.selectedDocIds.includes(id)
            ? state.selectedDocIds
            : [...state.selectedDocIds, id],
        }))
      },

      deselectDocument: (id) => {
        set((state) => ({
          selectedDocIds: state.selectedDocIds.filter((docId) => docId !== id),
        }))
      },

      toggleSelectDocument: (id) => {
        const { selectedDocIds } = get()
        if (selectedDocIds.includes(id)) {
          get().deselectDocument(id)
        } else {
          get().selectDocument(id)
        }
      },

      selectAll: () => {
        set((state) => ({
          selectedDocIds: state.documents.map((doc) => doc.id),
        }))
      },

      deselectAll: () => {
        set({ selectedDocIds: [] })
      },

      getSelectedDocuments: () => {
        const { documents, selectedDocIds } = get()
        return documents.filter((doc) => selectedDocIds.includes(doc.id))
      },

      // 分组操作
      createGroup: (name, description) => {
        const newGroup: DocumentGroup = {
          id: get().nextGroupId,
          name,
          description,
          createdAt: new Date(),
          documentIds: [],
        }
        set((state) => ({
          groups: [...state.groups, newGroup],
          nextGroupId: state.nextGroupId + 1,
        }))
        return newGroup
      },

      updateGroup: (id, updates) => {
        set((state) => ({
          groups: state.groups.map((group) =>
            group.id === id ? { ...group, ...updates } : group
          ),
        }))
      },

      removeGroup: (id) => {
        set((state) => ({
          groups: state.groups.filter((group) => group.id !== id),
          // 将分组内的文档移到未分组
          documents: state.documents.map((doc) =>
            doc.groupId === id ? { ...doc, groupId: undefined } : doc
          ),
        }))
      },

      addDocumentToGroup: (docId, groupId) => {
        set((state) => ({
          documents: state.documents.map((doc) =>
            doc.id === docId ? { ...doc, groupId } : doc
          ),
          groups: state.groups.map((group) =>
            group.id === groupId && !group.documentIds.includes(docId)
              ? { ...group, documentIds: [...group.documentIds, docId] }
              : group
          ),
        }))
      },

      removeDocumentFromGroup: (docId, groupId) => {
        set((state) => ({
          documents: state.documents.map((doc) =>
            doc.id === docId && doc.groupId === groupId
              ? { ...doc, groupId: undefined }
              : doc
          ),
          groups: state.groups.map((group) =>
            group.id === groupId
              ? { ...group, documentIds: group.documentIds.filter((id) => id !== docId) }
              : group
          ),
        }))
      },

      // 工具方法
      getDocumentsByGroup: (groupId) => {
        return get().documents.filter((doc) => doc.groupId === groupId)
      },

      getUngroupedDocuments: () => {
        return get().documents.filter((doc) => !doc.groupId)
      },

      searchDocuments: (query) => {
        const lowerQuery = query.toLowerCase()
        return get().documents.filter(
          (doc) =>
            doc.name.toLowerCase().includes(lowerQuery) ||
            doc.content.toLowerCase().includes(lowerQuery) ||
            doc.metadata?.translator?.toLowerCase().includes(lowerQuery) ||
            doc.tags?.some((tag) => tag.toLowerCase().includes(lowerQuery))
        )
      },
    }),
    {
      name: 'buddhist-documents',
      partialize: (state) => ({
        documents: state.documents,
        groups: state.groups,
        nextDocId: state.nextDocId,
        nextGroupId: state.nextGroupId,
      }),
    }
  )
)
