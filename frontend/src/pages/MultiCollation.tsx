/**
 * 版本对勘页面 - 含异文汇校表和版本谱系分析
 * 支持项目持久化存储（保存/加载/列表/删除/追加校本）
 */
import { useState, useCallback, useEffect, useMemo, useRef } from 'react'
import {
  Card,
  Upload,
  Button,
  Typography,
  Space,
  message,
  Spin,
  Table,
  Tag,
  Divider,
  Row,
  Col,
  Statistic,
  Alert,
  Select,
  Dropdown,
  Tooltip,
  Drawer,
  List,
  Empty,
  Popconfirm,
  Input,
  Modal,
} from 'antd'
import {
  UploadOutlined,
  FileTextOutlined,
  BookOutlined,
  BarChartOutlined,
  TableOutlined,
  DownOutlined,
  DownloadOutlined,
  InboxOutlined,
  HistoryOutlined,
  DeleteOutlined,
  FolderOpenOutlined,
  PlusOutlined,
  EditOutlined,
  SaveOutlined,
  ApartmentOutlined,
  CopyOutlined,
  DragOutlined,
  OrderedListOutlined,
} from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import { useLocation } from 'react-router-dom'
import CollationView from '../components/CollationView'
import PhylogenyAnalysis from '../components/PhylogenyAnalysis'
import CollationNotePanel from '../components/CollationNotePanel'
import { apiFetchJson } from '../utils/apiFetch'
import CollationDecisionModal, {
  CollationDecision,
  VariantItem,
} from '../components/CollationDecisionModal'
import {
  CheckCircleOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons'
import Draggable from 'react-draggable'
import type { DraggableData, DraggableEvent } from 'react-draggable'
import { parseVersionInfo, getShortName } from '../utils/versionParser'
import {
  downloadDefinitiveText,
  downloadCollationNotes,
  type DefinitiveTextData,
} from '../utils/exportUtils'
import {
  MAX_COLLATION_FILES,
  DEFAULT_PAGE_SIZE,
  SYSTEM_COLORS,
} from '../constants/multiCollation'

const { Text } = Typography

// API 基础地址（使用 Vite 代理，留空使用相对路径）
const API_BASE = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').trim()

// 版本系统展示顺序：中系 → 南系 → 北系 → 未知
const SYSTEM_DISPLAY_ORDER: Record<string, number> = {
  '中系': 0,
  '南系': 1,
  '北系': 2,
  '未知': 3,
}

const getCollationDisplayOrder = (names: string[]) =>
  names
    .map((name, idx) => ({ idx, system: parseVersionInfo(name).system }))
    .sort((a, b) => {
      const sa = SYSTEM_DISPLAY_ORDER[a.system] ?? SYSTEM_DISPLAY_ORDER['未知']
      const sb = SYSTEM_DISPLAY_ORDER[b.system] ?? SYSTEM_DISPLAY_ORDER['未知']
      if (sa !== sb) return sa - sb
      return a.idx - b.idx
    })
    .map(({ idx }) => idx)

interface CollationResult {
  collation_name: string
  collation_file: string
  char_count: number
  result: {
    mode: string
    mode_description: string
    version1_name: string
    version2_name: string
    statistics: any
    similarity: number
    aligned_sentences: any[]
    side_by_side: any
  }
}

interface VariantTableRow {
  position: number
  context: string
  base_char: string
  coll_values: string[]
  category: string
}

interface PhylogenyNode {
  name: string
  similarity?: number
  system?: string
  is_group?: boolean
  children: PhylogenyNode[]
}

interface SharedErrorDetail {
  position: number
  base_char: string
  shared_error_char?: string
  shared_char?: string
  category?: string
}

interface SharedErrors {
  names: string[]
  // 讹误（默认）
  matrix: number[][]
  details?: Record<string, SharedErrorDetail[]>
  total_by_version?: Record<string, number>
  // 异体字
  variant_matrix?: number[][]
  variant_details?: Record<string, SharedErrorDetail[]>
  variant_total_by_version?: Record<string, number>
  // 衍脱
  yantuo_matrix?: number[][]
  yantuo_details?: Record<string, SharedErrorDetail[]>
  yantuo_total_by_version?: Record<string, number>
}

interface MultiCollationResponse {
  success: boolean
  mode: string
  mode_description: string
  processing_time: number
  base: {
    name: string
    file: string
    char_count: number
    text: string
  }
  collations: CollationResult[]
  summary: {
    base_name: string
    collation_names: string[]
    stats_table: {
      headers: string[]
      rows: {
        type: string
        type_key: string
        values: number[]
        total: number
      }[]
    }
  }
  variant_table?: {
    headers: string[]
    rows: VariantTableRow[]
    total: number
  }
  phylogeny?: {
    similarity_matrix: {
      names: string[]
      matrix: number[][]
      systems?: Record<string, string>
    }
    shared_errors?: SharedErrors
    tree: PhylogenyNode
    conclusions?: string[]
  }
  // 新增：项目信息
  project?: {
    id: string
    title: string
    created_at: string
    updated_at: string
  }
}

// 项目摘要（用于列表）
interface ProjectSummary {
  id: string
  title: string
  description: string
  status: string
  created_at: string
  updated_at: string
  metadata: {
    base_name?: string
    collation_count?: number
    collation_names?: string[]
    variant_count?: number
    diff_total?: number
  }
}

// 完整项目（用于加载）
interface FullProject {
  id: string
  type: string
  title: string
  description: string
  status: string
  created_at: string
  updated_at: string
  metadata: any
  data: {
    base: MultiCollationResponse['base']
    collations: CollationResult[]
    summary: MultiCollationResponse['summary']
    variant_table: MultiCollationResponse['variant_table']
    phylogeny: MultiCollationResponse['phylogeny']
  }
}

export default function MultiCollation() {
  const location = useLocation()

  // 文件上传状态
  const [baseFile, setBaseFile] = useState<UploadFile | null>(null)
  const [collationFiles, setCollationFiles] = useState<UploadFile[]>([])

  // 结果状态
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<MultiCollationResponse | null>(null)
  const [activeTab, setActiveTab] = useState('summary')

  // 异文汇校表筛选状态
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [variantTablePage, setVariantTablePage] = useState(1)
  const [variantTablePageSize, setVariantTablePageSize] = useState(DEFAULT_PAGE_SIZE)
  const [highlightedPosition, setHighlightedPosition] = useState<number | null>(null)

  // 校勘判取状态
  const [decisions, setDecisions] = useState<Record<number, CollationDecision>>({})
  const [decisionModalVisible, setDecisionModalVisible] = useState(false)
  const [currentVariantItem, setCurrentVariantItem] = useState<VariantItem | null>(null)

  // 初始高亮定位（用于从汇校表跳转到校本详细页）
  const [initialHighlight, setInitialHighlight] = useState<{
    char: string
    collationIdx: number
  } | null>(null)

  // 选中的校本版本（用于工具栏筛选）
  const [selectedVersions, setSelectedVersions] = useState<number[]>([])

  const collationDisplayOrder = useMemo(() => {
    const names = result?.summary?.collation_names || []
    return getCollationDisplayOrder(names)
  }, [result?.summary?.collation_names])

  const collationDisplayRank = useMemo(() => {
    const rank: Record<number, number> = {}
    collationDisplayOrder.forEach((origIdx, displayIdx) => {
      rank[origIdx] = displayIdx
    })
    return rank
  }, [collationDisplayOrder])

  // 当校本数量变化（追加/去除/加载项目）时，修复 selectedVersions/activeTab 等状态，避免索引越界导致白屏
  useEffect(() => {
    if (!result?.collations) return

    const collationCount = result.collations.length

    // 修正 selectedVersions：过滤越界索引
    const filtered = selectedVersions.filter((i) => i >= 0 && i < collationCount)
    const same =
      filtered.length === selectedVersions.length &&
      filtered.every((v, i) => v === selectedVersions[i])
    if (!same) {
      setSelectedVersions(filtered)
    }

    // 修正 activeTab：若当前详情页索引越界则切回汇总
    // 注意：排除 'collation_notes' 这个特殊标签页
    if (activeTab.startsWith('collation_') && activeTab !== 'collation_notes') {
      const idx = parseInt(activeTab.replace('collation_', ''))
      if (!Number.isFinite(idx) || idx < 0 || idx >= collationCount) {
        setActiveTab('summary')
      }
    }

    // 修正 initialHighlight
    if (initialHighlight && initialHighlight.collationIdx >= collationCount) {
      setInitialHighlight(null)
    }
  }, [activeTab, initialHighlight, result?.collations, selectedVersions])

  // 切换项目/结果时，重置异文汇校表分页
  useEffect(() => {
    setVariantTablePage(1)
  }, [result?.variant_table])

  // ==================== 项目管理状态 ====================
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null)
  const [currentProjectTitle, setCurrentProjectTitle] = useState<string>('')
  const [projectDrawerOpen, setProjectDrawerOpen] = useState(false)
  const [projectList, setProjectList] = useState<ProjectSummary[]>([])
  const [projectListLoading, setProjectListLoading] = useState(false)
  const [projectListTotal, setProjectListTotal] = useState(0)
  const [editingTitle, setEditingTitle] = useState(false)
  const [projectSearch, setProjectSearch] = useState('')
  const [addCollationModalOpen, setAddCollationModalOpen] = useState(false)
  const [newCollationFiles, setNewCollationFiles] = useState<UploadFile[]>([])
  const [addingCollations, setAddingCollations] = useState(false)
  const [removeCollationModalOpen, setRemoveCollationModalOpen] = useState(false)
  const [removingCollations, setRemovingCollations] = useState(false)
  const [collationsToRemove, setCollationsToRemove] = useState<number[]>([])

  const createUploadFileFromText = useCallback((name: string, text: string): UploadFile => {
    const filename = name.trim().endsWith('.txt') ? name.trim() : `${name.trim()}.txt`
    const uid = `ocr-${Date.now()}-${Math.random().toString(16).slice(2)}`
    const file = new File([text], filename, { type: 'text/plain' })
    return {
      uid,
      name: filename,
      status: 'done',
      // 不要在 File 对象上挂 uid 等字段：部分浏览器/构建模式下可能是不可扩展对象，导致点击无响应
      originFileObj: file as any,
      size: file.size,
      type: file.type,
    }
  }, [])

  // 检查是否有从 CBETA 导入传来的文本
  useEffect(() => {
    const state = location.state as
      | {
          fromCBETA?: boolean
          prefill?: boolean
          source?: string
          baseText?: string
          baseName?: string
          collationText?: string
          collationName?: string
        }
      | null

    // fromCBETA 为旧的 CBETA 导入入口；prefill 为通用预填入口（如古籍OCR）
    if (state?.fromCBETA || state?.prefill) {
      const src = state.source || (state.fromCBETA ? 'cbeta' : 'prefill')
      const toastKey = `multiCollation:prefill:${src}:${location.key || 'no-key'}`
      if (sessionStorage.getItem(toastKey) !== '1') {
        sessionStorage.setItem(toastKey, '1')

        if (state.baseText) {
          const baseName = (state.baseName || 'CBETA底本').trim() || 'CBETA底本'
          const next = createUploadFileFromText(baseName, state.baseText)

          const apply = () => {
            setBaseFile(next)
            message.success(`已将“${baseName}”填充为底本`)
          }

          if (baseFile) {
            Modal.confirm({
              title: '替换底本？',
              content: `当前已选择底本“${baseFile.name}”，是否替换为“${next.name}”？`,
              okText: '替换',
              okButtonProps: { danger: true },
              cancelText: '取消',
              onOk: apply,
            })
          } else {
            apply()
          }
        }

        if (state.collationText) {
          const collationName = (state.collationName || 'CBETA校本').trim() || 'CBETA校本'
          const next = createUploadFileFromText(collationName, state.collationText)
          setCollationFiles((prev) => [...prev, next].slice(0, MAX_COLLATION_FILES))
          message.success(`已将“${collationName}”填充为校本`)
        }
      }
    }
  }, [baseFile, createUploadFileFromText, location.key, location.state])

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

  // ==================== 校勘判取函数 ====================

  // 确认判取（同时自动保存到后端）
  const handleDecisionConfirm = useCallback(async (decision: CollationDecision) => {
    setDecisions(prev => ({
      ...prev,
      [decision.position]: decision,
    }))
    setDecisionModalVisible(false)
    setCurrentVariantItem(null)

    // 如果有项目ID，自动保存到后端
    if (currentProjectId) {
      try {
        const response = await fetch(
          `${API_BASE}/api/v1/multi-collation/projects/${currentProjectId}/decisions`,
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
  }, [currentProjectId])

  // 取消判取对话框
  const handleDecisionCancel = useCallback(() => {
    setDecisionModalVisible(false)
    setCurrentVariantItem(null)
  }, [])

  // 加载已有判取结果
  const loadDecisions = useCallback(async (projectId: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${projectId}/decisions`
      )
      if (response.ok) {
        const data = await response.json()
        if (data.decisions) {
          // 将后端数据转换为前端格式（key从字符串转为数字）
          const loadedDecisions: Record<number, CollationDecision> = {}
          for (const [pos, decision] of Object.entries(data.decisions)) {
            loadedDecisions[parseInt(pos)] = decision as CollationDecision
          }
          setDecisions(loadedDecisions)
          if (Object.keys(loadedDecisions).length > 0) {
            message.info(`已加载 ${Object.keys(loadedDecisions).length} 条判取记录`)
          }
        }
      }
    } catch (error) {
      console.error('加载判取结果失败:', error)
    }
  }, [])

  // 批量保存所有判取结果
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
      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${currentProjectId}/decisions`,
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
  }, [currentProjectId, decisions])

  // 生成定本
  const [definitiveTextModalOpen, setDefinitiveTextModalOpen] = useState(false)
  const [definitiveTextData, setDefinitiveTextData] = useState<DefinitiveTextData | null>(null)
  const [generatingDefinitive, setGeneratingDefinitive] = useState(false)

  // 定本预览拖动相关状态
  const [definitiveDragDisabled, setDefinitiveDragDisabled] = useState(true)
  const [definitiveDragBounds, setDefinitiveDragBounds] = useState({
    left: 0,
    top: 0,
    bottom: 0,
    right: 0,
  })
  const definitiveDragRef = useRef<HTMLDivElement>(null!)

  const onStartDefinitiveDrag = (_event: DraggableEvent, uiData: DraggableData) => {
    const { clientWidth, clientHeight } = window.document.documentElement
    const targetRect = definitiveDragRef.current?.getBoundingClientRect()
    if (!targetRect) return
    setDefinitiveDragBounds({
      left: -targetRect.left + uiData.x,
      right: clientWidth - (targetRect.right - uiData.x),
      top: -targetRect.top + uiData.y,
      bottom: clientHeight - (targetRect.bottom - uiData.y),
    })
  }

  const getVariantRowByPosition = useCallback((position: number) => {
    const rows = result?.variant_table?.rows
    if (!rows) return null
    return rows.find((r) => r.position === position) || null
  }, [result?.variant_table?.rows])

  const scrollToVariantRow = useCallback((position: number) => {
    const el = document.querySelector(`tr[data-row-key="${position}"]`) as HTMLElement | null
    if (!el) return false
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    // 触发闪烁高亮效果
    setHighlightedPosition(position)
    // 2秒后取消高亮
    setTimeout(() => setHighlightedPosition(null), 2000)
    return true
  }, [])

  const jumpToVariantPosition = useCallback((position: number) => {
    const rows = result?.variant_table?.rows
    if (!rows) return

    setCategoryFilter('all')
    setActiveTab('variant_table')

    const idx = rows.findIndex((r) => r.position === position)
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
  }, [result?.variant_table?.rows, scrollToVariantRow, variantTablePageSize])

  const openDecisionModalForPosition = useCallback((position: number) => {
    const row = getVariantRowByPosition(position)
    if (!row) {
      message.warning('未找到对应异文记录')
      return
    }

    jumpToVariantPosition(position)
    setCurrentVariantItem({
      position: row.position,
      context: row.context,
      base_char: row.base_char,
      coll_values: row.coll_values,
      category: row.category,
    })
    setDecisionModalVisible(true)
  }, [getVariantRowByPosition, jumpToVariantPosition])

  const generateDefinitiveText = useCallback(async (includeUncertain: boolean = false) => {
    if (!currentProjectId) {
      message.warning('请先保存项目')
      return
    }

    setGeneratingDefinitive(true)
    try {
      // 先保存所有判取结果
      if (Object.keys(decisions).length > 0) {
        await fetch(
          `${API_BASE}/api/v1/multi-collation/projects/${currentProjectId}/decisions`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ decisions }),
          }
        )
      }

      // 生成定本
      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${currentProjectId}/generate-definitive-text`,
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
  }, [currentProjectId, decisions])

  // ==================== 项目管理函数 ====================

  // 加载项目列表
  const loadProjectList = useCallback(async () => {
    setProjectListLoading(true)
    try {
      const data = await apiFetchJson<{ items?: any[]; total?: number }>(
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

  // 打开项目列表抽屉
  const openProjectDrawer = useCallback(() => {
    setProjectSearch('')
    setProjectDrawerOpen(true)
    loadProjectList()
  }, [loadProjectList])

  // 加载项目详情
  const loadProject = useCallback(async (projectId: string) => {
    setLoading(true)
    setProjectDrawerOpen(false)
    try {
      const data = await apiFetchJson<{ project: FullProject }>(
        `/api/v1/multi-collation/projects/${projectId}`,
        { retries: 2 }
      )
      const project: FullProject = data.project

      // 将项目数据转换为结果格式
      setResult({
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
      })

      setCurrentProjectId(project.id)
      setCurrentProjectTitle(project.title)
      setActiveTab('summary')
      setBaseFile(null)
      setCollationFiles([])

      // 加载判取结果
      await loadDecisions(projectId)

      message.success(`已加载项目: ${project.title}`)
    } catch (error: any) {
      message.error('加载项目失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }, [loadDecisions])

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

  const handleProjectSearch = useCallback(
    (value: string) => {
      const q = value.trim()
      setProjectSearch(q)
      const exact = projectList.find((p) => p.id === q)
      if (exact) {
        void loadProject(exact.id)
      }
    },
    [loadProject, projectList]
  )

  // 删除项目
  const deleteProject = useCallback(async (projectId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/multi-collation/projects/${projectId}`, {
        method: 'DELETE',
      })

      // 正确解析后端返回的错误信息
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMsg = errorData.detail || '删除失败'
        throw new Error(errorMsg)
      }

      message.success('项目已删除')
      loadProjectList()

      // 如果删除的是当前项目，清空结果
      if (projectId === currentProjectId) {
        setResult(null)
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
      if (result) {
        setResult({
          ...result,
          project: result.project ? { ...result.project, title: newTitle.trim() } : undefined,
        })
      }
      message.success('项目标题已更新')
    } catch (error: any) {
      message.error('更新失败: ' + error.message)
    }
    setEditingTitle(false)
  }, [currentProjectId, result])

  // 追加校本
  const handleAddCollations = useCallback(async () => {
    if (!currentProjectId || newCollationFiles.length === 0) return
    setAddingCollations(true)
    try {
      const formData = new FormData()
      newCollationFiles.forEach((file) => {
        formData.append('collation_files', file.originFileObj as File)
      })

      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${currentProjectId}/add-collations`,
        { method: 'POST', body: formData }
      )

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '追加失败')
      }

      const data = await response.json()

      // 更新结果
      setResult({
        success: true,
        mode: 'multi_collation',
        mode_description: '一底多校模式',
        processing_time: data.processing_time,
        base: data.base,
        collations: data.collations,
        summary: data.summary,
        variant_table: data.variant_table,
        phylogeny: data.phylogeny,
        project: data.project,
      })

      setNewCollationFiles([])
      setAddCollationModalOpen(false)
      message.success(`成功追加 ${data.new_collations.length} 个校本`)
    } catch (error: any) {
      message.error(error.message || '追加校本失败')
    } finally {
      setAddingCollations(false)
    }
  }, [currentProjectId, newCollationFiles])

  // 去除校本
  const handleRemoveCollations = useCallback(async () => {
    if (!currentProjectId || collationsToRemove.length === 0) return
    setRemovingCollations(true)
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${currentProjectId}/remove-collations`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ indices: collationsToRemove }),
        }
      )

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '移除失败')
      }

      const data = await response.json()

      setResult({
        success: true,
        mode: 'multi_collation',
        mode_description: '一底多校模式',
        processing_time: data.processing_time,
        base: data.base,
        collations: data.collations,
        summary: data.summary,
        variant_table: data.variant_table,
        phylogeny: data.phylogeny,
        project: data.project,
      })

      setCollationsToRemove([])
      setRemoveCollationModalOpen(false)

      const removedNames = Array.isArray(data.removed_collations) ? data.removed_collations.join('、') : ''
      if (data.removed_decisions && data.removed_decisions > 0) {
        message.success(`已移除校本：${removedNames}；并清理 ${data.removed_decisions} 条判取结果`)
      } else {
        message.success(`已移除校本：${removedNames}`)
      }
    } catch (error: any) {
      message.error(error.message || '去除校本失败')
    } finally {
      setRemovingCollations(false)
    }
  }, [API_BASE, collationsToRemove, currentProjectId])

  // 新建项目（清空当前状态）
  const createNewProject = useCallback(() => {
    setResult(null)
    setCurrentProjectId(null)
    setCurrentProjectTitle('')
    setBaseFile(null)
    setCollationFiles([])
    setActiveTab('summary')
    setProjectDrawerOpen(false)
  }, [])

  // 渲染三层表头单元格
  const renderVersionHeader = (fullName: string, isBase: boolean = false) => {
    const info = parseVersionInfo(fullName)
    return (
      <Tooltip title={fullName}>
        <div style={{ textAlign: 'center', lineHeight: 1.3 }}>
          <div style={{
            fontSize: 11,
            color: SYSTEM_COLORS[info.system] || '#8c8c8c',
            fontWeight: 500,
          }}>
            {info.system}
          </div>
          <div style={{
            fontSize: 13,
            fontWeight: 'bold',
            color: isBase ? '#1890ff' : '#333',
          }}>
            {info.canon}
          </div>
          {info.sutra && (
            <div style={{ fontSize: 10, color: '#999' }}>
              {info.sutra}
            </div>
          )}
        </div>
      </Tooltip>
    )
  }

  // ==================== 导出功能 ====================

  // 导出汇总统计 CSV
  const exportSummaryCSV = useCallback(() => {
    if (!result) return

    const BOM = '\uFEFF'
    const rows: string[] = []
    const { summary, base, collations, processing_time } = result

    // 标题
    rows.push('==================== 版本对勘汇总报告 ====================')
    rows.push('')

    // 基本信息
    rows.push('"项目","数值"')
    rows.push(`"底本","${base.name}"`)
    rows.push(`"底本字数","${base.char_count}"`)
    rows.push(`"校本数量","${collations.length}"`)
    rows.push(`"处理耗时","${processing_time}秒"`)
    rows.push('')

    // 各校本差异统计表
    rows.push('==================== 各校本差异统计 ====================')
    rows.push('')

    const order = getCollationDisplayOrder(summary.collation_names)

    // 表头
    const headers = ['版本信息', ...order.map(i => parseVersionInfo(summary.collation_names[i]).canon), '合计']
    rows.push(headers.map(h => `"${h}"`).join(','))

    // 数据行
    summary.stats_table.rows.forEach(row => {
      const rowData = [row.type, ...order.map(i => String(row.values[i])), String(row.total)]
      rows.push(rowData.map(d => `"${d}"`).join(','))
    })

    // 下载
    const csvContent = BOM + rows.join('\n')
    downloadFile(csvContent, `版本对勘_汇总统计_${formatDate()}.csv`, 'text/csv;charset=utf-8;')
    message.success('汇总统计已导出')
  }, [result])

  // 导出异文汇校表 CSV
  const exportVariantTableCSV = useCallback(() => {
    if (!result?.variant_table) {
      message.warning('暂无异文汇校表数据')
      return
    }

    const BOM = '\uFEFF'
    const rows: string[] = []
    const { variant_table, base, summary } = result

    // 标题
    rows.push('==================== 异文汇校表 ====================')
    rows.push('')
    rows.push(`"底本","${base.name}"`)
    rows.push(`"异文总数","${variant_table.total}"`)
    rows.push('')

    const order = getCollationDisplayOrder(summary.collation_names)

    // 表头
    const headers = ['序号', '上下文', base.name, ...order.map(i => summary.collation_names[i]), '类型']
    rows.push(headers.map(h => `"${h}"`).join(','))

    // 数据行
    variant_table.rows.forEach((row, idx) => {
      const rowData = [
        String(idx + 1),
        row.context,
        row.base_char,
        ...order.map(i => row.coll_values[i]),
        row.category
      ]
      rows.push(rowData.map(d => `"${d}"`).join(','))
    })

    // 下载
    const csvContent = BOM + rows.join('\n')
    downloadFile(csvContent, `版本对勘_异文汇校表_${formatDate()}.csv`, 'text/csv;charset=utf-8;')
    message.success('异文汇校表已导出')
  }, [result])

  // 导出综合报告 CSV（包含所有数据）
  const exportFullReportCSV = useCallback(() => {
    if (!result) return

    const BOM = '\uFEFF'
    const rows: string[] = []
    const { summary, base, collations, processing_time, variant_table } = result

    // ===== 第一部分：基本信息 =====
    rows.push('##################################################')
    rows.push('# 版本对勘综合报告')
    rows.push('##################################################')
    rows.push('')
    rows.push('"项目","数值"')
    rows.push(`"底本","${base.name}"`)
    rows.push(`"底本字数","${base.char_count}"`)
    rows.push(`"校本数量","${collations.length}"`)
    rows.push(`"处理耗时","${processing_time}秒"`)
    rows.push(`"导出时间","${new Date().toLocaleString('zh-CN')}"`)
    rows.push('')

    // ===== 第二部分：各校本差异统计 =====
    rows.push('##################################################')
    rows.push('# 各校本差异统计')
    rows.push('##################################################')
    rows.push('')

    const order = getCollationDisplayOrder(summary.collation_names)
    const headers2 = ['版本信息', ...order.map(i => parseVersionInfo(summary.collation_names[i]).canon), '合计']
    rows.push(headers2.map(h => `"${h}"`).join(','))

    summary.stats_table.rows.forEach(row => {
      const rowData = [row.type, ...order.map(i => String(row.values[i])), String(row.total)]
      rows.push(rowData.map(d => `"${d}"`).join(','))
    })
    rows.push('')

    // ===== 第三部分：异文汇校表 =====
    if (variant_table && variant_table.rows.length > 0) {
      rows.push('##################################################')
      rows.push('# 异文汇校表')
      rows.push('##################################################')
      rows.push('')
      rows.push(`"异文总数","${variant_table.total}"`)
      rows.push('')

      const vtHeaders = ['序号', '上下文', base.name, ...order.map(i => summary.collation_names[i]), '类型']
      rows.push(vtHeaders.map(h => `"${h}"`).join(','))

      variant_table.rows.forEach((row, idx) => {
        const rowData = [
          String(idx + 1),
          row.context,
          row.base_char,
          ...order.map(i => row.coll_values[i]),
          row.category
        ]
        rows.push(rowData.map(d => `"${d}"`).join(','))
      })
      rows.push('')
    }

    // ===== 第四部分：各校本详细统计 =====
    rows.push('##################################################')
    rows.push('# 各校本详细统计')
    rows.push('##################################################')
    rows.push('')

    collations.forEach((coll, idx) => {
      const stats = coll.result.statistics
      rows.push(`"校本 ${idx + 1}","${coll.collation_name}"`)
      rows.push(`"字数","${coll.char_count}"`)
      rows.push(`"相似度","${(coll.result.similarity * 100).toFixed(1)}%"`)

      if (stats.category_stats) {
        rows.push(`"异体字","${stats.category_stats.variant_chars}"`)
        rows.push(`"讹误","${stats.category_stats.error_chars}"`)
        rows.push(`"衍文","${stats.category_stats.yanwen_chars}"`)
        rows.push(`"脱文","${stats.category_stats.tuowen_chars}"`)
      }
      rows.push('')
    })

    // 下载
    const csvContent = BOM + rows.join('\n')
    downloadFile(csvContent, `版本对勘_综合报告_${formatDate()}.csv`, 'text/csv;charset=utf-8;')
    message.success('综合报告已导出')
  }, [result])

  // 导出全量对照表 CSV（包含所有字符位置，无论是否有异文）
  const exportFullAlignmentTableCSV = useCallback(() => {
    if (!result?.collations || result.collations.length === 0) {
      message.warning('暂无校勘数据')
      return
    }

    const BOM = '\uFEFF'
    const rows: string[] = []
    const { base, collations, summary } = result

    // 标题
    rows.push('==================== 全量对照表 ====================')
    rows.push('')
    rows.push(`"底本","${base.name}"`)
    rows.push(`"底本字数","${base.char_count}"`)
    rows.push(`"校本数量","${collations.length}"`)
    rows.push('')

    const order = getCollationDisplayOrder(summary.collation_names)

    // 表头：序号 | 上下文 | 底本 | 校本1 | 校本2 | ... | 类型
    const headers = ['序号', '上下文', base.name, ...order.map(i => summary.collation_names[i]), '类型']
    rows.push(headers.map(h => `"${h}"`).join(','))

    // 辅助函数：生成上下文（前3字 + 【当前字】 + 后3字）
    const getContext = (text: string, pos: number, contextLen: number = 3): string => {
      const before = text.slice(Math.max(0, pos - contextLen), pos)
      const current = text[pos] || ''
      const after = text.slice(pos + 1, pos + 1 + contextLen)
      return `${before}【${current}】${after}`
    }

    // 从第一个校本的 segments 重建规范化后的底本文本（移除了换行符等）
    const firstColl = collations[order[0]]
    if (!firstColl?.result?.side_by_side?.segments) {
      message.warning('暂无对齐数据')
      return
    }

    // 重建规范化后的底本文本
    let normalizedBaseText = ''
    for (const seg of firstColl.result.side_by_side.segments) {
      normalizedBaseText += seg.text1 || ''
    }

    // 构建每个校本的字符映射（底本位置 -> 校本字符）
    const collationMaps: Map<number, { char: string; category: string }>[] = order.map(orderIdx => {
      const coll = collations[orderIdx]
      const charMap = new Map<number, { char: string; category: string }>()

      if (!coll?.result?.side_by_side?.segments) {
        // 没有对齐数据，假设与底本相同
        for (let i = 0; i < normalizedBaseText.length; i++) {
          charMap.set(i, { char: normalizedBaseText[i], category: '相同' })
        }
        return charMap
      }

      const segments = coll.result.side_by_side.segments
      let basePos = 0

      for (const seg of segments) {
        const text1 = seg.text1 || ''
        const text2 = seg.text2 || ''
        const segType = seg.type

        if (segType === 'equal') {
          // 相同部分：校本字符与底本相同
          for (let i = 0; i < text1.length; i++) {
            charMap.set(basePos, { char: text2[i] || text1[i], category: '相同' })
            basePos++
          }
        } else if (segType === 'delete') {
          // 脱文：底本有，校本无
          for (let i = 0; i < text1.length; i++) {
            charMap.set(basePos, { char: '□', category: '脱文' })
            basePos++
          }
        } else if (segType === 'insert') {
          // 衍文：底本无，校本有 - 不对应底本位置，跳过
        } else if (segType === 'replace') {
          // 替换
          const len1 = text1.length
          const len2 = text2.length

          for (let i = 0; i < len1; i++) {
            if (i < len2) {
              charMap.set(basePos, { char: text2[i], category: '异文' })
            } else {
              charMap.set(basePos, { char: '□', category: '脱文' })
            }
            basePos++
          }
        }
      }

      return charMap
    })

    // 遍历规范化后的底本文本，构建全量对照数据
    for (let pos = 0; pos < normalizedBaseText.length; pos++) {
      const baseChar = normalizedBaseText[pos]
      const collValues: string[] = []
      let category = '相同'

      for (let i = 0; i < order.length; i++) {
        const charInfo = collationMaps[i].get(pos)
        if (charInfo) {
          collValues.push(charInfo.char)
          if (charInfo.category !== '相同') {
            category = charInfo.category
          }
        } else {
          collValues.push(baseChar)
        }
      }

      // 检查是否所有校本都与底本相同
      const allSame = collValues.every(v => v === baseChar)
      if (allSame) {
        category = '相同'
      }

      // 生成上下文（使用规范化后的底本文本）
      const context = getContext(normalizedBaseText, pos)

      const rowData = [
        String(pos + 1),
        context,
        baseChar,
        ...collValues,
        category
      ]
      rows.push(rowData.map(d => `"${d}"`).join(','))
    }

    // 统计信息
    rows.push('')
    rows.push('==================== 统计 ====================')
    // 重新计算统计
    let sameCount = 0
    let diffCount = 0
    for (let pos = 0; pos < normalizedBaseText.length; pos++) {
      const baseChar = normalizedBaseText[pos]
      let hasDiff = false
      for (let i = 0; i < order.length; i++) {
        const charInfo = collationMaps[i].get(pos)
        if (charInfo && charInfo.char !== baseChar) {
          hasDiff = true
          break
        }
      }
      if (hasDiff) {
        diffCount++
      } else {
        sameCount++
      }
    }
    rows.push(`"相同字数","${sameCount}"`)
    rows.push(`"异文字数","${diffCount}"`)
    rows.push(`"总字数","${normalizedBaseText.length}"`)

    // 下载
    const csvContent = BOM + rows.join('\n')
    downloadFile(csvContent, `版本对勘_全量对照表_${formatDate()}.csv`, 'text/csv;charset=utf-8;')
    message.success('全量对照表已导出')
  }, [result])

  // 导出版本谱系报告 CSV
  const exportPhylogenyReportCSV = useCallback(() => {
    if (!result?.phylogeny) {
      message.warning('暂无版本谱系数据')
      return
    }

    const BOM = '\uFEFF'
    const rows: string[] = []
    const { phylogeny, base } = result
    const { similarity_matrix, shared_errors, conclusions } = phylogeny

    // ===== 第一部分：报告标题与基本信息 =====
    rows.push('##################################################')
    rows.push('# 版本谱系分析报告')
    rows.push('##################################################')
    rows.push('')
    rows.push('"项目","数值"')
    rows.push(`"底本","${base.name}"`)
    rows.push(`"版本数量","${similarity_matrix.names.length}"`)
    rows.push(`"导出时间","${new Date().toLocaleString('zh-CN')}"`)
    rows.push('')

    // ===== 第二部分：版本谱系分析结论 =====
    if (conclusions && conclusions.length > 0) {
      rows.push('##################################################')
      rows.push('# 版本谱系分析结论')
      rows.push('##################################################')
      rows.push('')
      conclusions.forEach((conclusion, idx) => {
        rows.push(`"结论${idx + 1}","${conclusion.replace(/"/g, '""')}"`)
      })
      rows.push('')
    }

    // ===== 第三部分：版本系统分类 =====
    if (similarity_matrix.systems && Object.keys(similarity_matrix.systems).length > 0) {
      rows.push('##################################################')
      rows.push('# 版本系统分类')
      rows.push('##################################################')
      rows.push('')
      rows.push('"版本名称","所属系统"')

      // 按系统分组统计
      const systemGroups: Record<string, string[]> = {}
      Object.entries(similarity_matrix.systems).forEach(([name, system]) => {
        if (!systemGroups[system]) {
          systemGroups[system] = []
        }
        systemGroups[system].push(name)
      })

      // 输出每个版本的系统归属
      similarity_matrix.names.forEach(name => {
        const system = similarity_matrix.systems?.[name] || '未知'
        rows.push(`"${name.replace(/"/g, '""')}","${system}"`)
      })
      rows.push('')

      // 输出系统汇总
      rows.push('"系统汇总",""')
      Object.entries(systemGroups).forEach(([system, names]) => {
        rows.push(`"${system}","${names.length}个版本"`)
      })
      rows.push('')
    }

    // ===== 第四部分：相似度矩阵 =====
    rows.push('##################################################')
    rows.push('# 相似度矩阵')
    rows.push('##################################################')
    rows.push('')

    // 矩阵表头
    const matrixHeaders = ['版本', ...similarity_matrix.names.map(n => {
      // 简化版本名称用于表头
      const info = parseVersionInfo(n)
      return info.canon || n.slice(0, 10)
    })]
    rows.push(matrixHeaders.map(h => `"${h.replace(/"/g, '""')}"`).join(','))

    // 矩阵数据行
    similarity_matrix.matrix.forEach((row, i) => {
      const rowName = similarity_matrix.names[i]
      const info = parseVersionInfo(rowName)
      const shortName = info.canon || rowName.slice(0, 10)
      const rowData = [shortName, ...row.map(v => `${(v * 100).toFixed(1)}%`)]
      rows.push(rowData.map(d => `"${d}"`).join(','))
    })
    rows.push('')

    // 找出最相似的版本对（排除自身对比）
    rows.push('"相似度排名（前10对）",""')
    rows.push('"版本对","相似度"')

    const similarityPairs: Array<{ name1: string; name2: string; similarity: number }> = []
    for (let i = 0; i < similarity_matrix.names.length; i++) {
      for (let j = i + 1; j < similarity_matrix.names.length; j++) {
        similarityPairs.push({
          name1: similarity_matrix.names[i],
          name2: similarity_matrix.names[j],
          similarity: similarity_matrix.matrix[i][j],
        })
      }
    }
    similarityPairs.sort((a, b) => b.similarity - a.similarity)

    similarityPairs.slice(0, 10).forEach(pair => {
      const info1 = parseVersionInfo(pair.name1)
      const info2 = parseVersionInfo(pair.name2)
      const name1 = info1.canon || pair.name1.slice(0, 15)
      const name2 = info2.canon || pair.name2.slice(0, 15)
      rows.push(`"${name1} ↔ ${name2}","${(pair.similarity * 100).toFixed(2)}%"`)
    })
    rows.push('')

    // ===== 第五部分：共同异文统计 =====
    if (shared_errors) {
      rows.push('##################################################')
      rows.push('# 共同异文统计')
      rows.push('##################################################')
      rows.push('')

      // 共同异文矩阵（讹误）
      if (shared_errors.matrix) {
        rows.push('"【讹误】共同异文矩阵",""')
        const errorHeaders = ['版本', ...shared_errors.names.map(n => {
          const info = parseVersionInfo(n)
          return info.canon || n.slice(0, 10)
        })]
        rows.push(errorHeaders.map(h => `"${h.replace(/"/g, '""')}"`).join(','))

        shared_errors.matrix.forEach((row, i) => {
          const rowName = shared_errors.names[i]
          const info = parseVersionInfo(rowName)
          const shortName = info.canon || rowName.slice(0, 10)
          const rowData = [shortName, ...row.map(v => String(v))]
          rows.push(rowData.map(d => `"${d}"`).join(','))
        })
        rows.push('')
      }

      // 共同异文矩阵（异体字）
      if (shared_errors.variant_matrix) {
        rows.push('"【异体字】共同异文矩阵",""')
        const variantHeaders = ['版本', ...shared_errors.names.map(n => {
          const info = parseVersionInfo(n)
          return info.canon || n.slice(0, 10)
        })]
        rows.push(variantHeaders.map(h => `"${h.replace(/"/g, '""')}"`).join(','))

        shared_errors.variant_matrix.forEach((row, i) => {
          const rowName = shared_errors.names[i]
          const info = parseVersionInfo(rowName)
          const shortName = info.canon || rowName.slice(0, 10)
          const rowData = [shortName, ...row.map(v => String(v))]
          rows.push(rowData.map(d => `"${d}"`).join(','))
        })
        rows.push('')
      }

      // 共同异文矩阵（衍脱）
      if (shared_errors.yantuo_matrix) {
        rows.push('"【衍脱】共同异文矩阵",""')
        const yantuoHeaders = ['版本', ...shared_errors.names.map(n => {
          const info = parseVersionInfo(n)
          return info.canon || n.slice(0, 10)
        })]
        rows.push(yantuoHeaders.map(h => `"${h.replace(/"/g, '""')}"`).join(','))

        shared_errors.yantuo_matrix.forEach((row, i) => {
          const rowName = shared_errors.names[i]
          const info = parseVersionInfo(rowName)
          const shortName = info.canon || rowName.slice(0, 10)
          const rowData = [shortName, ...row.map(v => String(v))]
          rows.push(rowData.map(d => `"${d}"`).join(','))
        })
        rows.push('')
      }

      // 各版本共同异文总数
      rows.push('"各版本共同异文总数",""')
      rows.push('"版本","讹误","异体字","衍脱"')

      shared_errors.names.forEach(name => {
        const info = parseVersionInfo(name)
        const shortName = info.canon || name.slice(0, 15)
        const errorCount = shared_errors.total_by_version?.[name] || 0
        const variantCount = shared_errors.variant_total_by_version?.[name] || 0
        const yantuoCount = shared_errors.yantuo_total_by_version?.[name] || 0
        rows.push(`"${shortName.replace(/"/g, '""')}","${errorCount}","${variantCount}","${yantuoCount}"`)
      })
      rows.push('')

      // 共同异文详情（讹误）
      if (shared_errors.details && Object.keys(shared_errors.details).length > 0) {
        rows.push('"【讹误】共同异文详情",""')
        rows.push('"版本对","位置","底本字","共同异文字"')

        Object.entries(shared_errors.details).forEach(([pairKey, details]) => {
          const [name1, name2] = pairKey.split('|')
          const info1 = parseVersionInfo(name1 || '')
          const info2 = parseVersionInfo(name2 || '')
          const shortPair = `${info1.canon || name1?.slice(0, 10)} ↔ ${info2.canon || name2?.slice(0, 10)}`

          details.forEach(detail => {
            const sharedChar = detail.shared_error_char || detail.shared_char || ''
            rows.push(`"${shortPair}","${detail.position}","${detail.base_char}","${sharedChar}"`)
          })
        })
        rows.push('')
      }

      // 共同异文详情（异体字）
      if (shared_errors.variant_details && Object.keys(shared_errors.variant_details).length > 0) {
        rows.push('"【异体字】共同异文详情",""')
        rows.push('"版本对","位置","底本字","共同异文字"')

        Object.entries(shared_errors.variant_details).forEach(([pairKey, details]) => {
          const [name1, name2] = pairKey.split('|')
          const info1 = parseVersionInfo(name1 || '')
          const info2 = parseVersionInfo(name2 || '')
          const shortPair = `${info1.canon || name1?.slice(0, 10)} ↔ ${info2.canon || name2?.slice(0, 10)}`

          details.forEach(detail => {
            const sharedChar = detail.shared_error_char || detail.shared_char || ''
            rows.push(`"${shortPair}","${detail.position}","${detail.base_char}","${sharedChar}"`)
          })
        })
        rows.push('')
      }

      // 共同异文详情（衍脱）
      if (shared_errors.yantuo_details && Object.keys(shared_errors.yantuo_details).length > 0) {
        rows.push('"【衍脱】共同异文详情",""')
        rows.push('"版本对","位置","底本字","共同异文字","类型"')

        Object.entries(shared_errors.yantuo_details).forEach(([pairKey, details]) => {
          const [name1, name2] = pairKey.split('|')
          const info1 = parseVersionInfo(name1 || '')
          const info2 = parseVersionInfo(name2 || '')
          const shortPair = `${info1.canon || name1?.slice(0, 10)} ↔ ${info2.canon || name2?.slice(0, 10)}`

          details.forEach(detail => {
            const sharedChar = detail.shared_error_char || detail.shared_char || ''
            const category = detail.category || ''
            rows.push(`"${shortPair}","${detail.position}","${detail.base_char}","${sharedChar}","${category}"`)
          })
        })
        rows.push('')
      }
    }

    // 下载
    const csvContent = BOM + rows.join('\n')
    downloadFile(csvContent, `版本谱系报告_${formatDate()}.csv`, 'text/csv;charset=utf-8;')
    message.success('版本谱系报告已导出')
  }, [result])

  // 辅助函数：下载文件
  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // 辅助函数：格式化日期
  const formatDate = () => {
    return new Date().toISOString().slice(0, 10)
  }

  // 导出菜单项
  const exportMenuItems = [
    {
      key: 'summary',
      label: '汇总统计',
      icon: <BarChartOutlined />,
      onClick: exportSummaryCSV,
    },
    {
      key: 'variant',
      label: '异文汇校表',
      icon: <TableOutlined />,
      onClick: exportVariantTableCSV,
    },
    {
      key: 'fullAlignment',
      label: '全量对照表',
      icon: <OrderedListOutlined />,
      onClick: exportFullAlignmentTableCSV,
    },
    {
      key: 'phylogeny',
      label: '版本谱系报告',
      icon: <ApartmentOutlined />,
      onClick: exportPhylogenyReportCSV,
      disabled: !result?.phylogeny,
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'full',
      label: '综合报告（全部）',
      icon: <FileTextOutlined />,
      onClick: exportFullReportCSV,
    },
  ]

  // 处理底本文件上传
  const handleBaseFileChange = (info: any) => {
    const file = info.fileList[0]
    setBaseFile(file || null)
  }

  // 处理校本文件上传
  const handleCollationFilesChange = (info: any) => {
    const files = info.fileList.slice(0, MAX_COLLATION_FILES)
    setCollationFiles(files)
  }

  // 提交对比
  const handleSubmit = async () => {
    if (!baseFile) {
      message.warning('请上传底本文件')
      return
    }
    if (collationFiles.length === 0) {
      message.warning('请至少上传一个校本文件')
      return
    }

    setLoading(true)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('base_file', baseFile.originFileObj as File)
      collationFiles.forEach((file) => {
        formData.append('collation_files', file.originFileObj as File)
      })
      // 自动保存
      formData.append('auto_save', 'true')

      const response = await fetch(`${API_BASE}/api/v1/multi-collation/compare`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '对比失败')
      }

      const data: MultiCollationResponse = await response.json()
      setResult(data)
      setActiveTab('summary')

      // 更新项目状态
      if (data.project) {
        setCurrentProjectId(data.project.id)
        setCurrentProjectTitle(data.project.title)
        message.success(`对比完成，项目已保存 (${data.project.id})`)
      } else {
        message.success(`对比完成，耗时 ${data.processing_time} 秒`)
      }
    } catch (error: any) {
      message.error(error.message || '对比失败')
    } finally {
      setLoading(false)
    }
  }

  // 渲染汇总统计表格
  const renderSummaryTable = () => {
    if (!result) return null
    const { summary } = result

    const columns = [
      {
        title: '版本信息',
        dataIndex: 'type',
        key: 'type',
        fixed: 'left' as const,
        width: 100,
        render: (text: string, record: any) => {
          const colorMap: Record<string, string> = {
            variant: 'green',
            error: 'red',
            yanwen: 'orange',
            tuowen: 'purple',
            total: 'blue',
          }
          const isTotal = record.type_key === 'total'
          return (
            <Tag color={colorMap[record.type_key]} style={isTotal ? { fontWeight: 'bold' } : {}}>
              {text}
            </Tag>
          )
        },
      },
      ...collationDisplayOrder.map((origIdx) => ({
        title: renderVersionHeader(summary.collation_names[origIdx]),
        dataIndex: `col_${origIdx}`,
        key: `col_${origIdx}`,
        align: 'center' as const,
        render: (_: any, record: any) => record.values[origIdx],
      })),
      {
        title: '合计',
        dataIndex: 'total',
        key: 'total',
        align: 'center' as const,
        render: (total: number) => <strong>{total}</strong>,
      },
    ]

    const dataSource = summary.stats_table.rows.map((row, idx) => ({
      key: idx,
      ...row,
    }))

    // 计算总数行
    const totalRow = {
      key: 'total',
      type: '总数',
      type_key: 'total',
      values: summary.collation_names.map((_, colIdx) =>
        summary.stats_table.rows.reduce((sum, row) => sum + (row.values[colIdx] || 0), 0)
      ),
      total: summary.stats_table.rows.reduce((sum, row) => sum + (row.total || 0), 0),
    }

    return (
      <Table
        columns={columns}
        dataSource={[...dataSource, totalRow]}
        pagination={false}
        bordered
        size="middle"
        rowClassName={(record) => record.key === 'total' ? 'total-row' : ''}
      />
    )
  }

  // 渲染异文汇校表
  const renderVariantTable = () => {
    if (!result?.variant_table) return <Alert type="info" message="暂无异文汇校表数据" />

    const { variant_table, summary } = result

    // 注意：后端对衍文（insert）逐字记录时，可能出现同一 position 对应多条记录。
    // 若直接用 position 作为 Table rowKey，会导致渲染/筛选错乱（React key 冲突）。
    const rowsWithKey = (() => {
      const insertCounters: Record<number, number> = {}
      return variant_table.rows.map((row) => {
        if (row.category === '衍文') {
          const idx = insertCounters[row.position] ?? 0
          insertCounters[row.position] = idx + 1
          return { ...row, _rowKey: `ins_${row.position}_${idx}` }
        }
        return { ...row, _rowKey: String(row.position) }
      })
    })()

    const filteredRows = categoryFilter === 'all'
      ? rowsWithKey
      : rowsWithKey.filter(row => row.category === categoryFilter)

    // 点击查看按钮，跳转到对应校本详细对比
    const handleViewClick = (record: VariantTableRow, collationIdx: number) => {
      // 设置高亮定位信息
      setInitialHighlight({
        char: record.base_char !== '∅' ? record.base_char : record.coll_values[collationIdx],
        collationIdx: collationIdx
      })
      // 切换到对应校本标签页
      setActiveTab(`collation_${collationIdx}`)
      message.info(`已跳转到「${summary.collation_names[collationIdx]}」并定位到差异位置`)
    }

    // 获取该记录中有差异的校本索引列表
    const getDiffCollationIndices = (record: VariantTableRow): number[] => {
      const indices: number[] = []
      record.coll_values.forEach((val, idx) => {
        if (val !== record.base_char) {
          indices.push(idx)
        }
      })
      return indices
    }

    const columns = [
      {
        title: '序号',
        dataIndex: 'index',
        key: 'index',
        width: 60,
        fixed: 'left' as const,
        align: 'center' as const,
        render: (_: any, __: any, index: number) => index + 1,
      },
      {
        title: '上下文',
        dataIndex: 'context',
        key: 'context',
        width: 200,
        fixed: 'left' as const,
        align: 'center' as const,
        render: (text: string) => (
          <span style={{ fontFamily: "'Noto Serif SC', serif", fontSize: 13 }}>{text}</span>
        ),
      },
      {
        title: renderVersionHeader(result.base.name, true),
        dataIndex: 'base_char',
        key: 'base_char',
        width: 90,
        fixed: 'left' as const,
        align: 'center' as const,
        render: (text: string) => (
          <span style={{
            fontFamily: "'Noto Serif SC', serif",
            fontSize: 16,
            fontWeight: 'bold',
            color: '#1890ff'
          }}>{text}</span>
        ),
      },
      ...collationDisplayOrder.map((origIdx) => ({
        title: renderVersionHeader(summary.collation_names[origIdx]),
        key: `coll_${origIdx}`,
        width: 90,
        align: 'center' as const,
        render: (_: any, record: VariantTableRow) => {
          const val = record.coll_values[origIdx]
          const isDiff = val !== record.base_char
          return (
            <span style={{
              fontFamily: "'Noto Serif SC', serif",
              fontSize: 16,
              fontWeight: isDiff ? 'bold' : 'normal',
              color: isDiff ? '#f5222d' : '#999',
              background: isDiff ? '#fff1f0' : 'transparent',
              padding: isDiff ? '2px 6px' : 0,
              borderRadius: 4,
            }}>{val}</span>
          )
        },
      })),
      {
        title: '类型',
        dataIndex: 'category',
        key: 'category',
        width: 70,
        fixed: 'right' as const,
        align: 'center' as const,
        render: (cat: string) => {
          const colorMap: Record<string, string> = {
            '异体字': 'green',
            '讹误': 'red',
            '衍文': 'orange',
            '脱文': 'purple',
          }
          return <Tag color={colorMap[cat] || 'default'}>{cat}</Tag>
        },
      },
      {
        title: '操作',
        key: 'action',
        width: 70,
        fixed: 'right' as const,
        align: 'center' as const,
        render: (_: any, record: VariantTableRow) => {
          const diffIndices = getDiffCollationIndices(record)

          // 如果没有差异，不显示按钮
          if (diffIndices.length === 0) {
            return <span style={{ color: '#999' }}>-</span>
          }

          // 统一按钮样式：固定宽度，文字左对齐，箭头绝对定位
          const buttonStyle: React.CSSProperties = {
            width: 60,
            position: 'relative',
            textAlign: 'left',
            paddingLeft: 12,
            paddingRight: 16,
          }

          // 如果只有一个校本有差异，直接显示按钮
          if (diffIndices.length === 1) {
            return (
              <Button
                type="link"
                size="small"
                style={buttonStyle}
                onClick={() => handleViewClick(record, diffIndices[0])}
              >
                查看
              </Button>
            )
          }

          // 多个校本有差异，显示下拉菜单
          const menuItems = diffIndices
            .slice()
            .sort((a, b) => (collationDisplayRank[a] ?? 0) - (collationDisplayRank[b] ?? 0))
            .map(idx => ({
              key: idx.toString(),
              label: summary.collation_names[idx],
              onClick: () => handleViewClick(record, idx)
            }))

          return (
            <Dropdown menu={{ items: menuItems }} trigger={['click']}>
              <Button type="link" size="small" style={buttonStyle}>
                查看
                <DownOutlined style={{
                  fontSize: 10,
                  position: 'absolute',
                  right: 4,
                  top: '50%',
                  transform: 'translateY(-50%)',
                }} />
              </Button>
            </Dropdown>
          )
        },
      },
      {
        title: '判取',
        key: 'decision',
        width: 80,
        fixed: 'right' as const,
        align: 'center' as const,
        render: (_: any, record: VariantTableRow) => {
          const decision = decisions[record.position]
          if (!decision) {
            return (
              <Button
                type="link"
                size="small"
                onClick={() => openDecisionModalForPosition(record.position)}
              >
                判取
              </Button>
            )
          }
          if (decision.uncertain) {
            return (
              <Tooltip title={`存疑：${decision.selectedText}`}>
                <QuestionCircleOutlined
                  style={{ color: '#faad14', fontSize: 16, cursor: 'pointer' }}
                  onClick={() => openDecisionModalForPosition(record.position)}
                />
              </Tooltip>
            )
          }
          return (
            <Tooltip title={`已判取：${decision.selectedText}`}>
              <CheckCircleOutlined
                style={{ color: '#52c41a', fontSize: 16, cursor: 'pointer' }}
                onClick={() => openDecisionModalForPosition(record.position)}
              />
            </Tooltip>
          )
        },
      },
    ]

    // 计算判取统计
    const totalVariants = variant_table.rows.length
    const decidedCount = variant_table.rows.filter(row => decisions[row.position]).length
    const uncertainCount = variant_table.rows.filter(row => decisions[row.position]?.uncertain).length

    return (
      <div>
        <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <span>类型筛选：</span>
          <Select
            value={categoryFilter}
            onChange={(v) => {
              setCategoryFilter(v)
              setVariantTablePage(1)
            }}
            style={{ width: 120 }}
            options={[
              { value: 'all', label: '全部' },
              { value: '异体字', label: '异体字' },
              { value: '讹误', label: '讹误' },
              { value: '脱文', label: '脱文' },
              { value: '衍文', label: '衍文' },
            ]}
          />
          <span style={{ color: '#999' }}>
            共 {filteredRows.length} 条记录
            {categoryFilter !== 'all' && ` (总计 ${variant_table.total} 条)`}
          </span>
          <Divider type="vertical" style={{ height: 20 }} />
          <Space size="small">
            <span>判取进度：</span>
            <Tag color="green">{decidedCount - uncertainCount} 已判取</Tag>
            {uncertainCount > 0 && <Tag color="orange">{uncertainCount} 存疑</Tag>}
            <Tag color="default">{totalVariants - decidedCount} 待判取</Tag>
            <span style={{ color: '#1890ff', fontWeight: 500 }}>
              {((decidedCount / totalVariants) * 100).toFixed(0)}%
            </span>
          </Space>
        </div>
        <Table
          columns={columns}
          dataSource={filteredRows}
          rowKey={(row) => (row as VariantTableRow & { _rowKey: string })._rowKey}
          rowClassName={(record) =>
            record.position === highlightedPosition ? 'variant-row-highlight' : ''
          }
          pagination={{
            current: variantTablePage,
            pageSize: variantTablePageSize,
            showSizeChanger: true,
            showQuickJumper: true,
            onChange: (page, pageSize) => {
              setVariantTablePage(page)
              if (pageSize !== variantTablePageSize) {
                setVariantTablePageSize(pageSize)
                setVariantTablePage(1)
              }
            },
          }}
          bordered
          size="small"
          scroll={{ x: 330 + summary.collation_names.length * 70 + 220, y: 600 }}
          sticky
        />
      </div>
    )
  }

  // 渲染版本谱系（使用专业组件）
  const renderPhylogeny = () => {
    if (!result?.phylogeny) return <Alert type="info" message="暂无版本谱系数据" />

    return (
      <PhylogenyAnalysis
        data={result.phylogeny}
        baseName={result.base.name}
        projectId={currentProjectId}
      />
    )
  }

  // 渲染工具栏
  const renderToolbar = () => {
    if (!result) return null

    // 构建版本选项（按版本系统排序展示，但 value 仍为原始索引）
    const orderedIndices = collationDisplayOrder.length
      ? collationDisplayOrder
      : result.collations.map((_, idx) => idx)

    const versionOptions = orderedIndices
      .map((idx) => {
        const coll = result.collations[idx]
        return {
          value: idx,
          label: getShortName(coll?.collation_name || ''),
          fullName: coll?.collation_name || '',
        }
      })
      .filter((o) => o.fullName)

    return (
      <div style={{
        padding: '12px 16px',
        background: '#fafafa',
        borderRadius: 6,
        marginBottom: 16,
        border: '1px solid #e8e8e8',
      }}>
        <Space split={<Divider type="vertical" style={{ height: 28, margin: '0 12px' }} />} wrap>
          {/* 功能操作区 */}
          <Space size="small">
            <Button
              type={activeTab === 'summary' ? 'primary' : 'default'}
              icon={<BarChartOutlined />}
              onClick={() => setActiveTab('summary')}
            >
              汇总统计
            </Button>
            <Button
              type={activeTab === 'variant_table' ? 'primary' : 'default'}
              icon={<TableOutlined />}
              onClick={() => setActiveTab('variant_table')}
            >
              异文汇校表
            </Button>
            <Button
              type={activeTab === 'phylogeny' ? 'primary' : 'default'}
              icon={<ApartmentOutlined />}
              onClick={() => setActiveTab('phylogeny')}
            >
              版本谱系
            </Button>
            <Button
              type={activeTab === 'collation_notes' ? 'primary' : 'default'}
              icon={<FileTextOutlined />}
              onClick={() => setActiveTab('collation_notes')}
            >
              校勘记
            </Button>
          </Space>

          {/* 版本选择区 - 单选模式 */}
          <Space>
            <Text type="secondary" style={{ whiteSpace: 'nowrap' }}>校本:</Text>
            <Select
              style={{ minWidth: 200 }}
              placeholder="选择要查看的校本"
              value={selectedVersions[0]}
              onChange={(value: number) => {
                setSelectedVersions([value])
                setActiveTab(`collation_${value}`)
              }}
              options={versionOptions}
              optionRender={(option) => (
                <Tooltip title={option.data.fullName} placement="right">
                  <span>{option.data.label}</span>
                </Tooltip>
              )}
            />
          </Space>

          {/* 生成定本按钮 */}
          {currentProjectId && Object.keys(decisions).length > 0 && (
            <Button
              type="primary"
              icon={<FileTextOutlined />}
              onClick={() => generateDefinitiveText(false)}
              loading={generatingDefinitive}
            >
              生成定本
            </Button>
          )}

          {/* 导出按钮 */}
          <Dropdown menu={{ items: exportMenuItems }} trigger={['click']}>
            <Button icon={<DownloadOutlined />}>
              导出 <DownOutlined />
            </Button>
          </Dropdown>
        </Space>
      </div>
    )
  }

  // 渲染当前选中的内容区域
  const renderContent = () => {
    if (!result) return null

    // 汇总统计
    if (activeTab === 'summary') {
      return (
        <Card>
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Statistic title="底本" value={result.base.name} valueStyle={{ fontSize: 16 }} />
            </Col>
            <Col span={6}>
              <Statistic title="底本字数" value={result.base.char_count} suffix="字" />
            </Col>
            <Col span={6}>
              <Statistic title="校本数量" value={result.collations.length} suffix="个" />
            </Col>
            <Col span={6}>
              <Statistic title="处理耗时" value={result.processing_time} suffix="秒" />
            </Col>
          </Row>
          <Divider>各校本差异统计</Divider>
          {renderSummaryTable()}
        </Card>
      )
    }

    // 异文汇校表
    if (activeTab === 'variant_table') {
      return (
        <Card>
          <Alert
            type="info"
            message="异文汇校表"
            description="显示同一位置各版本的不同写法，便于对照分析。红色高亮表示与底本不同。"
            style={{ marginBottom: 16 }}
          />
          {renderVariantTable()}
        </Card>
      )
    }

    // 版本谱系
    if (activeTab === 'phylogeny') {
      return (
        <Card>
          <Alert
            type="info"
            message="版本谱系分析"
            description="基于文本相似度，分析各版本之间的亲疏关系。相似度越高，版本越接近。"
            style={{ marginBottom: 16 }}
          />
          {renderPhylogeny()}
        </Card>
      )
    }

    // 校勘记
    if (activeTab === 'collation_notes') {
      return (
        <Card>
          <Alert
            type="info"
            message="校勘记"
            description="基于校勘判取结果，自动生成符合《中华大藏经》体例的校勘记。支持编辑和导出。"
            style={{ marginBottom: 16 }}
          />
          <CollationNotePanel
            projectId={currentProjectId}
            decisionsCount={Object.keys(decisions).length}
            onLocate={jumpToVariantPosition}
            onEditDecision={openDecisionModalForPosition}
            onDeleteDecision={(position) => {
              // 从本地状态中删除判取记录
              setDecisions(prev => {
                const newDecisions = { ...prev }
                delete newDecisions[position]
                return newDecisions
              })
            }}
          />
        </Card>
      )
    }

    // 校本详情
    if (activeTab.startsWith('collation_')) {
      const idx = parseInt(activeTab.replace('collation_', ''))
      const coll = result.collations[idx]
      if (!coll) return null

      return (
        <CollationView
          data={{
            mode: coll.result.mode,
            mode_description: coll.result.mode_description || '文字校勘模式',
            version1_name: coll.result.version1_name,
            version2_name: coll.result.version2_name,
            statistics: coll.result.statistics,
            similarity: coll.result.similarity,
            aligned_sentences: coll.result.aligned_sentences,
            side_by_side: coll.result.side_by_side,
          }}
          initialHighlight={
            initialHighlight && initialHighlight.collationIdx === idx
              ? { char: initialHighlight.char }
              : undefined
          }
        />
      )
    }

    return null
  }

  // 渲染结果区域（工具栏 + 内容）
  const renderResultTabs = () => {
    if (!result) return null

    return (
      <div>
        {renderToolbar()}
        {renderContent()}
      </div>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题 */}
        <Card>
          <div style={{ textAlign: 'center', position: 'relative' }}>
            {/* 历史项目按钮 - 右上角 */}
            <div style={{ position: 'absolute', right: 0, top: 0 }}>
              <Space>
                {currentProjectId && (
                  <Button
                    icon={<PlusOutlined />}
                    onClick={createNewProject}
                  >
                    新建项目
                  </Button>
                )}
                <Button
                  type="primary"
                  ghost
                  icon={<HistoryOutlined />}
                  onClick={openProjectDrawer}
                >
                  历史项目
                </Button>
              </Space>
            </div>

            <BookOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
            <h1 style={{ fontSize: 28, marginBottom: 8 }}>版本对勘</h1>
            <p style={{ color: '#666', fontSize: 16 }}>
              选择一个底本文件，与一个或多个校本文件进行对比，查看各校本与底本之间的差异
            </p>

            {/* 当前项目信息 */}
            {currentProjectId && (
              <div style={{
                marginTop: 16,
                padding: '12px 24px',
                background: '#f6ffed',
                borderRadius: 8,
                border: '1px solid #b7eb8f',
                display: 'inline-block',
              }}>
                <Space>
                  <SaveOutlined style={{ color: '#52c41a' }} />
                  <Text type="secondary">当前项目：</Text>
                  {editingTitle ? (
                    <Input
                      size="small"
                      defaultValue={currentProjectTitle}
                      style={{ width: 200 }}
                      onPressEnter={(e) => updateProjectTitle((e.target as HTMLInputElement).value)}
                      onBlur={(e) => updateProjectTitle(e.target.value)}
                      autoFocus
                    />
                  ) : (
                    <Text strong>{currentProjectTitle}</Text>
                  )}
                  <Tooltip title="编辑项目名称">
                    <Button
                      type="text"
                      size="small"
                      icon={<EditOutlined />}
                      onClick={() => setEditingTitle(true)}
                    />
                  </Tooltip>
                  <Tooltip title="复制项目ID">
                    <Button type="text" size="small" icon={<CopyOutlined />} onClick={() => void copyProjectId()} />
                  </Tooltip>
                  {result && result.collations && result.collations.length < 30 && (
                    <Button
                      size="small"
                      type="link"
                      icon={<PlusOutlined />}
                      onClick={() => setAddCollationModalOpen(true)}
                    >
                      追加校本
                    </Button>
                  )}
                  {currentProjectId && Object.keys(decisions).length > 0 && (
                    <Button
                      size="small"
                      type="link"
                      icon={<SaveOutlined />}
                      onClick={saveAllDecisions}
                    >
                      保存判取
                    </Button>
                  )}
                  {result && result.collations && result.collations.length > 1 && (
                    <Button
                      size="small"
                      type="link"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => setRemoveCollationModalOpen(true)}
                    >
                      去除校本
                    </Button>
                  )}
                </Space>
              </div>
            )}
          </div>
        </Card>

        {/* 上传区域 */}
        <Card title="上传底本与校本">
          <div style={{ display: 'flex', gap: 16, alignItems: 'stretch' }}>
            {/* 底本上传 */}
            <div style={{ flex: 1, minWidth: 0 }}>
              {baseFile ? (
                <Card
                  size="small"
                  style={{
                    border: '2px solid #1890ff',
                    borderRadius: 8,
                    height: '100%',
                  }}
                  title={
                    <Space>
                      <span style={{ color: '#1890ff' }}>底本文件</span>
                    </Space>
                  }
                  extra={
                    <Button
                      type="text"
                      danger
                      size="small"
                      onClick={() => setBaseFile(null)}
                    >
                      移除
                    </Button>
                  }
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text type="secondary">文件：</Text>
                      <Text strong>{baseFile.name}</Text>
                    </div>
                  </Space>
                </Card>
              ) : (
                <Upload.Dragger
                  accept=".txt,.docx"
                  maxCount={1}
                  fileList={[]}
                  onChange={handleBaseFileChange}
                  beforeUpload={() => false}
                  style={{
                    border: '2px dashed #1890ff',
                    borderRadius: 8,
                    background: '#fafafa',
                  }}
                >
                  <p className="ant-upload-drag-icon">
                    <InboxOutlined style={{ color: '#1890ff' }} />
                  </p>
                  <p className="ant-upload-text" style={{ color: '#1890ff' }}>底本文件</p>
                  <p className="ant-upload-hint">点击或拖拽上传</p>
                </Upload.Dragger>
              )}
            </div>

            {/* 校本上传 */}
            <div style={{ flex: 1, minWidth: 0 }}>
              {collationFiles.length > 0 ? (
                <Card
                  size="small"
                  style={{
                    border: '2px solid #52c41a',
                    borderRadius: 8,
                    height: '100%',
                    minHeight: 180,
                  }}
                  title={
                    <Space>
                      <span style={{ color: '#52c41a' }}>校本文件（{collationFiles.length}/30）</span>
                    </Space>
                  }
                  extra={
                    <Button
                      type="text"
                      danger
                      size="small"
                      onClick={() => setCollationFiles([])}
                    >
                      清空
                    </Button>
                  }
                >
                  <div style={{ maxHeight: 200, overflowY: 'auto', marginBottom: 8 }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      {collationFiles.map((file, idx) => (
                        <Tag
                          key={idx}
                          closable
                          onClose={() => setCollationFiles(collationFiles.filter((_, i) => i !== idx))}
                          style={{ margin: 2, maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis' }}
                        >
                          <Tooltip title={file.name}>
                            <span>{idx + 1}. {file.name.length > 12 ? file.name.slice(0, 10) + '...' : file.name}</span>
                          </Tooltip>
                        </Tag>
                      ))}
                    </div>
                  </div>
                  {collationFiles.length < MAX_COLLATION_FILES && (
                    <Upload
                      accept=".txt,.docx"
                      multiple
                      maxCount={MAX_COLLATION_FILES - collationFiles.length}
                      fileList={[]}
                      onChange={(info) => {
                        const newFiles = info.fileList.slice(0, MAX_COLLATION_FILES - collationFiles.length)
                        setCollationFiles([...collationFiles, ...newFiles])
                      }}
                      beforeUpload={() => false}
                      showUploadList={false}
                    >
                      <Button size="small" icon={<UploadOutlined />}>
                        继续添加（还可添加 {MAX_COLLATION_FILES - collationFiles.length} 个）
                      </Button>
                    </Upload>
                  )}
                </Card>
              ) : (
                <Upload.Dragger
                  accept=".txt,.docx"
                  multiple
                  maxCount={30}
                  fileList={[]}
                  onChange={handleCollationFilesChange}
                  beforeUpload={() => false}
                  style={{
                    border: '2px dashed #52c41a',
                    borderRadius: 8,
                    background: '#fafafa',
                  }}
                >
                  <p className="ant-upload-drag-icon">
                    <InboxOutlined style={{ color: '#52c41a' }} />
                  </p>
                  <p className="ant-upload-text" style={{ color: '#52c41a' }}>校本文件（1-30个）</p>
                  <p className="ant-upload-hint">点击或拖拽上传，支持多选</p>
                </Upload.Dragger>
              )}
            </div>
          </div>

          {/* 提示信息 */}
          <Alert
            message="使用提示"
            description={
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                <li>底本：作为对比基准的版本</li>
                <li>校本：最多可添加 {MAX_COLLATION_FILES} 个校本与底本进行对比</li>
                <li>支持格式：.txt、.docx | 单个文件最大 10MB</li>
              </ul>
            }
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />

          <div style={{ marginTop: 24, textAlign: 'center' }}>
            <Button
              type="primary"
              size="large"
              onClick={handleSubmit}
              loading={loading}
              disabled={!baseFile || collationFiles.length === 0}
              style={{ minWidth: 200, height: 48, fontSize: 16 }}
            >
              开始版本对勘
            </Button>
          </div>
        </Card>


        {/* 加载状态 */}
        {loading && (
          <Card>
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
              <Spin size="large" />
              <p style={{ marginTop: 20, color: '#666' }}>
                正在进行版本对勘，请稍候...
              </p>
            </div>
          </Card>
        )}

        {/* 结果展示 */}
        {result && !loading && (
          <Card>{renderResultTabs()}</Card>
        )}
      </Space>

      {/* 项目列表抽屉 */}
      <Drawer
        title={
          <Space>
            <HistoryOutlined />
            <span>历史校勘项目</span>
            <Tag color="blue">{projectListTotal} 个</Tag>
            {projectSearch.trim() && (
              <Tag color="default">{filteredProjectList.length} / {projectListTotal}</Tag>
            )}
          </Space>
        }
        placement="right"
        width={480}
        open={projectDrawerOpen}
        onClose={() => setProjectDrawerOpen(false)}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={createNewProject}
          >
            新建项目
          </Button>
        }
      >
        {projectListLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin />
          </div>
        ) : projectList.length === 0 ? (
          <Empty description="暂无历史项目" />
        ) : (
          <div>
            <Input.Search
              allowClear
              value={projectSearch}
              placeholder="按项目ID/标题/底本/校本搜索（回车可按ID直达）"
              onChange={(e) => setProjectSearch(e.target.value)}
              onSearch={handleProjectSearch}
              style={{ marginBottom: 12 }}
            />
            {filteredProjectList.length === 0 ? (
              <Empty description="未找到匹配的项目" />
            ) : (
              <List
                dataSource={filteredProjectList}
                renderItem={(item) => (
                  <List.Item
                    style={{
                      background: item.id === currentProjectId ? '#e6f7ff' : 'transparent',
                      borderRadius: 8,
                      marginBottom: 8,
                      padding: '12px 16px',
                      border: '1px solid #f0f0f0',
                    }}
                    actions={[
                      <Button
                        type="link"
                        icon={<FolderOpenOutlined />}
                        onClick={() => loadProject(item.id)}
                      >
                        打开
                      </Button>,
                      <Popconfirm
                        title="确定删除此项目？"
                        description="删除后不可恢复"
                        onConfirm={() => deleteProject(item.id)}
                        okText="删除"
                        cancelText="取消"
                        okButtonProps={{ danger: true }}
                      >
                        <Button type="link" danger icon={<DeleteOutlined />}>
                          删除
                        </Button>
                      </Popconfirm>,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <span>{item.title}</span>
                          {item.id === currentProjectId && <Tag color="green">当前</Tag>}
                        </Space>
                      }
                      description={
                        <div style={{ fontSize: 12 }}>
                          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
                            <Text type="secondary">底本：</Text>
                            <Text
                              ellipsis={{ tooltip: item.metadata?.base_name || '-' }}
                              style={{ maxWidth: 320, display: 'inline-block' }}
                            >
                              {item.metadata?.base_name || '-'}
                            </Text>
                          </div>
                          <div style={{ marginTop: 4 }}>
                            <Space size={[12, 4]} wrap>
                              <span>
                                <Text type="secondary">校本：</Text>
                                {item.metadata?.collation_count || 0} 个
                                {item.metadata?.collation_names && (
                                  <Tooltip
                                    title={
                                      <div style={{ textAlign: 'left' }}>
                                        {item.metadata.collation_names.map((name, idx) => (
                                          <div key={idx} style={{ lineHeight: '20px' }}>
                                            {idx + 1}. {name}
                                          </div>
                                        ))}
                                      </div>
                                    }
                                  >
                                    <span style={{ marginLeft: 8, color: '#1890ff', cursor: 'pointer' }}>
                                      查看详情
                                    </span>
                                  </Tooltip>
                                )}
                              </span>

                              <span>
                                <Tooltip title="汇校表条目数（按底本位置合并，同一位置多校本差异只算 1 条）">
                                  <Text type="secondary">异文位点：</Text>
                                </Tooltip>
                                {item.metadata?.variant_count || 0} 条
                              </span>

                              {typeof item.metadata?.diff_total === 'number' && (
                                <span>
                                  <Tooltip title="差异总数（按各校本逐一累加，同一位置多校本差异会累计）">
                                    <Text type="secondary">差异总数：</Text>
                                  </Tooltip>
                                  {item.metadata.diff_total} 处
                                </span>
                              )}

                              <span>
                                <Text type="secondary">更新：</Text>
                                {new Date(item.updated_at).toLocaleString('zh-CN')}
                              </span>
                            </Space>
                          </div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </div>
        )}
      </Drawer>

      {/* 追加校本弹窗 */}
      <Modal
        title={
          <Space>
            <PlusOutlined />
            <span>追加校本到项目</span>
          </Space>
        }
        open={addCollationModalOpen}
        onCancel={() => {
          setAddCollationModalOpen(false)
          setNewCollationFiles([])
        }}
        onOk={handleAddCollations}
        okText="开始追加"
        cancelText="取消"
        confirmLoading={addingCollations}
        okButtonProps={{ disabled: newCollationFiles.length === 0 }}
        width={500}
      >
        <Alert
          message={`当前项目已有 ${result?.collations?.length || 0} 个校本，最多可追加 ${MAX_COLLATION_FILES - (result?.collations?.length || 0)} 个`}
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Upload.Dragger
          accept=".txt,.docx"
          multiple
          maxCount={MAX_COLLATION_FILES - (result?.collations?.length || 0)}
          fileList={newCollationFiles}
          onChange={(info) => {
            const maxNew = MAX_COLLATION_FILES - (result?.collations?.length || 0)
            setNewCollationFiles(info.fileList.slice(0, maxNew))
          }}
          beforeUpload={() => false}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽上传新的校本文件</p>
          <p className="ant-upload-hint">支持 .txt、.docx 格式</p>
        </Upload.Dragger>

        {newCollationFiles.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">已选择 {newCollationFiles.length} 个文件：</Text>
            <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {newCollationFiles.map((file, idx) => (
                <Tag
                  key={idx}
                  closable
                  onClose={() => setNewCollationFiles(newCollationFiles.filter((_, i) => i !== idx))}
                >
                  {file.name.length > 20 ? file.name.slice(0, 18) + '...' : file.name}
                </Tag>
              ))}
            </div>
          </div>
        )}
      </Modal>

      {/* 去除校本弹窗 */}
      <Modal
        title={
          <Space>
            <DeleteOutlined />
            <span>去除校本</span>
          </Space>
        }
        open={removeCollationModalOpen}
        onCancel={() => {
          setRemoveCollationModalOpen(false)
          setCollationsToRemove([])
        }}
        onOk={handleRemoveCollations}
        okText={removingCollations ? '处理中...' : '确认去除'}
        okButtonProps={{
          danger: true,
          disabled: collationsToRemove.length === 0,
          loading: removingCollations,
        }}
        cancelText="取消"
        destroyOnClose
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Alert
            type="warning"
            showIcon
            message="去除校本会重新生成汇总统计、异文汇校表和谱系分析"
            description="若已有判取结果引用被移除版本，系统将自动清理这些判取条目。"
          />
          <div>
            <div style={{ marginBottom: 8 }}>请选择要去除的校本（至少保留 1 个校本）：</div>
            <Select
              mode="multiple"
              style={{ width: '100%' }}
              placeholder="选择一个或多个校本"
              value={collationsToRemove}
              onChange={(v) => setCollationsToRemove(v)}
              options={(() => {
                const collations = result?.collations || []
                const orderedIndices = collationDisplayOrder.length
                  ? collationDisplayOrder
                  : collations.map((_, idx) => idx)

                return orderedIndices.map((idx) => ({
                  value: idx,
                  label: collations[idx]?.collation_name || `校本${idx + 1}`,
                }))
              })()}
            />
          </div>
        </Space>
      </Modal>

      {/* 校勘判取对话框 */}
      <CollationDecisionModal
        visible={decisionModalVisible}
        onCancel={handleDecisionCancel}
        onConfirm={handleDecisionConfirm}
        variantItem={currentVariantItem}
        collationNames={result?.summary?.collation_names || []}
        baseName={result?.base?.name || '底本'}
        existingDecision={currentVariantItem ? decisions[currentVariantItem.position] : null}
        projectId={currentProjectId || undefined}
      />

      {/* 定本预览弹窗 */}
      <Modal
        title={
          <div
            style={{ width: '100%', cursor: 'move' }}
            onMouseOver={() => definitiveDragDisabled && setDefinitiveDragDisabled(false)}
            onMouseOut={() => setDefinitiveDragDisabled(true)}
          >
            <Space>
              <FileTextOutlined />
              <span>校勘定本预览</span>
              <Tooltip title="拖动标题栏可移动窗口">
                <DragOutlined style={{ color: '#999', fontSize: 12 }} />
              </Tooltip>
            </Space>
          </div>
        }
        open={definitiveTextModalOpen}
        onCancel={() => setDefinitiveTextModalOpen(false)}
        footer={[
          <Button key="close" onClick={() => setDefinitiveTextModalOpen(false)}>
            关闭
          </Button>,
          <Button
            key="download-notes"
            icon={<DownloadOutlined />}
            onClick={() => downloadCollationNotes(definitiveTextData, currentProjectTitle)}
            disabled={!definitiveTextData?.notes?.length}
          >
            下载校勘记
          </Button>,
          <Button
            key="download"
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => downloadDefinitiveText(definitiveTextData, currentProjectTitle)}
          >
            下载定本
          </Button>,
        ]}
        width={900}
        modalRender={(modal) => (
          <Draggable
            disabled={definitiveDragDisabled}
            bounds={definitiveDragBounds}
            nodeRef={definitiveDragRef}
            onStart={(event, uiData) => onStartDefinitiveDrag(event, uiData)}
          >
            <div ref={definitiveDragRef}>{modal}</div>
          </Draggable>
        )}
      >
        {definitiveTextData && (
          <div>
            {/* 统计信息 */}
            <Alert
              type="info"
              message="生成统计"
              description={
                <Row gutter={16}>
                  <Col span={6}>
                    <Statistic
                      title="底本字数"
                      value={definitiveTextData.statistics.base_char_count}
                      suffix="字"
                      valueStyle={{ fontSize: 16 }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="定本字数"
                      value={definitiveTextData.statistics.definitive_char_count}
                      suffix="字"
                      valueStyle={{ fontSize: 16 }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="已应用修改"
                      value={definitiveTextData.statistics.applied_count}
                      suffix="处"
                      valueStyle={{ fontSize: 16, color: '#52c41a' }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="存疑跳过"
                      value={definitiveTextData.statistics.skipped_uncertain_count}
                      suffix="处"
                      valueStyle={{ fontSize: 16, color: '#faad14' }}
                    />
                  </Col>
                </Row>
              }
              style={{ marginBottom: 16 }}
            />

            {/* 定本文本预览 */}
            <Card
              title="定本文本"
              size="small"
              style={{ marginBottom: 16 }}
              extra={
                <Text type="secondary">
                  共 {definitiveTextData.statistics.definitive_char_count} 字
                </Text>
              }
            >
              <div
                style={{
                  maxHeight: 300,
                  overflowY: 'auto',
                  fontFamily: "'Noto Serif SC', serif",
                  fontSize: 16,
                  lineHeight: 2,
                  whiteSpace: 'pre-wrap',
                  padding: 12,
                  background: '#fafafa',
                  borderRadius: 8,
                }}
              >
                {definitiveTextData.text}
              </div>
            </Card>

            {/* 校勘记列表 */}
            {definitiveTextData.notes.length > 0 && (
              <Card title="校勘记" size="small">
                <Table
                  columns={[
                    {
                      title: '位置',
                      dataIndex: 'position',
                      key: 'position',
                      width: 80,
                      align: 'center',
                    },
                    {
                      title: '改动',
                      dataIndex: 'text',
                      key: 'text',
                      width: 150,
                      render: (text: string) => (
                        <Text strong style={{ fontFamily: "'Noto Serif SC', serif" }}>
                          {text}
                        </Text>
                      ),
                    },
                    {
                      title: '采用版本',
                      dataIndex: 'version',
                      key: 'version',
                      width: 150,
                      ellipsis: true,
                    },
                    {
                      title: '依据',
                      dataIndex: 'basis',
                      key: 'basis',
                      width: 100,
                    },
                    {
                      title: '说明',
                      dataIndex: 'note',
                      key: 'note',
                      ellipsis: true,
                    },
                  ]}
                  dataSource={definitiveTextData.notes.map((note, idx) => ({
                    ...note,
                    key: idx,
                  }))}
                  pagination={{ pageSize: 10, size: 'small' }}
                  size="small"
                  scroll={{ y: 200 }}
                />
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
