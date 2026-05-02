/**
 * 校勘记面板组件
 *
 * 显示生成的校勘记列表，支持：
 * - 一键生成校勘记
 * - 导出（Word/Markdown/TXT）
 * - 统计信息显示
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  Card,
  Button,
  Space,
  Table,
  Tag,
  Typography,
  Tooltip,
  Modal,
  message,
  Spin,
  Alert,
  Empty,
  Dropdown,
  Row,
  Col,
  Statistic,
  Switch,
  Divider,
} from 'antd'
import {
  FileTextOutlined,
  DownloadOutlined,
  DeleteOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  QuestionCircleOutlined,
  DownOutlined,
  CopyOutlined,
  ExclamationCircleOutlined,
  AimOutlined,
  FormOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { MenuProps } from 'antd'

const { Text, Paragraph } = Typography

// API 基础地址
const API_BASE = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').trim()

// 校勘记类型定义
export interface CollationNoteItem {
  index: number
  position: number
  position_display: string
  original_char: string
  replacement_char: string
  action: string
  source_versions: string[]
  explanation: string
  category: string
  uncertain: boolean
  formatted_text: string
  decision_data?: Record<string, any>
  updated_at?: string
}

export interface CollationNoteStatistics {
  total: number
  decided: number
  uncertain: number
  by_category: Record<string, number>
  by_action: Record<string, number>
}

interface CollationNotePanelProps {
  projectId: string | null
  decisionsCount: number
  onGenerateComplete?: () => void
  onLocate?: (position: number) => void  // 定位到异文汇校表的指定位置
  onEditDecision?: (position: number) => void  // 编辑判取
  onDeleteDecision?: (position: number) => void  // 删除判取（同时删除校勘记时调用）
}

export default function CollationNotePanel({
  projectId,
  decisionsCount,
  onGenerateComplete,
  onLocate,
  onEditDecision,
  onDeleteDecision,
}: CollationNotePanelProps) {
  // 状态
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [notes, setNotes] = useState<CollationNoteItem[]>([])
  const [statistics, setStatistics] = useState<CollationNoteStatistics | null>(null)
  const [generatedAt, setGeneratedAt] = useState<string | null>(null)

  // 显示选项
  const [showUncertain, setShowUncertain] = useState(true)
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  // 加载校勘记
  const loadNotes = useCallback(async () => {
    if (!projectId) return

    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/v1/multi-collation/projects/${projectId}/collation-notes`)
      if (!response.ok) {
        throw new Error('加载校勘记失败')
      }
      const data = await response.json()
      if (data.success) {
        setNotes(data.notes || [])
        setStatistics(data.statistics || null)
        setGeneratedAt(data.generated_at || null)
      }
    } catch (error) {
      console.error('加载校勘记失败:', error)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  // 首次加载
  useEffect(() => {
    loadNotes()
  }, [loadNotes])

  // 生成校勘记
  const handleGenerate = async () => {
    if (!projectId) {
      message.warning('请先保存项目')
      return
    }
    if (decisionsCount === 0) {
      message.warning('请先完成一些校勘判取')
      return
    }

    setGenerating(true)
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${projectId}/generate-collation-notes`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ regenerate: notes.length > 0 }),
        }
      )
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '生成失败')
      }
      const data = await response.json()
      if (data.success) {
        setNotes(data.notes || [])
        message.success(data.message || `成功生成 ${data.total} 条校勘记`)
        await loadNotes() // 重新加载以获取统计信息
        onGenerateComplete?.()
      }
    } catch (error: any) {
      message.error(error.message || '生成校勘记失败')
    } finally {
      setGenerating(false)
    }
  }

  // 删除校勘记（同时删除判取记录）
  const handleDelete = (note: CollationNoteItem) => {
    Modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>确定要删除这条校勘记吗？</p>
          <p style={{ color: '#666', fontSize: 12, marginTop: 8 }}>
            【{note.index}】{note.position_display}「{note.original_char}」→「{note.replacement_char}」
          </p>
        </div>
      ),
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          // 删除校勘记（后端会同时删除判取记录）
          const response = await fetch(
            `${API_BASE}/api/v1/multi-collation/projects/${projectId}/collation-notes/${note.index}?delete_decision=true`,
            { method: 'DELETE' }
          )
          if (!response.ok) {
            throw new Error('删除失败')
          }
          const data = await response.json()
          if (data.success) {
            // 更新本地状态，重新编号
            setNotes(prev => {
              const filtered = prev.filter(n => n.index !== note.index)
              return filtered.map((n, idx) => ({ ...n, index: idx + 1 }))
            })
            message.success('删除成功')
            // 通知父组件更新判取状态
            onDeleteDecision?.(note.position)
            // 重新加载以获取最新统计
            loadNotes()
          }
        } catch (error: any) {
          message.error(error.message || '删除失败')
        }
      },
    })
  }

  // 导出功能
  const handleExport = async (format: 'word' | 'markdown' | 'txt') => {
    if (!projectId || notes.length === 0) {
      message.warning('无校勘记可导出')
      return
    }

    setExporting(true)
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${projectId}/export-collation-notes`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            format,
            include_statistics: true,
            include_base_info: true,
          }),
        }
      )

      if (!response.ok) {
        throw new Error('导出失败')
      }

      // 获取文件名
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = `校勘记.${format === 'word' ? 'docx' : format === 'markdown' ? 'md' : 'txt'}`
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/)
        if (filenameMatch) {
          filename = decodeURIComponent(filenameMatch[1])
        }
      }

      // 下载文件
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      message.success('导出成功')
    } catch (error: any) {
      message.error(error.message || '导出失败')
    } finally {
      setExporting(false)
    }
  }

  // 复制全部校勘记
  const handleCopyAll = () => {
    const text = notes.map(n => n.formatted_text).join('\n')
    navigator.clipboard.writeText(text)
      .then(() => message.success('已复制到剪贴板'))
      .catch(() => message.error('复制失败'))
  }

  // 导出菜单
  const exportMenuItems: MenuProps['items'] = [
    {
      key: 'word',
      label: '导出 Word',
      icon: <FileTextOutlined />,
      onClick: () => handleExport('word'),
    },
    {
      key: 'markdown',
      label: '导出 Markdown',
      icon: <FileTextOutlined />,
      onClick: () => handleExport('markdown'),
    },
    {
      key: 'txt',
      label: '导出 TXT',
      icon: <FileTextOutlined />,
      onClick: () => handleExport('txt'),
    },
    { type: 'divider' },
    {
      key: 'copy',
      label: '复制全部',
      icon: <CopyOutlined />,
      onClick: handleCopyAll,
    },
  ]

  // 过滤后的校勘记
  const filteredNotes = useMemo(() => {
    let filtered = notes
    if (!showUncertain) {
      filtered = filtered.filter(n => !n.uncertain)
    }
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(n => n.category === categoryFilter)
    }
    return filtered
  }, [notes, showUncertain, categoryFilter])

  // 类别选项
  const categoryOptions = useMemo(() => {
    const categories = new Set(notes.map(n => n.category))
    return [
      { value: 'all', label: '全部类型' },
      ...Array.from(categories).map(cat => ({ value: cat, label: cat })),
    ]
  }, [notes])

  // 表格列
  const columns: ColumnsType<CollationNoteItem> = [
    {
      title: '序号',
      dataIndex: 'index',
      key: 'index',
      width: 50,
      align: 'center',
    },
    {
      title: '位置',
      dataIndex: 'position_display',
      key: 'position_display',
      width: 70,
      align: 'center',
    },
    {
      title: '原字',
      dataIndex: 'original_char',
      key: 'original_char',
      width: 50,
      align: 'center',
      render: (char: string) => (
        <Text strong style={{ color: '#1890ff', fontSize: 16, whiteSpace: 'nowrap' }}>
          {char === '∅' ? '无' : char}
        </Text>
      ),
    },
    {
      title: '动作',
      dataIndex: 'action',
      key: 'action',
      width: 50,
      align: 'center',
      render: (action: string) => {
        const colorMap: Record<string, string> = {
          '改': 'blue',
          '删': 'red',
          '补': 'green',
          '乙': 'purple',
          '不改': 'default',
        }
        return <Tag color={colorMap[action] || 'default'}>{action}</Tag>
      },
    },
    {
      title: '改字',
      dataIndex: 'replacement_char',
      key: 'replacement_char',
      width: 50,
      align: 'center',
      render: (char: string) => (
        <Text strong style={{ color: '#52c41a', fontSize: 16, whiteSpace: 'nowrap' }}>
          {char === '∅' ? '删' : char}
        </Text>
      ),
    },
    {
      title: '类型',
      dataIndex: 'category',
      key: 'category',
      width: 70,
      align: 'center',
      render: (category: string) => {
        const colorMap: Record<string, string> = {
          '讹误': 'red',
          '异体字': 'green',
          '衍文': 'orange',
          '脱文': 'orange',
          '倒文': 'purple',
        }
        return <Tag color={colorMap[category] || 'default'}>{category}</Tag>
      },
    },
    {
      title: '校勘记',
      dataIndex: 'formatted_text',
      key: 'formatted_text',
      ellipsis: true,
      render: (text: string, record: CollationNoteItem) => (
        <Tooltip title={text} placement="topLeft">
          <Paragraph
            ellipsis={{ rows: 2 }}
            style={{
              marginBottom: 0,
              color: record.uncertain ? '#faad14' : undefined,
            }}
          >
            {record.uncertain && <QuestionCircleOutlined style={{ marginRight: 4, color: '#faad14' }} />}
            {text}
          </Paragraph>
        </Tooltip>
      ),
    },
    {
      title: '状态',
      key: 'status',
      width: 50,
      align: 'center',
      render: (_: any, record: CollationNoteItem) => (
        record.uncertain
          ? <Tooltip title="存疑"><QuestionCircleOutlined style={{ color: '#faad14', fontSize: 16 }} /></Tooltip>
          : <Tooltip title="已确定"><CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} /></Tooltip>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      align: 'center',
      render: (_: any, record: CollationNoteItem) => (
        <Space size={0}>
          {onLocate && (
            <Tooltip title="定位到异文表">
              <Button
                type="text"
                size="small"
                icon={<AimOutlined />}
                onClick={() => onLocate(record.position)}
              />
            </Tooltip>
          )}
          {onEditDecision && (
            <Tooltip title="编辑判取">
              <Button
                type="text"
                size="small"
                icon={<FormOutlined />}
                onClick={() => onEditDecision(record.position)}
              />
            </Tooltip>
          )}
          <Tooltip title="删除">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  // 渲染统计卡片
  const renderStatistics = () => {
    if (!statistics) return null

    return (
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="总条数"
              value={statistics.total}
              suffix="条"
              valueStyle={{ fontSize: 20 }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="已确定"
              value={statistics.decided}
              suffix="条"
              valueStyle={{ color: '#52c41a', fontSize: 20 }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="存疑"
              value={statistics.uncertain}
              suffix="条"
              valueStyle={{ color: '#faad14', fontSize: 20 }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card size="small">
            <Text type="secondary">异文类型分布：</Text>
            <Space wrap style={{ marginTop: 8 }}>
              {Object.entries(statistics.by_category || {}).map(([cat, count]) => (
                <Tag key={cat}>{cat}: {count}</Tag>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>
    )
  }

  // 无数据状态
  if (!projectId) {
    return (
      <Card>
        <Empty
          description="请先保存项目后再生成校勘记"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    )
  }

  return (
    <div>
      {/* 工具栏 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16,
        padding: '12px 16px',
        background: '#fafafa',
        borderRadius: 6,
        border: '1px solid #e8e8e8',
      }}>
        <Space>
          <Button
            type="primary"
            icon={notes.length > 0 ? <ReloadOutlined /> : <FileTextOutlined />}
            onClick={handleGenerate}
            loading={generating}
            disabled={decisionsCount === 0}
          >
            {notes.length > 0 ? '重新生成' : '生成校勘记'}
          </Button>

          {notes.length > 0 && (
            <>
              <Divider type="vertical" />
              <Text type="secondary">
                共 {notes.length} 条
                {generatedAt && ` (${new Date(generatedAt).toLocaleString()})`}
              </Text>
            </>
          )}
        </Space>

        <Space>
          {/* 筛选控件 */}
          {notes.length > 0 && (
            <>
              <Space size="small">
                <Text type="secondary">显示存疑:</Text>
                <Switch
                  size="small"
                  checked={showUncertain}
                  onChange={setShowUncertain}
                />
              </Space>
              <select
                value={categoryFilter}
                onChange={e => setCategoryFilter(e.target.value)}
                style={{
                  padding: '4px 8px',
                  borderRadius: 4,
                  border: '1px solid #d9d9d9',
                }}
              >
                {categoryOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </>
          )}

          {/* 导出按钮 */}
          {notes.length > 0 && (
            <Dropdown
              menu={{ items: exportMenuItems }}
              trigger={['click']}
              disabled={exporting}
            >
              <Button icon={<DownloadOutlined />} loading={exporting}>
                导出 <DownOutlined />
              </Button>
            </Dropdown>
          )}
        </Space>
      </div>

      {/* 提示信息 */}
      {decisionsCount === 0 && (
        <Alert
          type="info"
          message="请先完成校勘判取"
          description="在异文汇校表中点击各异文位置，完成判取后再生成校勘记。"
          style={{ marginBottom: 16 }}
          showIcon
        />
      )}

      {/* 判取数量变化提示 */}
      {notes.length > 0 && decisionsCount > 0 && notes.length !== decisionsCount && (
        <Alert
          type="warning"
          message="判取数量已更新"
          description={`当前有 ${decisionsCount} 条判取记录，但校勘记只有 ${notes.length} 条。点击「重新生成」按钮更新校勘记。`}
          style={{ marginBottom: 16 }}
          showIcon
          action={
            <Button size="small" type="primary" onClick={handleGenerate} loading={generating}>
              重新生成
            </Button>
          }
        />
      )}

      {/* 统计信息 */}
      {renderStatistics()}

      {/* 内容区 */}
      <Spin spinning={loading || generating}>
        {notes.length === 0 ? (
          <Card>
            <Empty
              description={
                decisionsCount > 0
                  ? "点击「生成校勘记」按钮开始生成"
                  : "完成校勘判取后可生成校勘记"
              }
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              {decisionsCount > 0 && (
                <Button type="primary" onClick={handleGenerate} loading={generating}>
                  生成校勘记
                </Button>
              )}
            </Empty>
          </Card>
        ) : (
          <Card>
            <Table
              dataSource={filteredNotes}
              columns={columns}
              rowKey="index"
              size="small"
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                pageSizeOptions: ['10', '20', '50', '100'],
                showTotal: (total) => `共 ${total} 条`,
              }}
              scroll={{ y: 500 }}
            />
          </Card>
        )}
      </Spin>
    </div>
  )
}
