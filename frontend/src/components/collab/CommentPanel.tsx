/**
 * 评论面板组件
 * 用于项目内的讨论和评论
 */
import React, { useState, useEffect, useRef } from 'react'
import {
  Card,
  List,
  Input,
  Button,
  Avatar,
  Space,
  Typography,
  Popconfirm,
  message,
  Empty,
  Spin,
  Tag,
  Tooltip,
} from 'antd'
import {
  CommentOutlined,
  SendOutlined,
  DeleteOutlined,
  EditOutlined,
  UserOutlined,
} from '@ant-design/icons'
import api from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import { getApiErrorMessage } from '../../utils/errors'

const { Text, Paragraph } = Typography
const { TextArea } = Input

interface Comment {
  id: number
  user_id: number
  username: string
  full_name?: string
  avatar_url?: string
  content: string
  variant_index?: number
  parent_id?: number
  created_at?: string
  updated_at?: string
}

interface CommentPanelProps {
  projectId: string
  variantIndex?: number  // 可选：针对特定异文的评论
  style?: React.CSSProperties
}

const CommentPanel: React.FC<CommentPanelProps> = ({
  projectId,
  variantIndex,
  style,
}) => {
  const { user, isAuthenticated } = useAuthStore()
  const [comments, setComments] = useState<Comment[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [content, setContent] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editContent, setEditContent] = useState('')
  const listRef = useRef<HTMLDivElement>(null)

  // 获取评论列表
  const fetchComments = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (variantIndex !== undefined) {
        params.variant_index = variantIndex
      }
      const response = await api.get(`/api/v1/collab/projects/${projectId}/comments`, { params })
      if (response.data.success) {
        setComments(response.data.comments || [])
      }
    } catch (error) {
      message.error(getApiErrorMessage(error, '获取评论失败'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (projectId) {
      fetchComments()
    }
  }, [projectId, variantIndex])

  // 发表评论
  const handleSubmit = async () => {
    if (!content.trim()) {
      message.warning('请输入评论内容')
      return
    }

    if (!isAuthenticated) {
      message.warning('请先登录')
      return
    }

    setSubmitting(true)
    try {
      const response = await api.post(`/api/v1/collab/projects/${projectId}/comments`, {
        content: content.trim(),
        variant_index: variantIndex,
      })
      if (response.data.success) {
        setContent('')
        fetchComments()
        // 滚动到底部
        setTimeout(() => {
          listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
        }, 100)
      }
    } catch (error) {
      message.error(getApiErrorMessage(error, '发表失败'))
    } finally {
      setSubmitting(false)
    }
  }

  // 编辑评论
  const handleEdit = async (commentId: number) => {
    if (!editContent.trim()) {
      message.warning('请输入评论内容')
      return
    }

    try {
      const response = await api.put(
        `/api/v1/collab/projects/${projectId}/comments/${commentId}`,
        { content: editContent.trim() }
      )
      if (response.data.success) {
        setEditingId(null)
        setEditContent('')
        fetchComments()
      }
    } catch (error) {
      message.error(getApiErrorMessage(error, '编辑失败'))
    }
  }

  // 删除评论
  const handleDelete = async (commentId: number) => {
    try {
      const response = await api.delete(
        `/api/v1/collab/projects/${projectId}/comments/${commentId}`
      )
      if (response.data.success) {
        fetchComments()
      }
    } catch (error) {
      message.error(getApiErrorMessage(error, '删除失败'))
    }
  }

  // 格式化时间
  const formatTime = (dateStr?: string) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()

    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`

    return date.toLocaleDateString('zh-CN')
  }

  return (
    <Card
      title={
        <Space>
          <CommentOutlined />
          <span>评论{variantIndex !== undefined && <Tag style={{ marginLeft: 8 }}>异文 #{variantIndex + 1}</Tag>}</span>
        </Space>
      }
      size="small"
      style={{ ...style }}
      bodyStyle={{ padding: 0 }}
    >
      {/* 评论列表 */}
      <div
        ref={listRef}
        style={{
          maxHeight: 400,
          overflowY: 'auto',
          padding: '12px 16px',
        }}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin />
          </div>
        ) : comments.length === 0 ? (
          <Empty description="暂无评论" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <List
            itemLayout="horizontal"
            dataSource={comments}
            renderItem={(item) => (
              <List.Item
                key={item.id}
                style={{ padding: '8px 0' }}
                actions={
                  user?.id === item.user_id
                    ? [
                        <Button
                          key="edit"
                          type="link"
                          size="small"
                          icon={<EditOutlined />}
                          onClick={() => {
                            setEditingId(item.id)
                            setEditContent(item.content)
                          }}
                        />,
                        <Popconfirm
                          key="delete"
                          title="确定删除这条评论？"
                          onConfirm={() => handleDelete(item.id)}
                        >
                          <Button type="link" size="small" danger icon={<DeleteOutlined />} />
                        </Popconfirm>,
                      ]
                    : undefined
                }
              >
                <List.Item.Meta
                  avatar={
                    <Avatar size="small" src={item.avatar_url} icon={<UserOutlined />} />
                  }
                  title={
                    <Space size="small">
                      <Text strong style={{ fontSize: 13 }}>
                        {item.full_name || item.username}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {formatTime(item.created_at)}
                      </Text>
                      {item.updated_at && item.updated_at !== item.created_at && (
                        <Tooltip title={`编辑于 ${new Date(item.updated_at).toLocaleString()}`}>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            (已编辑)
                          </Text>
                        </Tooltip>
                      )}
                    </Space>
                  }
                  description={
                    editingId === item.id ? (
                      <Space.Compact style={{ width: '100%', marginTop: 4 }}>
                        <Input
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          onPressEnter={() => handleEdit(item.id)}
                        />
                        <Button type="primary" onClick={() => handleEdit(item.id)}>
                          保存
                        </Button>
                        <Button onClick={() => setEditingId(null)}>取消</Button>
                      </Space.Compact>
                    ) : (
                      <Paragraph
                        style={{ marginBottom: 0, fontSize: 13 }}
                        ellipsis={{ rows: 3, expandable: true }}
                      >
                        {item.content}
                      </Paragraph>
                    )
                  }
                />
              </List.Item>
            )}
          />
        )}
      </div>

      {/* 发表评论 */}
      {isAuthenticated ? (
        <div style={{ padding: '12px 16px', borderTop: '1px solid #f0f0f0' }}>
          <Space.Compact style={{ width: '100%' }}>
            <TextArea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="发表评论..."
              autoSize={{ minRows: 1, maxRows: 4 }}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault()
                  handleSubmit()
                }
              }}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSubmit}
              loading={submitting}
            >
              发送
            </Button>
          </Space.Compact>
        </div>
      ) : (
        <div style={{ padding: '12px 16px', borderTop: '1px solid #f0f0f0', textAlign: 'center' }}>
          <Text type="secondary">请先登录后发表评论</Text>
        </div>
      )}
    </Card>
  )
}

export default CommentPanel
