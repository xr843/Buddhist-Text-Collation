/**
 * 项目列表抽屉组件
 */

import { Drawer, Space, Tag, Button, Spin, Empty, Input, List, Popconfirm, Typography } from 'antd'
import {
  HistoryOutlined,
  PlusOutlined,
  FolderOpenOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import type { ProjectSummary } from './types'

const { Text } = Typography

interface ProjectDrawerProps {
  open: boolean
  projectList: ProjectSummary[]
  filteredProjectList: ProjectSummary[]
  projectListLoading: boolean
  projectListTotal: number
  currentProjectId: string | null
  projectSearch: string
  onSearchChange: (value: string) => void
  onSearch: (value: string) => void
  onClose: () => void
  onLoad: (projectId: string) => void
  onDelete: (projectId: string) => void
  onCreateNew: () => void
}

export default function ProjectDrawer({
  open,
  projectList,
  filteredProjectList,
  projectListLoading,
  projectListTotal,
  currentProjectId,
  projectSearch,
  onSearchChange,
  onSearch,
  onClose,
  onLoad,
  onDelete,
  onCreateNew,
}: ProjectDrawerProps) {
  return (
    <Drawer
      title={
        <Space>
          <HistoryOutlined />
          <span>历史标点对比项目</span>
          <Tag color="blue">{projectListTotal} 个</Tag>
          {projectSearch.trim() && (
            <Tag color="default">
              {filteredProjectList.length} / {projectListTotal}
            </Tag>
          )}
        </Space>
      }
      placement="right"
      width={450}
      open={open}
      onClose={onClose}
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={onCreateNew}>
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
            placeholder="按项目ID/标题/版本A/版本B搜索（回车可按ID直达）"
            onChange={(e) => onSearchChange(e.target.value)}
            onSearch={onSearch}
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
                      onClick={() => onLoad(item.id)}
                    >
                      打开
                    </Button>,
                    <Popconfirm
                      title="确定删除此项目？"
                      onConfirm={() => onDelete(item.id)}
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
                        <div>
                          <Text type="secondary">版本A：</Text>
                          {item.metadata?.version1_name || '-'}
                        </div>
                        <div>
                          <Text type="secondary">版本B：</Text>
                          {item.metadata?.version2_name || '-'}
                        </div>
                        <div>
                          <Text type="secondary">差异数：</Text>
                          {item.metadata?.total_differences || 0} 处
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
  )
}
