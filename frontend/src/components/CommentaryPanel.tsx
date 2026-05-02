/**
 * 注疏面板组件 - 显示关联注疏及其引文列表
 * 支持：引文展示、定位到经文、用于校勘判取
 */
import { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Collapse,
  List,
  Tag,
  Button,
  Space,
  Typography,
  Empty,
  Spin,
  Tooltip,
  Badge,
  Divider,
  Upload,
  Input,
  Popconfirm,
  message,
} from 'antd'
import {
  BookOutlined,
  AimOutlined,
  CheckCircleOutlined,
  UploadOutlined,
  DeleteOutlined,
  ReloadOutlined,
  EnvironmentOutlined,
  LinkOutlined,
} from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'

const { Text, Paragraph } = Typography
const { Panel } = Collapse

// API 基础地址
const API_BASE = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').trim()

// 注疏信息接口
export interface CommentaryInfo {
  commentary_id: string
  title: string
  citations_count: number
}

// 引文接口
export interface Citation {
  id: string
  marker: string
  extracted_text: string
  original_text: string
  start_pos: number
  end_pos: number
  context_before: string
  context_after: string
}

// 引文匹配位置接口
export interface CitationMatch {
  citation_id: string
  position: number
  similarity: number
  matched_text: string
}

// 带匹配位置的完整引文数据
export interface CitationWithMatches extends Citation {
  commentary_id: string
  commentary_title: string
  matched_positions: CitationMatch[]
}

interface CommentaryPanelProps {
  projectId: string | null
  onLocateToPosition?: (position: number) => void
  onUseForDecision?: (citation: CitationWithMatches, matchPosition: number) => void
  style?: React.CSSProperties
}

