/**
 * 版本对勘项目管理 Hook
 * 从 MultiCollation.tsx 中提取的项目管理相关逻辑
 */
import { useState, useCallback, useMemo } from 'react'
import { message } from 'antd'
import type {
  MultiCollationResponse,
  ProjectSummary,
  FullProject,
  CollationDecision,
} from '../types/multiCollation'
import { apiFetchJson } from '../utils/apiFetch'

// API 基础地址
const API_BASE = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').trim()

interface UseMultiCollationProjectOptions {
  onDecisionsLoaded?: (decisions: Record<number, CollationDecision>) => void
}

interface UseMultiCollationProjectReturn {
  // 项目状态
  currentProjectId: string | null
  currentProjectTitle: string
  projectList: ProjectSummary[]
  projectListLoading: boolean
  projectListTotal: number
  projectSearch: string

  // 状态设置函数
  setCurrentProjectId: (id: string | null) => void
  setCurrentProjectTitle: (title: string) => void
  setProjectSearch: (search: string) => void

  // 项目操作
  loadProjectList: () => Promise<void>
  loadProject: (projectId: string) => Promise<MultiCollationResponse | null>
  deleteProject: (projectId: string) => Promise<void>
  updateProjectTitle: (newTitle: string) => Promise<void>
  createNewProject: () => void
  copyProjectId: () => Promise<void>

  // 过滤后的项目列表
  filteredProjectList: ProjectSummary[]
}

export function useMultiCollationProject(
  options: UseMultiCollationProjectOptions = {}
): UseMultiCollationProjectReturn {
  const { onDecisionsLoaded } = options

  // 项目状态
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null)
  const [currentProjectTitle, setCurrentProjectTitle] = useState<string>('')
  const [projectList, setProjectList] = useState<ProjectSummary[]>([])
  const [projectListLoading, setProjectListLoading] = useState(false)
  const [projectListTotal, setProjectListTotal] = useState(0)
  const [projectSearch, setProjectSearch] = useState('')

  // 加载项目列表
  const loadProjectList = useCallback(async () => {
    setProjectListLoading(true)
    try {
      const data = await apiFetchJson<{ items?: ProjectSummary[]; total?: number }>(
        '/api/v1/multi-collation/projects?limit=50',
        { retries: 2 }
      )
      setProjectList(data.items || [])
      setProjectListTotal(data.total || 0)
    } catch (error: any) {
      message.error('加载项目列表失败: ' + error.message)
    } finally {
      setProjectListLoading(false)
    }
  }, [])

  // 加载判取结果
  const loadDecisions = useCallback(async (projectId: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${projectId}/decisions`
      )
      if (response.ok) {
        const data = await response.json()
        if (data.decisions) {
          const loadedDecisions: Record<number, CollationDecision> = {}
          for (const [pos, decision] of Object.entries(data.decisions)) {
            loadedDecisions[parseInt(pos)] = decision as CollationDecision
          }
          onDecisionsLoaded?.(loadedDecisions)
          if (Object.keys(loadedDecisions).length > 0) {
            message.info(`已加载 ${Object.keys(loadedDecisions).length} 条判取记录`)
          }
        }
      }
    } catch (error) {
      console.error('加载判取结果失败:', error)
    }
  }, [onDecisionsLoaded])

  // 加载项目详情
  const loadProject = useCallback(async (projectId: string): Promise<MultiCollationResponse | null> => {
    try {
      const data = await apiFetchJson<{ project: FullProject }>(
        `/api/v1/multi-collation/projects/${projectId}`,
        { retries: 2 }
      )
      const project: FullProject = data.project

      // 构建结果对象
      const result: MultiCollationResponse = {
        success: true,
        mode: 'multi_collation',
        mode_description: '一底多校模式',
        processing_time: 0,
        base: project.data.base,
        collations: project.data.collations,
        summary: project.data.summary,
        variant_table: project.data.variant_table,
        phylogeny: project.data.phylogeny,
        project: {
          id: project.id,
          title: project.title,
          created_at: project.created_at,
          updated_at: project.updated_at,
        },
      }

      setCurrentProjectId(project.id)
      setCurrentProjectTitle(project.title)

      // 加载判取结果
      await loadDecisions(projectId)

      message.success(`已加载项目: ${project.title}`)
      return result
    } catch (error: any) {
      message.error('加载项目失败: ' + error.message)
      return null
    }
  }, [loadDecisions])

  // 删除项目
  const deleteProject = useCallback(async (projectId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/multi-collation/projects/${projectId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMsg = errorData.detail || '删除失败'
        throw new Error(errorMsg)
      }

      message.success('项目已删除')
      loadProjectList()

      // 如果删除的是当前项目，清空状态
      if (projectId === currentProjectId) {
        setCurrentProjectId(null)
        setCurrentProjectTitle('')
      }
    } catch (error: any) {
      message.error('删除项目失败: ' + error.message)
    }
  }, [currentProjectId, loadProjectList])

  // 更新项目标题
  const updateProjectTitle = useCallback(async (newTitle: string) => {
    if (!currentProjectId || !newTitle.trim()) return
    try {
      const response = await fetch(`${API_BASE}/api/v1/multi-collation/projects/${currentProjectId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle.trim() }),
      })
      if (!response.ok) throw new Error('更新失败')
      setCurrentProjectTitle(newTitle.trim())
      message.success('项目标题已更新')
    } catch (error: any) {
      message.error('更新失败: ' + error.message)
    }
  }, [currentProjectId])

  // 新建项目（清空当前状态）
  const createNewProject = useCallback(() => {
    setCurrentProjectId(null)
    setCurrentProjectTitle('')
  }, [])

  // 复制项目ID
  const copyProjectId = useCallback(async () => {
    if (!currentProjectId) return
    try {
      await navigator.clipboard.writeText(currentProjectId)
      message.success('项目ID已复制')
    } catch {
      // 降级方案
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

  // 过滤后的项目列表
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

  return {
    // 状态
    currentProjectId,
    currentProjectTitle,
    projectList,
    projectListLoading,
    projectListTotal,
    projectSearch,

    // 状态设置函数
    setCurrentProjectId,
    setCurrentProjectTitle,
    setProjectSearch,

    // 操作
    loadProjectList,
    loadProject,
    deleteProject,
    updateProjectTitle,
    createNewProject,
    copyProjectId,

    // 派生数据
    filteredProjectList,
  }
}
