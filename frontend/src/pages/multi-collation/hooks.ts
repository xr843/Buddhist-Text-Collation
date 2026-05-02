/**
 * 版本对勘自定义 Hooks
 */

import { useState, useCallback, useMemo } from 'react'
import { message } from 'antd'
import type {
  ProjectSummary,
  CollationDecision,
  VariantTableRow,
} from './types'
import {
  fetchProjectList,
  deleteProject as apiDeleteProject,
  updateProjectTitle as apiUpdateProjectTitle,
  fetchDecisions,
  saveDecisions as apiSaveDecisions,
  deleteDecision as apiDeleteDecision,
} from './api'
import {
  buildDecidedNotes,
  scrollToVariantRow,
  copyToClipboard,
} from './utils'
import { getCollationDisplayOrder } from './constants'

/**
 * 项目管理 Hook
 */
export function useProjectManager() {
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null)
  const [currentProjectTitle, setCurrentProjectTitle] = useState<string>('')
  const [projectDrawerOpen, setProjectDrawerOpen] = useState(false)
  const [projectList, setProjectList] = useState<ProjectSummary[]>([])
  const [projectListLoading, setProjectListLoading] = useState(false)
  const [projectListTotal, setProjectListTotal] = useState(0)
  const [editingTitle, setEditingTitle] = useState(false)
  const [projectSearch, setProjectSearch] = useState('')

  const loadProjectList = useCallback(async () => {
    setProjectListLoading(true)
    try {
      const { items, total } = await fetchProjectList(50)
      setProjectList(items)
      setProjectListTotal(total)
    } catch (error: any) {
      message.error('加载项目列表失败: ' + error.message)
    } finally {
      setProjectListLoading(false)
    }
  }, [])

  const openProjectDrawer = useCallback(() => {
    setProjectSearch('')
    setProjectDrawerOpen(true)
    loadProjectList()
  }, [loadProjectList])

  const filteredProjectList = useMemo(() => {
    const q = projectSearch.trim().toLowerCase()
    if (!q) return projectList
    return projectList.filter((p) => {
      const haystack = [
        p.id,
        p.title,
        p.description,
        p.metadata?.base_name,
        ...(p.metadata?.collation_names || []),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(q)
    })
  }, [projectList, projectSearch])

  const deleteProject = useCallback(async (projectId: string) => {
    try {
      await apiDeleteProject(projectId)
      message.success('项目已删除')
      loadProjectList()

      if (projectId === currentProjectId) {
        setCurrentProjectId(null)
        setCurrentProjectTitle('')
        return true // 返回是否需要清空结果
      }
      return false
    } catch (error: any) {
      message.error('删除项目失败: ' + error.message)
      return false
    }
  }, [currentProjectId, loadProjectList])

  const updateProjectTitle = useCallback(async (newTitle: string) => {
    if (!currentProjectId || !newTitle.trim()) return false
    try {
      await apiUpdateProjectTitle(currentProjectId, newTitle)
      setCurrentProjectTitle(newTitle.trim())
      message.success('项目标题已更新')
      setEditingTitle(false)
      return true
    } catch (error: any) {
      message.error('更新失败: ' + error.message)
      return false
    }
  }, [currentProjectId])

  const copyProjectId = useCallback(async () => {
    if (!currentProjectId) return
    await copyToClipboard(currentProjectId)
    message.success('项目ID已复制')
  }, [currentProjectId])

  const createNewProject = useCallback(() => {
    setCurrentProjectId(null)
    setCurrentProjectTitle('')
    setProjectDrawerOpen(false)
  }, [])

  return {
    currentProjectId,
    setCurrentProjectId,
    currentProjectTitle,
    setCurrentProjectTitle,
    projectDrawerOpen,
    setProjectDrawerOpen,
    projectList,
    projectListLoading,
    projectListTotal,
    editingTitle,
    setEditingTitle,
    projectSearch,
    setProjectSearch,
    loadProjectList,
    openProjectDrawer,
    filteredProjectList,
    deleteProject,
    updateProjectTitle,
    copyProjectId,
    createNewProject,
  }
}

/**
 * 校勘判取 Hook
 */
