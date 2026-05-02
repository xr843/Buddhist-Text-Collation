/**
 * 项目编辑器组件 - 左右分栏布局
 *
 * 左侧：经论原文显示（支持高亮和点击跳转）
 * 右侧：注疏管理和引文列表
 */
import { useState, useCallback, useRef, useEffect } from 'react'
import {
  Card,
  Upload,
  Button,
  Typography,
  Space,
  message,
  List,
  Tag,
  Divider,
  Row,
  Col,
  Statistic,
  Collapse,
  Tooltip,
  Popconfirm,
  Progress,
  Input,
  Modal,
  Form,
  Empty,
  Badge,
} from 'antd'
import {
  UploadOutlined,
  FileTextOutlined,
  CommentOutlined,
  DeleteOutlined,
  SyncOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  QuestionCircleOutlined,
  InboxOutlined,
} from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import { apiFetchJson } from '../../utils/apiFetch'
import type { SutraCommentaryProject } from './index'

const { Text } = Typography
const { Dragger } = Upload
const { Panel } = Collapse

interface ProjectEditorProps {
  project: SutraCommentaryProject
  onProjectUpdate: (projectId: string) => void
}

interface Citation {
  id: string
  marker: string
  extracted_text: string
  context_before: string
  context_after: string
  commentary_id: string
  commentary_title: string
  matched_positions: Array<{
    position: number
    similarity: number
    matched_text: string
  }>
}

