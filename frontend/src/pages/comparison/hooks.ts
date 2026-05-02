/**
 * 标点对比模块自定义 Hooks
 */

import { useState, useMemo, useCallback, useEffect } from 'react'
import { message } from 'antd'
import {
  fetchProjectList,
  deleteProject as apiDeleteProject,
  updateProjectTitle as apiUpdateProjectTitle,
  fetchDecisions,
  saveDecisions as apiSaveDecisions,
  generateDefinitive as apiGenerateDefinitive,
  compareFiles,
} from './api'
import { getCategoryForPunct, PUNCTUATION_CATEGORIES } from './constants'
import type {
  ProjectSummary,
  PunctuationComparisonResponse,
  PunctuationDifference,
  PunctuationDecision,
  PunctuationDefinitiveData,
} from './types'

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

  const filteredProjectList = useMemo(() => {
    const query = projectSearch.trim().toLowerCase()
    if (!query) return projectList
    return projectList.filter((item) => {
      const haystack = [
        item.id,
        item.title,
        item.metadata?.version1_name,
        item.metadata?.version2_name,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(query)
    })
  }, [projectList, projectSearch])

  const loadProjectList = useCallback(async () => {
    setProjectListLoading(true)
    try {
      const { items, total } = await fetchProjectList()
      setProjectList(items)
      setProjectListTotal(total)
    } catch (error: any) {
      message.error('加载项目列表失败: ' + error.message)
    } finally {
      setProjectListLoading(false)
    }
  }, [])

  const openProjectDrawer = useCallback(() => {
    setProjectDrawerOpen(true)
    setProjectSearch('')
    loadProjectList()
  }, [loadProjectList])

  const deleteProject = useCallback(
    async (projectId: string) => {
      try {
        await apiDeleteProject(projectId)
        message.success('项目已删除')
        loadProjectList()

        if (projectId === currentProjectId) {
          setCurrentProjectId(null)
          setCurrentProjectTitle('')
          return true // 表示删除了当前项目
        }
        return false
      } catch (error: any) {
        message.error('删除项目失败: ' + error.message)
        return false
      }
    },
    [currentProjectId, loadProjectList]
  )

  const updateProjectTitle = useCallback(
    async (newTitle: string) => {
      if (!currentProjectId || !newTitle.trim()) return
      try {
        await apiUpdateProjectTitle(currentProjectId, newTitle)
        setCurrentProjectTitle(newTitle.trim())
        message.success('项目标题已更新')
      } catch (error: any) {
        message.error('更新失败: ' + error.message)
      }
      setEditingTitle(false)
    },
    [currentProjectId]
  )

  const createNewProject = useCallback(() => {
    setCurrentProjectId(null)
    setCurrentProjectTitle('')
    setProjectDrawerOpen(false)
  }, [])

  const copyProjectId = useCallback(async () => {
    if (!currentProjectId) return
    try {
      await navigator.clipboard.writeText(currentProjectId)
      message.success('项目ID已复制')
    } catch {
      const textarea = document.createElement('textarea')
      textarea.value = currentProjectId
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      message.success('项目ID已复制')
    }
  }, [currentProjectId])

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
    filteredProjectList,
    loadProjectList,
    openProjectDrawer,
    deleteProject,
    updateProjectTitle,
    createNewProject,
    copyProjectId,
  }
}

/**
 * 判取管理 Hook
 */
