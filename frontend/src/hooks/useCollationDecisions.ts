/**
 * 校勘判取管理 Hook
 * 从 MultiCollation.tsx 中提取的判取相关逻辑
 */
import { useState, useCallback, useMemo } from 'react'
import { message } from 'antd'
import type {
  CollationDecision,
  VariantItem,
  VariantTableRow,
  DecidedNote,
  DefinitiveTextData,
} from '../types/multiCollation'

// API 基础地址
const API_BASE = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').trim()

interface UseCollationDecisionsOptions {
  projectId: string | null
  variantTableRows?: VariantTableRow[]
}

interface UseCollationDecisionsReturn {
  // 判取状态
  decisions: Record<number, CollationDecision>
  setDecisions: React.Dispatch<React.SetStateAction<Record<number, CollationDecision>>>
  decisionModalVisible: boolean
  currentVariantItem: VariantItem | null

  // 定本生成状态
  definitiveTextModalOpen: boolean
  definitiveTextData: DefinitiveTextData | null
  generatingDefinitive: boolean

  // 判取操作
  handleDecisionConfirm: (decision: CollationDecision) => Promise<void>
  handleDecisionCancel: () => void
  openDecisionModal: (item: VariantItem) => void
  deleteDecision: (position: number) => Promise<void>
  saveAllDecisions: () => Promise<void>

  // 定本生成操作
  generateDefinitiveText: (includeUncertain?: boolean) => Promise<void>
  closeDefinitiveModal: () => void

  // 派生数据
  decidedNotes: DecidedNote[]
  decidedNotesFiltered: (query: string) => DecidedNote[]
  decidedCount: number
  uncertainCount: number
}