export default function ProjectEditor({ project, onProjectUpdate }: ProjectEditorProps) {
  // 状态
  const [loading, setLoading] = useState(false)
  const [matching, setMatching] = useState(false)
  const [citations, setCitations] = useState<Citation[]>([])
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const [highlightPosition, setHighlightPosition] = useState<number | null>(null)
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [uploadType, setUploadType] = useState<'sutra' | 'commentary'>('sutra')
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [form] = Form.useForm()

  const sutraRef = useRef<HTMLDivElement>(null)

  // 加载所有引文
  const loadCitations = useCallback(async () => {
    try {
      const res = await apiFetchJson(`/api/v1/sutra-commentary/projects/${project.id}/citations`) as { citations: Citation[] }
      setCitations(res.citations || [])
    } catch (err: any) {
      console.error('加载引文失败:', err)
    }
  }, [project.id])

  // 执行批量匹配
  const handleMatch = async () => {
    setMatching(true)
    try {
      const res = await apiFetchJson(`/api/v1/sutra-commentary/projects/${project.id}/match`, {
        method: 'POST',
      }) as { message: string }
      message.success(res.message)
      onProjectUpdate(project.id)
      loadCitations()
    } catch (err: any) {
      message.error(`匹配失败: ${err.message}`)
    } finally {
      setMatching(false)
    }
  }

  // 上传经论
  const handleUploadSutra = async (file: File, title: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', title)

    try {
      setLoading(true)
      await fetch(`/api/v1/sutra-commentary/projects/${project.id}/sutra`, {
        method: 'POST',
        body: formData,
      }).then(async (res) => {
        if (!res.ok) {
          const err = await res.json()
          throw new Error(err.detail || '上传失败')
        }
        return res.json()
      })
      message.success('经论上传成功')
      setUploadModalOpen(false)
      setUploadFile(null)
      form.resetFields()
      onProjectUpdate(project.id)
    } catch (err: any) {
      message.error(`上传失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  // 上传注疏
  const handleUploadCommentary = async (file: File, title: string, markers?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', title)
    if (markers) {
      formData.append('marker_patterns', markers)
    }

    try {
      setLoading(true)
      const res = await fetch(`/api/v1/sutra-commentary/projects/${project.id}/commentary`, {
        method: 'POST',
        body: formData,
      }).then(async (res) => {
        if (!res.ok) {
          const err = await res.json()
          throw new Error(err.detail || '上传失败')
        }
        return res.json()
      })
      message.success(res.message)
      setUploadModalOpen(false)
      setUploadFile(null)
      form.resetFields()
      onProjectUpdate(project.id)
      loadCitations()
    } catch (err: any) {
      message.error(`上传失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  // 删除注疏
  const handleDeleteCommentary = async (commentaryId: string) => {
    try {
      await apiFetchJson(
        `/api/v1/sutra-commentary/projects/${project.id}/commentary/${commentaryId}`,
        { method: 'DELETE' }
      )
      message.success('注疏已删除')
      onProjectUpdate(project.id)
      loadCitations()
    } catch (err: any) {
      message.error(`删除失败: ${err.message}`)
    }
  }

  // 点击引文，跳转到经论对应位置
  const handleCitationClick = (citation: Citation) => {
    setSelectedCitation(citation)
    if (citation.matched_positions && citation.matched_positions.length > 0) {
      const firstMatch = citation.matched_positions[0]
      setHighlightPosition(firstMatch.position)
      // 滚动到对应位置
      scrollToPosition(firstMatch.position)
    }
  }

  // 滚动到经论指定位置
  const scrollToPosition = (position: number) => {
    if (sutraRef.current) {
      // 计算大致滚动位置（每行约50字）
      const lineHeight = 24
      const charsPerLine = 50
      const lineNumber = Math.floor((position - 1) / charsPerLine)
      const scrollTop = lineNumber * lineHeight - 100

      sutraRef.current.scrollTo({
        top: Math.max(0, scrollTop),
        behavior: 'smooth',
      })
    }
  }

  // 渲染经论文本（带高亮）
  const renderSutraText = () => {
    const content = project.data?.sutra?.content || ''
    if (!content) return null

    if (highlightPosition === null) {
      return (
        <pre
          style={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
            fontFamily: 'var(--font-family-chinese)',
            fontSize: '16px',
            lineHeight: '1.8',
            margin: 0,
          }}
        >
          {content}
        </pre>
      )
    }

    // 高亮匹配文本
    const matchedText = selectedCitation?.matched_positions?.[0]?.matched_text || ''
    const matchLen = matchedText.length || 10
    const start = Math.max(0, highlightPosition - 1)
    const end = Math.min(content.length, start + matchLen)

    const before = content.slice(0, start)
    const highlight = content.slice(start, end)
    const after = content.slice(end)

    return (
      <pre
        style={{
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
          fontFamily: 'var(--font-family-chinese)',
          fontSize: '16px',
          lineHeight: '1.8',
          margin: 0,
        }}
      >
        {before}
        <mark
          style={{
            backgroundColor: '#ffec3d',
            padding: '2px 0',
            borderRadius: '2px',
          }}
        >
          {highlight}
        </mark>
        {after}
      </pre>
    )
  }

  // 初始化加载引文
  useEffect(() => {
    if (project.data?.commentaries?.length > 0) {
      loadCitations()
    }
  }, [project.id, loadCitations])

  // 清除高亮
  const clearHighlight = () => {
    setHighlightPosition(null)
    setSelectedCitation(null)
  }

  const sutra = project.data?.sutra
  const commentaries = project.data?.commentaries || []
  const totalCitations = citations.length
  const matchedCitations = citations.filter((c) => c.matched_positions?.length > 0).length

  return (
    <div style={{ height: '100%', display: 'flex', gap: 16 }}>
      {/* 左侧：经论原文 */}
      <Card
        title={
          <Space>
            <FileTextOutlined />
            <span>经论原文</span>
            {sutra && (
              <Tag color="blue">{sutra.title}</Tag>
            )}
          </Space>
        }
        extra={
          <Space>
            {highlightPosition !== null && (
              <Button size="small" onClick={clearHighlight}>
                清除高亮
              </Button>
            )}
            <Button
              icon={<UploadOutlined />}
              onClick={() => {
                setUploadType('sutra')
                setUploadModalOpen(true)
              }}
            >
              {sutra ? '更换经论' : '上传经论'}
            </Button>
          </Space>
        }
        style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        bodyStyle={{ flex: 1, overflow: 'hidden', padding: 0 }}
      >
        {sutra ? (
          <div
            ref={sutraRef}
            style={{
              height: '100%',
              overflow: 'auto',
              padding: 16,
            }}
          >
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Statistic title="字数" value={sutra.char_count} />
                {sutra.source && (
                  <Tag>{sutra.source}</Tag>
                )}
              </Space>
            </div>
            <Divider style={{ margin: '12px 0' }} />
            {renderSutraText()}
          </div>
        ) : (
          <div
            style={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 24,
            }}
          >
            <Dragger
              accept=".txt"
              showUploadList={false}
              beforeUpload={(file) => {
                setUploadType('sutra')
                setUploadFile(file)
                form.setFieldsValue({ file: file.name, title: file.name.replace('.txt', '') })
                setUploadModalOpen(true)
                return false
              }}
              style={{ padding: '40px 20px' }}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽上传经论文本</p>
              <p className="ant-upload-hint">支持 .txt 格式（UTF-8 或 GBK 编码）</p>
            </Dragger>
          </div>
        )}
      </Card>

      {/* 右侧：注疏和引文 */}
      <Card
        title={
          <Space>
            <CommentOutlined />
            <span>关联注疏</span>
            <Badge count={commentaries.length} showZero style={{ backgroundColor: '#52c41a' }} />
          </Space>
        }
        extra={
          <Space>
            <Tooltip title="执行批量匹配">
              <Button
                icon={<SyncOutlined spin={matching} />}
                onClick={handleMatch}
                disabled={!sutra || commentaries.length === 0 || matching}
              >
                执行匹配
              </Button>
            </Tooltip>
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={() => {
                setUploadType('commentary')
                setUploadModalOpen(true)
              }}
            >
              上传注疏
            </Button>
          </Space>
        }
        style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        bodyStyle={{ flex: 1, overflow: 'auto', padding: 0 }}
      >
        {/* 统计信息 */}
        {commentaries.length > 0 && (
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>
            <Row gutter={16}>
              <Col span={8}>
                <Statistic title="注疏数" value={commentaries.length} />
              </Col>
              <Col span={8}>
                <Statistic title="引文总数" value={totalCitations} />
              </Col>
              <Col span={8}>
                <Statistic
                  title="已匹配"
                  value={matchedCitations}
                  suffix={`/ ${totalCitations}`}
                  valueStyle={{ color: matchedCitations > 0 ? '#52c41a' : undefined }}
                />
              </Col>
            </Row>
            {totalCitations > 0 && (
              <Progress
                percent={Math.round((matchedCitations / totalCitations) * 100)}
                size="small"
                style={{ marginTop: 8 }}
              />
            )}
          </div>
        )}

        {/* 注疏列表 */}
        <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
          {commentaries.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无关联注疏"
            />
          ) : (
            <Collapse defaultActiveKey={commentaries.map((c) => c.id)}>
              {commentaries.map((comm) => {
                const commCitations = citations.filter((c) => c.commentary_id === comm.id)
                // commMatched 用于未来扩展，暂时保留计算逻辑
                const _commMatched = commCitations.filter(
                  (c) => c.matched_positions?.length > 0
                ).length
                void _commMatched // 避免 unused 警告

                return (
                  <Panel
                    key={comm.id}
                    header={
                      <Space>
                        <span>{comm.title}</span>
                        <Tag>{comm.citations_count} 条引文</Tag>
                        {comm.matched_count > 0 && (
                          <Tag color="success">{comm.matched_count} 已匹配</Tag>
                        )}
                      </Space>
                    }
                    extra={
                      <Popconfirm
                        title="确定删除此注疏？"
                        onConfirm={(e) => {
                          e?.stopPropagation()
                          handleDeleteCommentary(comm.id)
                        }}
                        onCancel={(e) => e?.stopPropagation()}
                        okText="删除"
                        cancelText="取消"
                        okButtonProps={{ danger: true }}
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
                    <List
                      size="small"
                      dataSource={commCitations}
                      locale={{ emptyText: '暂无引文数据，请执行匹配' }}
                      renderItem={(citation) => {
                        const isMatched = citation.matched_positions?.length > 0
                        const isSelected = selectedCitation?.id === citation.id

                        return (
                          <List.Item
                            style={{
                              cursor: 'pointer',
                              backgroundColor: isSelected ? '#e6f7ff' : undefined,
                              borderRadius: 4,
                              padding: '8px 12px',
                              marginBottom: 4,
                            }}
                            onClick={() => handleCitationClick(citation)}
                          >
                            <div style={{ width: '100%' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                {isMatched ? (
                                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                                ) : (
                                  <QuestionCircleOutlined style={{ color: '#faad14' }} />
                                )}
                                <Tag color="blue">{citation.marker}</Tag>
                                <Text ellipsis style={{ flex: 1 }}>
                                  {citation.extracted_text.slice(0, 30)}
                                  {citation.extracted_text.length > 30 && '...'}
                                </Text>
                              </div>
                              {isMatched && (
                                <div style={{ marginTop: 4, marginLeft: 24 }}>
                                  <Text type="secondary" style={{ fontSize: 12 }}>
                                    <LinkOutlined /> 位置: {citation.matched_positions[0].position} |
                                    相似度: {Math.round(citation.matched_positions[0].similarity * 100)}%
                                  </Text>
                                </div>
                              )}
                            </div>
                          </List.Item>
                        )
                      }}
                    />
                  </Panel>
                )
              })}
            </Collapse>
          )}
        </div>
      </Card>

      {/* 上传弹窗 */}
      <Modal
        title={uploadType === 'sutra' ? '上传经论' : '上传注疏'}
        open={uploadModalOpen}
        onCancel={() => {
          setUploadModalOpen(false)
          setUploadFile(null)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        okText="上传"
        cancelText="取消"
        confirmLoading={loading}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => {
            if (!uploadFile) {
              message.error('请选择文件')
              return
            }
            if (uploadType === 'sutra') {
              handleUploadSutra(uploadFile, values.title)
            } else {
              handleUploadCommentary(uploadFile, values.title, values.markers)
            }
          }}
        >
          <Form.Item
            name="file"
            label="选择文件"
            rules={[{ required: true, message: '请选择文件' }]}
          >
            <Upload
              accept=".txt"
              maxCount={1}
              fileList={uploadFile ? [{ uid: '-1', name: uploadFile.name, status: 'done' } as UploadFile] : []}
              beforeUpload={(file) => {
                setUploadFile(file)
                form.setFieldsValue({ file: file.name, title: file.name.replace('.txt', '') })
                return false
              }}
              onRemove={() => {
                setUploadFile(null)
                form.setFieldsValue({ file: undefined })
              }}
            >
              <Button icon={<UploadOutlined />}>选择 .txt 文件</Button>
            </Upload>
          </Form.Item>

          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder={uploadType === 'sutra' ? '如：顺正理论卷十二' : '如：述文记卷九'} />
          </Form.Item>

          {uploadType === 'commentary' && (
            <Form.Item
              name="markers"
              label="引文标记词"
              help="可选，自定义用于识别引文的标记词，多个用逗号分隔"
            >
              <Input placeholder="如：论云,论曰,经云,释曰" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}