export default function CommentaryPanel({
  projectId,
  onLocateToPosition,
  onUseForDecision,
  style,
}: CommentaryPanelProps) {
  // 注疏列表
  const [commentaryList, setCommentaryList] = useState<CommentaryInfo[]>([])
  const [loadingList, setLoadingList] = useState(false)

  // 所有引文数据（含匹配位置）
  const [allCitations, setAllCitations] = useState<CitationWithMatches[]>([])
  const [loadingCitations, setLoadingCitations] = useState(false)

  // 上传相关状态
  const [uploadFile, setUploadFile] = useState<UploadFile | null>(null)
  const [markerPatterns, setMarkerPatterns] = useState<string>('')
  const [uploading, setUploading] = useState(false)

  // 批量匹配状态
  const [batchMatching, setBatchMatching] = useState(false)

  // 加载注疏列表
  const loadCommentaryList = useCallback(async () => {
    if (!projectId) {
      setCommentaryList([])
      return
    }

    setLoadingList(true)
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${projectId}/commentary/list`
      )
      if (!response.ok) throw new Error('获取注疏列表失败')
      const data = await response.json()
      setCommentaryList(data.commentaries || [])
    } catch (error: any) {
      console.error('加载注疏列表失败:', error)
      message.error('加载注疏列表失败')
    } finally {
      setLoadingList(false)
    }
  }, [projectId])

  // 加载所有引文及其匹配位置
  const loadAllCitations = useCallback(async () => {
    if (!projectId) {
      setAllCitations([])
      return
    }

    setLoadingCitations(true)
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${projectId}/commentary/citations`
      )
      if (!response.ok) throw new Error('获取引文数据失败')
      const data = await response.json()
      setAllCitations(data.citations || [])
    } catch (error: any) {
      console.error('加载引文数据失败:', error)
      // 如果新API不存在，降级处理
      setAllCitations([])
    } finally {
      setLoadingCitations(false)
    }
  }, [projectId])

  // 上传注疏
  const uploadCommentary = useCallback(async () => {
    if (!projectId || !uploadFile) {
      message.warning('请选择注疏文件')
      return
    }

    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadFile.originFileObj as File)
      formData.append('title', uploadFile.name)
      if (markerPatterns.trim()) {
        formData.append('marker_patterns', markerPatterns.trim())
      }

      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${projectId}/commentary/upload`,
        {
          method: 'POST',
          body: formData,
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '上传失败')
      }

      const data = await response.json()
      message.success(`上传成功，提取 ${data.citations_count} 条引文`)

      // 清空上传状态
      setUploadFile(null)
      setMarkerPatterns('')

      // 刷新数据
      await loadCommentaryList()

      // 触发批量匹配
      await triggerBatchMatch()

    } catch (error: any) {
      console.error('上传注疏失败:', error)
      message.error('上传注疏失败: ' + error.message)
    } finally {
      setUploading(false)
    }
  }, [projectId, uploadFile, markerPatterns, loadCommentaryList])

  // 删除注疏
  const deleteCommentary = useCallback(async (commentaryId: string) => {
    if (!projectId) return

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${projectId}/commentary/${commentaryId}`,
        { method: 'DELETE' }
      )
      if (!response.ok) throw new Error('删除失败')

      message.success('注疏已删除')
      await loadCommentaryList()
      await loadAllCitations()
    } catch (error: any) {
      message.error('删除注疏失败: ' + error.message)
    }
  }, [projectId, loadCommentaryList, loadAllCitations])

  // 触发批量匹配
  const triggerBatchMatch = useCallback(async () => {
    if (!projectId) return

    setBatchMatching(true)
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/multi-collation/projects/${projectId}/commentary/batch-match`,
        { method: 'POST' }
      )

      if (!response.ok) {
        console.warn('批量匹配API可能不存在，跳过')
        return
      }

      const data = await response.json()
      message.success(`批量匹配完成，匹配 ${data.matched_count || 0} 条引文`)

      // 刷新引文数据
      await loadAllCitations()
    } catch (error: any) {
      console.error('批量匹配失败:', error)
    } finally {
      setBatchMatching(false)
    }
  }, [projectId, loadAllCitations])

  // 初始加载
  useEffect(() => {
    loadCommentaryList()
    loadAllCitations()
  }, [loadCommentaryList, loadAllCitations])

  // 处理文件选择
  const handleFileChange = (info: any) => {
    const file = info.fileList[0]
    setUploadFile(file || null)
  }

  // 按注疏分组引文
  const citationsByCommentary = allCitations.reduce((acc, cit) => {
    const key = cit.commentary_id
    if (!acc[key]) {
      acc[key] = {
        title: cit.commentary_title,
        citations: [],
      }
    }
    acc[key].citations.push(cit)
    return acc
  }, {} as Record<string, { title: string; citations: CitationWithMatches[] }>)

  // 渲染单条引文
  const renderCitationItem = (citation: CitationWithMatches) => {
    const hasMatches = citation.matched_positions && citation.matched_positions.length > 0
    const bestMatch = hasMatches
      ? citation.matched_positions.reduce((best, m) => m.similarity > best.similarity ? m : best, citation.matched_positions[0])
      : null

    return (
      <List.Item
        style={{
          background: hasMatches ? '#f6ffed' : '#fff',
          padding: '12px 16px',
          marginBottom: 8,
          borderRadius: 8,
          border: hasMatches ? '1px solid #b7eb8f' : '1px solid #f0f0f0',
        }}
      >
        <div style={{ width: '100%' }}>
          {/* 引文标记词和相似度 */}
          <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space>
              <Tag color="blue">{citation.marker}</Tag>
              {hasMatches && bestMatch && (
                <Tag color={
                  bestMatch.similarity >= 0.9 ? 'green' :
                  bestMatch.similarity >= 0.75 ? 'cyan' : 'orange'
                }>
                  相似度 {(bestMatch.similarity * 100).toFixed(0)}%
                </Tag>
              )}
            </Space>
            {hasMatches && (
              <Badge
                count={citation.matched_positions.length}
                style={{ backgroundColor: '#52c41a' }}
                title={`匹配到 ${citation.matched_positions.length} 个位置`}
              />
            )}
          </div>

          {/* 引文内容 */}
          <Paragraph
            style={{
              fontFamily: "'Noto Serif SC', 'Source Han Serif SC', serif",
              fontSize: 15,
              lineHeight: 1.8,
              marginBottom: 8,
              color: '#333',
            }}
            ellipsis={{ rows: 2, expandable: true, symbol: '展开' }}
          >
            {citation.extracted_text}
          </Paragraph>

          {/* 上下文 */}
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 12 }}>
            <EnvironmentOutlined style={{ marginRight: 4 }} />
            上下文：{citation.context_before}...{citation.context_after}
          </Text>

          {/* 匹配位置列表 */}
          {hasMatches && (
            <div style={{ marginTop: 8 }}>
              <Divider style={{ margin: '8px 0' }} />
              <Text type="secondary" style={{ fontSize: 12, marginBottom: 8, display: 'block' }}>
                <LinkOutlined style={{ marginRight: 4 }} />
                匹配位置：
              </Text>
              <Space wrap size={[8, 8]}>
                {citation.matched_positions.slice(0, 5).map((match, idx) => (
                  <Space key={idx} size={4}>
                    <Button
                      size="small"
                      type={idx === 0 ? 'primary' : 'default'}
                      icon={<AimOutlined />}
                      onClick={() => onLocateToPosition?.(match.position)}
                    >
                      第{match.position}字
                    </Button>
                    <Tag color={match.similarity >= 0.9 ? 'green' : match.similarity >= 0.75 ? 'blue' : 'orange'}>
                      {(match.similarity * 100).toFixed(0)}%
                    </Tag>
                  </Space>
                ))}
                {citation.matched_positions.length > 5 && (
                  <Text type="secondary">
                    ...还有 {citation.matched_positions.length - 5} 个位置
                  </Text>
                )}
              </Space>
            </div>
          )}

          {/* 操作按钮 */}
          {hasMatches && bestMatch && (
            <div style={{ marginTop: 12 }}>
              <Button
                type="primary"
                size="small"
                icon={<CheckCircleOutlined />}
                onClick={() => onUseForDecision?.(citation, bestMatch.position)}
              >
                用于校勘判取
              </Button>
            </div>
          )}
        </div>
      </List.Item>
    )
  }

  // 无项目时显示提示
  if (!projectId) {
    return (
      <Card
        title={<Space><BookOutlined /> 关联注疏</Space>}
        size="small"
        style={style}
      >
        <Empty description="请先保存项目后再上传注疏" />
      </Card>
    )
  }

  return (
    <Card
      title={
        <Space>
          <BookOutlined style={{ color: '#722ed1' }} />
          <span>关联注疏</span>
          {commentaryList.length > 0 && (
            <Tag color="purple">{commentaryList.length} 部</Tag>
          )}
        </Space>
      }
      size="small"
      style={style}
      extra={
        <Space>
          <Tooltip title="刷新引文匹配">
            <Button
              type="text"
              size="small"
              icon={<ReloadOutlined />}
              loading={batchMatching}
              onClick={triggerBatchMatch}
            />
          </Tooltip>
        </Space>
      }
    >
      {/* 上传区域 */}
      <div style={{ marginBottom: 16, padding: 12, background: '#fafafa', borderRadius: 8 }}>
        <Space direction="vertical" style={{ width: '100%' }} size={8}>
          <Space style={{ width: '100%' }}>
            <Upload
              accept=".txt"
              maxCount={1}
              fileList={uploadFile ? [uploadFile] : []}
              onChange={handleFileChange}
              beforeUpload={() => false}
              showUploadList={false}
            >
              <Button icon={<UploadOutlined />} size="small">
                选择注疏文件
              </Button>
            </Upload>
            {uploadFile && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {uploadFile.name}
              </Text>
            )}
          </Space>

          <Input
            placeholder='自定义标记词（如："论云,论曰,经云"）'
            value={markerPatterns}
            onChange={(e) => setMarkerPatterns(e.target.value)}
            size="small"
            style={{ width: '100%' }}
          />

          <Button
            type="primary"
            size="small"
            onClick={uploadCommentary}
            loading={uploading}
            disabled={!uploadFile}
            block
          >
            上传并提取引文
          </Button>
        </Space>
      </div>

      {/* 加载中 */}
      {(loadingList || loadingCitations) && (
        <div style={{ textAlign: 'center', padding: 20 }}>
          <Spin />
          <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
            加载注疏数据...
          </Text>
        </div>
      )}

      {/* 注疏列表 */}
      {!loadingList && !loadingCitations && commentaryList.length === 0 && (
        <Empty
          description="暂无关联注疏"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      )}

      {!loadingList && !loadingCitations && commentaryList.length > 0 && (
        <Collapse
          defaultActiveKey={commentaryList.map(c => c.commentary_id)}
          ghost
          style={{ background: 'transparent' }}
        >
          {commentaryList.map((comm) => {
            const commCitations = citationsByCommentary[comm.commentary_id]?.citations || []
            const matchedCount = commCitations.filter(c => c.matched_positions?.length > 0).length

            return (
              <Panel
                key={comm.commentary_id}
                header={
                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Space>
                      <BookOutlined style={{ color: '#722ed1' }} />
                      <Text strong>{comm.title}</Text>
                    </Space>
                    <Space>
                      <Tag color="purple">{comm.citations_count} 条引文</Tag>
                      {matchedCount > 0 && (
                        <Tag color="green">{matchedCount} 已匹配</Tag>
                      )}
                    </Space>
                  </Space>
                }
                extra={
                  <Popconfirm
                    title="确定删除此注疏？"
                    onConfirm={(e) => {
                      e?.stopPropagation()
                      deleteCommentary(comm.commentary_id)
                    }}
                    onCancel={(e) => e?.stopPropagation()}
                  >
                    <Button
                      type="text"
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </Popconfirm>
                }
              >
                {commCitations.length === 0 ? (
                  <Empty
                    description="暂无引文数据"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                ) : (
                  <List
                    dataSource={commCitations}
                    renderItem={renderCitationItem}
                    style={{ maxHeight: 400, overflow: 'auto' }}
                  />
                )}
              </Panel>
            )
          })}
        </Collapse>
      )}
    </Card>
  )
}