export function useDecisionManager(
  currentProjectId: string | null,
  variantRows: VariantTableRow[] | undefined
) {
  const [decisions, setDecisions] = useState<Record<number, CollationDecision>>({})
  const [decisionModalVisible, setDecisionModalVisible] = useState(false)
  const [currentVariantItem, setCurrentVariantItem] = useState<{
    position: number
    context: string
    base_char: string
    coll_values: string[]
    category: string
  } | null>(null)

  // 加载判取结果
  const loadDecisions = useCallback(async (projectId: string) => {
    try {
      const loadedDecisions = await fetchDecisions(projectId)
      setDecisions(loadedDecisions)
      if (Object.keys(loadedDecisions).length > 0) {
        message.info(`已加载 ${Object.keys(loadedDecisions).length} 条判取记录`)
      }
    } catch (error) {
      console.error('加载判取结果失败:', error)
    }
  }, [])

  // 确认判取
  const handleDecisionConfirm = useCallback(async (decision: CollationDecision) => {
    setDecisions(prev => ({
      ...prev,
      [decision.position]: decision,
    }))
    setDecisionModalVisible(false)
    setCurrentVariantItem(null)

    if (currentProjectId) {
      try {
        await apiSaveDecisions(currentProjectId, { [decision.position]: decision })
        message.success(`已判取并保存位置 ${decision.position}：${decision.selectedText}`)
      } catch {
        message.warning(`判取已记录，但保存失败`)
      }
    } else {
      message.success(`已判取位置 ${decision.position}：${decision.selectedText}`)
    }
  }, [currentProjectId])

  // 取消判取
  const handleDecisionCancel = useCallback(() => {
    setDecisionModalVisible(false)
    setCurrentVariantItem(null)
  }, [])

  // 批量保存
  const saveAllDecisions = useCallback(async () => {
    if (!currentProjectId) {
      message.warning('请先保存项目')
      return
    }
    if (Object.keys(decisions).length === 0) {
      message.info('暂无判取结果需要保存')
      return
    }

    try {
      const data = await apiSaveDecisions(currentProjectId, decisions)
      message.success(`已保存 ${data.total_decisions} 条判取结果`)
    } catch (error: any) {
      message.error('保存判取结果失败: ' + error.message)
    }
  }, [currentProjectId, decisions])

  // 删除判取
  const deleteDecisionByPosition = useCallback(async (position: number) => {
    const existing = decisions[position]
    if (!existing) return

    setDecisions((prev) => {
      const next = { ...prev }
      delete next[position]
      return next
    })

    if (!currentProjectId) {
      message.success(`已删除位置 ${position} 的判取结果`)
      return
    }

    try {
      await apiDeleteDecision(currentProjectId, position)
      message.success(`已删除位置 ${position} 的判取结果`)
    } catch (e: any) {
      setDecisions((prev) => ({ ...prev, [position]: existing }))
      message.error(e?.message ? `删除失败：${e.message}` : '删除失败')
    }
  }, [currentProjectId, decisions])

  // 已判取记录
  const decidedNotes = useMemo(
    () => buildDecidedNotes(decisions, variantRows),
    [decisions, variantRows]
  )

  return {
    decisions,
    setDecisions,
    decisionModalVisible,
    setDecisionModalVisible,
    currentVariantItem,
    setCurrentVariantItem,
    loadDecisions,
    handleDecisionConfirm,
    handleDecisionCancel,
    saveAllDecisions,
    deleteDecisionByPosition,
    decidedNotes,
  }
}

/**
 * 异文表导航 Hook
 */
export function useVariantNavigation(
  variantRows: VariantTableRow[] | undefined,
  variantTablePageSize: number
) {
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [variantTablePage, setVariantTablePage] = useState(1)

  const jumpToVariantPosition = useCallback((
    position: number,
    setActiveTab: (tab: string) => void
  ) => {
    if (!variantRows) return

    setCategoryFilter('all')
    setActiveTab('variant_table')

    const idx = variantRows.findIndex((r) => r.position === position)
    if (idx >= 0) {
      const page = Math.floor(idx / variantTablePageSize) + 1
      setVariantTablePage(page)
    } else {
      setVariantTablePage(1)
    }

    // 等待表格渲染后再滚动定位
    window.setTimeout(() => {
      if (scrollToVariantRow(position)) return
      window.setTimeout(() => {
        scrollToVariantRow(position)
      }, 80)
    }, 60)
  }, [variantRows, variantTablePageSize])

  return {
    categoryFilter,
    setCategoryFilter,
    variantTablePage,
    setVariantTablePage,
    jumpToVariantPosition,
  }
}

/**
 * 校本显示顺序 Hook
 */
export function useCollationOrder(collationNames: string[] | undefined) {
  const collationDisplayOrder = useMemo(() => {
    const names = collationNames || []
    return getCollationDisplayOrder(names)
  }, [collationNames])

  const collationDisplayRank = useMemo(() => {
    const rank: Record<number, number> = {}
    collationDisplayOrder.forEach((origIdx, displayIdx) => {
      rank[origIdx] = displayIdx
    })
    return rank
  }, [collationDisplayOrder])

  return {
    collationDisplayOrder,
    collationDisplayRank,
  }
}
