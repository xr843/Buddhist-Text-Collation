/**
 * 两版本对勘页面 - 文字校勘
 * 支持项目持久化存储（保存/加载/列表/删除）
 */
import { useState, useCallback, useMemo } from 'react'
import {
  Card,
  message,
  Spin,
  Space,
  Button,
  Drawer,
  List,
  Empty,
  Tag,
  Popconfirm,
  Input,
  Typography,
  Tooltip,
} from 'antd'
import {
  FileSearchOutlined,
  HistoryOutlined,
  DeleteOutlined,
  FolderOpenOutlined,
  PlusOutlined,
  EditOutlined,
  SaveOutlined,
  CopyOutlined,
} from '@ant-design/icons'
import FileUploadCompare from '../components/FileUploadCompare'
import CollationView from '../components/CollationView'
import { apiFetchJson } from '../utils/apiFetch'

const { Text } = Typography
const API_BASE = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').trim()

// 项目摘要
interface ProjectSummary {
  id: string
  title: string
  description: string
  status: string
  created_at: string
  updated_at: string
  metadata: {
    base_name?: string
    collation_name?: string
    similarity?: number
    total_differences?: number
  }
}

export default function ComparisonNew() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  // 项目管理状态
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
        item.metadata?.base_name,
        item.metadata?.collation_name,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(query)
    })
  }, [projectList, projectSearch])

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

  // 加载项目列表
  const loadProjectList = useCallback(async () => {
    setProjectListLoading(true)
    try {
      const data = await apiFetchJson<{ items?: ProjectSummary[]; total?: number }>(
        '/api/v1/comparison/two-version/projects?limit=50',
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

  // 打开项目列表
  const openProjectDrawer = useCallback(() => {
    setProjectDrawerOpen(true)
    setProjectSearch('')
    loadProjectList()
  }, [loadProjectList])

  // 加载项目详情
  const loadProject = useCallback(async (projectId: string) => {
    setLoading(true)
    setProjectDrawerOpen(false)
    try {
      const data = await apiFetchJson<{ project: any }>(
        `/api/v1/comparison/two-version/projects/${projectId}`,
        { retries: 2 }
      )
      const project = data.project

      // 设置结果
      setResult(project.data.result)
      setCurrentProjectId(project.id)
      setCurrentProjectTitle(project.title)
      message.success(`已加载项目: ${project.title}`)
    } catch (error: any) {
      message.error('加载项目失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleProjectSearch = useCallback((value: string) => {
    const query = value.trim()
    if (!query) return
    const exact = projectList.find((p) => p.id === query)
    if (exact) {
      void loadProject(exact.id)
    }
  }, [loadProject, projectList])

  // 删除项目
  const deleteProject = useCallback(async (projectId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/comparison/two-version/projects/${projectId}`, {
        method: 'DELETE',
      })
      if (!response.ok) throw new Error('删除失败')
      message.success('项目已删除')
      loadProjectList()

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
      const response = await fetch(`${API_BASE}/api/v1/comparison/two-version/projects/${currentProjectId}`, {
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
    setEditingTitle(false)
  }, [currentProjectId])

  // 新建项目
  const createNewProject = useCallback(() => {
    setResult(null)
    setCurrentProjectId(null)
    setCurrentProjectTitle('')
    setProjectDrawerOpen(false)
  }, [])

  // 处理对比
  const handleCompare = async (
    file1: File,
    file2: File,
    version1Name: string,
    version2Name: string
  ) => {
    setLoading(true)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file1', file1)
      formData.append('file2', file2)
      formData.append('version1_name', version1Name)
      formData.append('version2_name', version2Name)
      formData.append('force_mode', 'collation')
      formData.append('auto_save', 'true')

      const response = await fetch(`${API_BASE}/api/v1/comparison/compare-files`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '对比失败')
      }

      const data = await response.json()
      console.log('[两版本对勘] 响应:', data)
      setResult(data)

      // 更新项目状态
      if (data.project) {
        setCurrentProjectId(data.project.id)
        setCurrentProjectTitle(data.project.title)
        message.success(`校勘完成，项目已保存`)
      } else {
        message.success('校勘分析完成！')
      }
    } catch (error: any) {
      console.error('[两版本对勘] 错误:', error)
      message.error(error.message || '对比失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题 */}
        <Card>
          <div style={{ textAlign: 'center', position: 'relative' }}>
            {/* 历史项目按钮 */}
            <div style={{ position: 'absolute', right: 0, top: 0 }}>
              <Space>
                {currentProjectId && (
                  <Button icon={<PlusOutlined />} onClick={createNewProject}>
                    新建项目
                  </Button>
                )}
                <Button type="primary" ghost icon={<HistoryOutlined />} onClick={openProjectDrawer}>
                  历史项目
                </Button>
              </Space>
            </div>

            <FileSearchOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
            <h1 style={{ fontSize: 28, marginBottom: 8 }}>两版本对勘</h1>
            <p style={{ color: '#666', fontSize: 16 }}>
              上传底本与校本（纯文本），进行文字校勘分析（异体字、讹误、衍文、脱文）
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
                    <Button type="text" size="small" icon={<EditOutlined />} onClick={() => setEditingTitle(true)} />
                  </Tooltip>
                  <Tooltip title="复制项目ID">
                    <Button type="text" size="small" icon={<CopyOutlined />} onClick={() => void copyProjectId()} />
                  </Tooltip>
                </Space>
              </div>
            )}
          </div>
        </Card>

        {/* 文件上传区域 */}
        <Card title="上传底本与校本">
          <FileUploadCompare onCompare={handleCompare} loading={loading} />
        </Card>

        {/* 加载状态 */}
        {loading && (
          <Card>
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
              <Spin size="large" />
              <p style={{ marginTop: 20, color: '#666' }}>
                正在进行文字校勘分析...
              </p>
            </div>
          </Card>
        )}

        {/* 结果展示 */}
        {!loading && result && (
          <CollationView data={result} />
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
        width={450}
        open={projectDrawerOpen}
        onClose={() => setProjectDrawerOpen(false)}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={createNewProject}>
            新建项目
          </Button>
        }
      >
        {projectListLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
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
                      <Button type="link" icon={<FolderOpenOutlined />} onClick={() => loadProject(item.id)}>
                        打开
                      </Button>,
                      <Popconfirm
                        title="确定删除此项目？"
                        onConfirm={() => deleteProject(item.id)}
                        okText="删除"
                        cancelText="取消"
                        okButtonProps={{ danger: true }}
                      >
                        <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
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
                          <div>
                            <Text type="secondary">底本：</Text>
                            {item.metadata?.base_name || '-'}
                          </div>
                          <div>
                            <Text type="secondary">校本：</Text>
                            {item.metadata?.collation_name || '-'}
                          </div>
                          <div>
                            <Text type="secondary">相似度：</Text>
                            {item.metadata?.similarity ? `${(item.metadata.similarity * 100).toFixed(1)}%` : '-'}
                          </div>
                          <div>
                            <Text type="secondary">更新：</Text>
                            {new Date(item.updated_at).toLocaleString('zh-CN')}
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
    </div>
  )
}
