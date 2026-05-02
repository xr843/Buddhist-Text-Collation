/**
 * 页面标题组件
 */

import { Card, Button, Space, Typography, Tooltip, Input } from 'antd'
import {
  DiffOutlined,
  HistoryOutlined,
  PlusOutlined,
  EditOutlined,
  CopyOutlined,
  SaveOutlined,
} from '@ant-design/icons'

const { Title, Paragraph, Text } = Typography

interface PageHeaderProps {
  currentProjectId: string | null
  currentProjectTitle: string
  editingTitle: boolean
  onOpenProjectDrawer: () => void
  onCreateNew: () => void
  onEditTitle: () => void
  onUpdateTitle: (newTitle: string) => void
  onCopyProjectId: () => void
}

export default function PageHeader({
  currentProjectId,
  currentProjectTitle,
  editingTitle,
  onOpenProjectDrawer,
  onCreateNew,
  onEditTitle,
  onUpdateTitle,
  onCopyProjectId,
}: PageHeaderProps) {
  return (
    <Card>
      <div style={{ textAlign: 'center', position: 'relative' }}>
        {/* 历史项目按钮 */}
        <div style={{ position: 'absolute', right: 0, top: 0 }}>
          <Space>
            {currentProjectId && (
              <Button icon={<PlusOutlined />} onClick={onCreateNew}>
                新建项目
              </Button>
            )}
            <Button type="primary" ghost icon={<HistoryOutlined />} onClick={onOpenProjectDrawer}>
              历史项目
            </Button>
          </Space>
        </div>

        <DiffOutlined style={{ fontSize: 48, color: '#52c41a', marginBottom: 16 }} />
        <Title level={2} style={{ marginBottom: 8 }}>
          标点版本对比
        </Title>
        <Paragraph type="secondary" style={{ fontSize: 16, marginBottom: 0 }}>
          上传两个带标点的佛典文本文件，进行标点差异分析
        </Paragraph>

        {/* 当前项目信息 */}
        {currentProjectId && (
          <div
            style={{
              marginTop: 16,
              padding: '12px 24px',
              background: '#f6ffed',
              borderRadius: 8,
              border: '1px solid #b7eb8f',
              display: 'inline-block',
            }}
          >
            <Space>
              <SaveOutlined style={{ color: '#52c41a' }} />
              <Text type="secondary">当前项目：</Text>
              {editingTitle ? (
                <Input
                  size="small"
                  defaultValue={currentProjectTitle}
                  style={{ width: 200 }}
                  onPressEnter={(e) => onUpdateTitle((e.target as HTMLInputElement).value)}
                  onBlur={(e) => onUpdateTitle(e.target.value)}
                  autoFocus
                />
              ) : (
                <Text strong>{currentProjectTitle}</Text>
              )}
              <Tooltip title="编辑项目名称">
                <Button type="text" size="small" icon={<EditOutlined />} onClick={onEditTitle} />
              </Tooltip>
              <Tooltip title="复制项目ID">
                <Button type="text" size="small" icon={<CopyOutlined />} onClick={onCopyProjectId} />
              </Tooltip>
            </Space>
          </div>
        )}
      </div>
    </Card>
  )
}