export function useDecisionManager(
  currentProjectId: string | null,
  result: PunctuationComparisonResponse | null,
  selectedDiff: PunctuationDifference | null,
  filteredDifferences: PunctuationDifference[],
  currentDiffIndex: number,
  setCurrentDiffIndex: (index: number) => void,
  setSelectedDiff: (diff: PunctuationDifference | null) => void
) {
  const [decisionMode, setDecisionMode] = useState(false)
  const [decisions, setDecisions] = useState<Record<number, PunctuationDecision>>({})
  const [definitiveModalOpen, setDefinitiveModalOpen] = useState(false)
  const [definitiveData, setDefinitiveData] = useState<PunctuationDefinitiveData | null>(null)
  const [generatingDefinitive, setGeneratingDefinitive] = useState(false)
  const [savingDecisions, setSavingDecisions] = useState(false)

  const decisionCount = useMemo(() => Object.keys(decisions).length, [decisions])

  const loadDecisions = useCallback(async (projectId: string) => {
    const loadedDecisions = await fetchDecisions(projectId)
    if (Object.keys(loadedDecisions).length > 0) {
      setDecisions(loadedDecisions)
      message.info(`已加载 ${Object.keys(loadedDecisions).length} 条判取结果`)
    }
  }, [])

  const handleDecision = useCallback(
    (version: 'version1' | 'version2', note?: string) => {
      if (!selectedDiff || !result) return

      const newDecision: PunctuationDecision = {
        diffId: selectedDiff.id,
        position: selectedDiff.position_v1 ?? selectedDiff.position,
        selectedVersion: version,
        selectedPunct:
          version === 'version1' ? selectedDiff.version1_punct : selectedDiff.version2_punct,
        note: note || undefined,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }

      setDecisions((prev) => ({
        ...prev,
        [selectedDiff.id]: newDecision,
      }))

      message.success(
        `已采用 ${version === 'version1' ? result.version1_name : result.version2_name} 的标点`
      )

      // 自动跳到下一个
      if (currentDiffIndex < filteredDifferences.length - 1) {
        const newIndex = currentDiffIndex + 1
        setCurrentDiffIndex(newIndex)
        setSelectedDiff(filteredDifferences[newIndex])
      }
    },
    [selectedDiff, result, currentDiffIndex, filteredDifferences, setCurrentDiffIndex, setSelectedDiff]
  )

  const saveDecisions = useCallback(async () => {
    if (!currentProjectId) {
      message.warning('请先保存项目')
      return
    }

    if (Object.keys(decisions).length === 0) {
      message.warning('暂无判取结果')
      return
    }

    setSavingDecisions(true)
    try {
      await apiSaveDecisions(currentProjectId, decisions)
      message.success(`已保存 ${Object.keys(decisions).length} 条判取结果`)
    } catch (error: any) {
      message.error('保存判取失败: ' + error.message)
    } finally {
      setSavingDecisions(false)
    }
  }, [currentProjectId, decisions])

  const generateDefinitiveText = useCallback(async () => {
    if (!currentProjectId) {
      message.warning('请先保存项目')
      return
    }

    if (Object.keys(decisions).length === 0) {
      message.warning('请先进行标点判取')
      return
    }

    // 先保存判取结果
    await saveDecisions()

    setGeneratingDefinitive(true)
    try {
      const data = await apiGenerateDefinitive(currentProjectId)
      setDefinitiveData(data)
      setDefinitiveModalOpen(true)
    } catch (error: any) {
      message.error('生成定本失败: ' + error.message)
    } finally {
      setGeneratingDefinitive(false)
    }
  }, [currentProjectId, decisions, saveDecisions])

  const resetDecisions = useCallback(() => {
    setDecisions({})
    setDecisionMode(false)
  }, [])

  return {
    decisionMode,
    setDecisionMode,
    decisions,
    setDecisions,
    definitiveModalOpen,
    setDefinitiveModalOpen,
    definitiveData,
    generatingDefinitive,
    savingDecisions,
    decisionCount,
    loadDecisions,
    handleDecision,
    saveDecisions,
    generateDefinitiveText,
    resetDecisions,
  }
}

/**
 * 审核导航 Hook
 */