export function useCollationDecisions(
  options: UseCollationDecisionsOptions
): UseCollationDecisionsReturn {
  const { projectId, variantTableRows = [] } = options

  // 判取状态
  const [decisions, setDecisions] = useState<Record<number, CollationDecision>>({})
  const [decisionModalVisible, setDecisionModalVisible] = useState(false)
  const [currentVariantItem, setCurrentVariantItem] = useState<VariantItem | null>(null)

  // 定本生成状态
  const [definitiveTextModalOpen, setDefinitiveTextModalOpen] = useState(false)
  const [definitiveTextData, setDefinitiveTextData] = useState<DefinitiveTextData | null>(null)
  const [generatingDefinitive, setGeneratingDefinitive] = useState(false)

  // 确认判取
  const handleDecisionConfirm = useCallback(async (decision: CollationDecision) => {
    setDecisions(prev => ({
      ...prev,
      [decision.position]: decision,
    }))
    setDecisionModalVisible(false)
    setCurrentVariantItem(null)

    // 如果有项目ID，自动保存到后端
    if (projectId) {
      try {
        const response = await fetch(
          `${API_BASE}/api/v1/multi-collation/projects/${projectId}/decisions`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              decisions: { [decision.position]: decision }
            }),
          }
        )
        if (response.ok) {
          message.success(`已判取并保存位置 ${decision.position}：${decision.selectedText}`)
        } else {
          message.warning(`判取已记录，但保存失败`)
        }
      } catch {
        message.warning(`判取已记录，但保存失败`)
      }
    } else {
      message.success(`已判取位置 ${decision.position}：${decision.selectedText}`)
    }
  }, [projectId])

  // 取消判取
  const handleDecisionCancel = useCallback(() => {
    setDecisionModalVisible(false)
    setCurrentVariantItem(null)
  }, [])

  // 打开判取弹窗
  const openDecisionModal = useCallback((item: VariantItem) => {
    setCurrentVariantItem(item)
    setDecisionModalVisible(true)
  }, [])

  // 删除判取
  const deleteDecision = useCallback(async (position: number) => {
    const existing = decisions[position]
    if (!existing) return

    setDecisions((prev) => {
      const next = { ...prev }
      delete next[position]
      return next
    })

    if (!projectId) {
      message.success(`已删除位置 ${position} 的判取结果`)
      return
    }

    try {
      const resp = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${projectId}/decisions/${position}`,
        { method: 'DELETE' }
      )
      if (!resp.ok) {
        throw new Error('删除失败')
      }
      message.success(`已删除位置 ${position} 的判取结果`)
    } catch (e: any) {
      // 恢复判取
      setDecisions((prev) => ({ ...prev, [position]: existing }))
      message.error(e?.message ? `删除失败：${e.message}` : '删除失败')
    }
  }, [decisions, projectId])

  // 批量保存所有判取结果
  const saveAllDecisions = useCallback(async () => {
    if (!projectId) {
      message.warning('请先保存项目')
      return
    }
    if (Object.keys(decisions).length === 0) {
      message.info('暂无判取结果需要保存')
      return
    }

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${projectId}/decisions`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ decisions }),
        }
      )
      if (response.ok) {
        const data = await response.json()
        message.success(`已保存 ${data.total_decisions} 条判取结果`)
      } else {
        throw new Error('保存失败')
      }
    } catch (error: any) {
      message.error('保存判取结果失败: ' + error.message)
    }
  }, [decisions, projectId])

  // 生成定本
  const generateDefinitiveText = useCallback(async (includeUncertain: boolean = false) => {
    if (!projectId) {
      message.warning('请先保存项目')
      return
    }

    setGeneratingDefinitive(true)
    try {
      // 先保存所有判取结果
      if (Object.keys(decisions).length > 0) {
        await fetch(
          `${API_BASE}/api/v1/multi-collation/projects/${projectId}/decisions`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ decisions }),
          }
        )
      }

      // 生成定本
      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${projectId}/generate-definitive-text`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ include_uncertain: includeUncertain }),
        }
      )

      if (!response.ok) {
        throw new Error('生成定本失败')
      }

      const data = await response.json()
      setDefinitiveTextData({
        text: data.definitive_text,
        notes: data.collation_notes,
        statistics: data.statistics,
      })
      setDefinitiveTextModalOpen(true)
    } catch (error: any) {
      message.error(error.message || '生成定本失败')
    } finally {
      setGeneratingDefinitive(false)
    }
  }, [decisions, projectId])

  // 关闭定本弹窗
  const closeDefinitiveModal = useCallback(() => {
    setDefinitiveTextModalOpen(false)
  }, [])

  // 已判取列表
  const decidedNotes = useMemo(() => {
    const rowMap = new Map(variantTableRows.map((r) => [r.position, r]))

    return Object.entries(decisions)
      .map(([posStr, d]) => {
        const position = parseInt(posStr)
        const row = rowMap.get(position)
        return {
          position,
          context: row?.context || '',
          category: row?.category || '',
          base_char: row?.base_char || '',
          selectedText: d.selectedText,
          selectedVersion: d.selectedVersion,
          uncertain: !!d.uncertain,
          note: d.note || '',
        }
      })
      .sort((a, b) => a.position - b.position)
  }, [decisions, variantTableRows])

  // 过滤已判取列表
  const decidedNotesFiltered = useCallback((query: string) => {
    const q = query.trim().toLowerCase()
    if (!q) return decidedNotes
    return decidedNotes.filter((r) => {
      const haystack = [
        r.position.toString(),
        r.context,
        r.category,
        r.base_char,
        r.selectedText,
        r.selectedVersion,
        r.note,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(q)
    })
  }, [decidedNotes])

  // 判取计数
  const decidedCount = useMemo(() => Object.keys(decisions).length, [decisions])
  const uncertainCount = useMemo(() =>
    Object.values(decisions).filter(d => d.uncertain).length,
    [decisions]
  )

  return {
    // 状态
    decisions,
    setDecisions,
    decisionModalVisible,
    currentVariantItem,
    definitiveTextModalOpen,
    definitiveTextData,
    generatingDefinitive,

    // 操作
    handleDecisionConfirm,
    handleDecisionCancel,
    openDecisionModal,
    deleteDecision,
    saveAllDecisions,
    generateDefinitiveText,
    closeDefinitiveModal,

    // 派生数据
    decidedNotes,
    decidedNotesFiltered,
    decidedCount,
    uncertainCount,
  }
}
