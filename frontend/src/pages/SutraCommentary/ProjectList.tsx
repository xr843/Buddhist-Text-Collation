/**
 * 项目列表组件
 */
import { List, Button, Typography, Space, Popconfirm, Tag, Empty } from 'antd'
import {
  DeleteOutlined,
  BookOutlined,
  FileTextOutlined,
  CommentOutlined,
} from '@ant-design/icons'
import type { SutraCommentaryProject } from './index'

const { Text } = Typography

interface ProjectListProps {
  projects: SutraCommentaryProject[]
  loading: boolean
  onSelect: (projectId: string) => void
  onDelete: (projectId: string) => void
  onRefresh?: () => void  // 可选，供将来扩展使用
}

export default function ProjectList({
  projects,
  loading,
  onSelect,
  onDelete,
  // onRefresh 暂未使用，保留接口供将来刷新按钮使用
}: ProjectListProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (!loading && projects.length === 0) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description="暂无项目"
      />
    )
  }

  return (
    <List
      loading={loading}
      dataSource={projects}
      renderItem={(project) => (
        <List.Item
          style={{
            cursor: 'pointer',
            padding: '12px',
            borderRadius: '8px',
            marginBottom: '8px',
            border: '1px solid #f0f0f0',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#fafafa'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent'
          }}
          actions={[
            <Popconfirm
              key="delete"
              title="确定删除此项目？"
              description="删除后无法恢复"
              onConfirm={(e) => {
                e?.stopPropagation()
                onDelete(project.id)
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
            </Popconfirm>,
          ]}
          onClick={() => onSelect(project.id)}
        >
          <List.Item.Meta
            avatar={
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: '8px',
                  backgroundColor: '#e6f7ff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <BookOutlined style={{ fontSize: 18, color: '#1890ff' }} />
              </div>
            }
            title={
              <Space>
                <span>{project.title}</span>
              </Space>
            }
            description={
              <div>
                {project.description && (
                  <div style={{ marginBottom: 4 }}>
                    <Text type="secondary" ellipsis>
                      {project.description}
                    </Text>
                  </div>
                )}
                <Space size={[8, 4]} wrap>
                  {project.metadata?.sutra_title && (
                    <Tag icon={<FileTextOutlined />} color="blue">
                      {project.metadata.sutra_title}
                    </Tag>
                  )}
                  <Tag icon={<CommentOutlined />}>
                    {project.metadata?.commentary_count || 0} 部注疏
                  </Tag>
                  <Tag>
                    {project.metadata?.citation_count || 0} 条引文
                  </Tag>
                </Space>
                <div style={{ marginTop: 4 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    更新于 {formatDate(project.updated_at)}
                  </Text>
                </div>
              </div>
            }
          />
        </List.Item>
      )}
    />
  )
}