export function useReviewNavigation(filteredDifferences: PunctuationDifference[]) {
  const [reviewStatus, setReviewStatus] = useState<boolean[]>([])
  const [currentDiffIndex, setCurrentDiffIndex] = useState(0)
  const [selectedDiff, setSelectedDiff] = useState<PunctuationDifference | null>(null)
  const [diffNotes, setDiffNotes] = useState<Record<number, string>>({})
  const [reviewDrawerVisible, setReviewDrawerVisible] = useState(false)

  const reviewedCount = useMemo(() => {
    return reviewStatus.filter(Boolean).length
  }, [reviewStatus])

  const reviewProgress = useMemo(() => {
    if (filteredDifferences.length === 0) return 0
    return Math.round((reviewedCount / filteredDifferences.length) * 100)
  }, [reviewedCount, filteredDifferences.length])

  const initReviewStatus = useCallback((diffCount: number) => {
    setReviewStatus(new Array(diffCount).fill(false))
    setCurrentDiffIndex(0)
  }, [])

  const gotoPrevious = useCallback(() => {
    if (!filteredDifferences.length) return
    const newIndex = currentDiffIndex > 0 ? currentDiffIndex - 1 : 0
    setCurrentDiffIndex(newIndex)
    setSelectedDiff(filteredDifferences[newIndex])
  }, [currentDiffIndex, filteredDifferences])

  const gotoNext = useCallback(() => {
    if (!filteredDifferences.length) return
    const newIndex =
      currentDiffIndex < filteredDifferences.length - 1 ? currentDiffIndex + 1 : currentDiffIndex
    setCurrentDiffIndex(newIndex)
    setSelectedDiff(filteredDifferences[newIndex])
  }, [currentDiffIndex, filteredDifferences])

  const markCurrentAsReviewed = useCallback(() => {
    if (currentDiffIndex < 0 || currentDiffIndex >= filteredDifferences.length) return

    setReviewStatus((prev) => {
      const newStatus = [...prev]
      newStatus[currentDiffIndex] = !newStatus[currentDiffIndex]
      return newStatus
    })

    message.success(reviewStatus[currentDiffIndex] ? '已取消审核标记' : '已标记为已审核')
  }, [currentDiffIndex, filteredDifferences.length, reviewStatus])

  // 快捷键监听
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        (e.target as HTMLElement).tagName === 'TEXTAREA' ||
        (e.target as HTMLElement).tagName === 'INPUT'
      ) {
        return
      }

      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault()
          gotoPrevious()
          break
        case 'ArrowRight':
          e.preventDefault()
          gotoNext()
          break
        case 'Enter':
          e.preventDefault()
          markCurrentAsReviewed()
          break
        case ' ':
          e.preventDefault()
          gotoNext()
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [gotoPrevious, gotoNext, markCurrentAsReviewed])

  return {
    reviewStatus,
    setReviewStatus,
    currentDiffIndex,
    setCurrentDiffIndex,
    selectedDiff,
    setSelectedDiff,
    diffNotes,
    setDiffNotes,
    reviewDrawerVisible,
    setReviewDrawerVisible,
    reviewedCount,
    reviewProgress,
    initReviewStatus,
    gotoPrevious,
    gotoNext,
    markCurrentAsReviewed,
  }
}

/**
 * 差异筛选 Hook
 */
export function useDifferenceFilter(result: PunctuationComparisonResponse | null) {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])

  const filteredDifferences = useMemo(() => {
    if (!result?.punctuation_analysis?.differences) return []

    const allDifferences = result.punctuation_analysis.differences

    // 如果没有选择任何筛选，显示全部差异
    if (selectedCategories.length === 0) {
      return allDifferences
    }

    // 从原始差异列表中筛选（保持位置顺序）
    return allDifferences.filter((diff) => {
      const punct = diff.version1_punct !== '无' ? diff.version1_punct : diff.version2_punct
      if (!punct || punct === '无') return false

      const firstChar = punct[0]
      const category = getCategoryForPunct(firstChar)
      return category && selectedCategories.includes(category)
    })
  }, [result, selectedCategories])

  const toggleCategory = useCallback((category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]
    )
  }, [])

  const selectAllCategories = useCallback(() => {
    setSelectedCategories([...PUNCTUATION_CATEGORIES])
  }, [])

  const clearCategories = useCallback(() => {
    setSelectedCategories([])
  }, [])

  return {
    selectedCategories,
    setSelectedCategories,
    filteredDifferences,
    toggleCategory,
    selectAllCategories,
    clearCategories,
  }
}

/**
 * 文件对比 Hook
 */
export function useFileCompare() {
  const [result, setResult] = useState<PunctuationComparisonResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const handleCompare = useCallback(
    async (
      file1: File,
      file2: File,
      version1Name: string,
      version2Name: string
    ): Promise<{
      result: PunctuationComparisonResponse
      projectId?: string
      projectTitle?: string
    } | null> => {
      setLoading(true)
      setResult(null)

      try {
        const response = await compareFiles(file1, file2, version1Name, version2Name)
        console.log('[标点对比] 响应:', response)

        setResult(response)

        const projectInfo = response.project
          ? { projectId: response.project.id, projectTitle: response.project.title }
          : {}

        message.success(response.project ? '标点对比完成，项目已保存！' : '标点对比分析完成！')

        return { result: response, ...projectInfo }
      } catch (error: any) {
        console.error('[标点对比] 错误:', error)
        const errorMsg = error.message || '对比失败，请稀后重试'
        message.error(errorMsg)
        return null
      } finally {
        setLoading(false)
      }
    },
    []
  )

  return {
    result,
    setResult,
    loading,
    handleCompare,
  }
}
