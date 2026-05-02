/**
 * 标点定本预览模态框
 * 用于展示标点定本生成结果，支持下载定本和标点改易记
 */
import { useRef, useState } from 'react'
import {
  Modal,
  Button,
  Alert,
  Row,
  Col,
  Card,
  Table,
  Typography,
  Statistic,
  Space,
  Tooltip,
  Tag,
} from 'antd'
import { DownloadOutlined, DragOutlined } from '@ant-design/icons'
import Draggable from 'react-draggable'
import type { DraggableData, DraggableEvent } from 'react-draggable'
import type { PunctuationDefinitiveData, PunctuationChangeNote } from '../types'

const { Text } = Typography

interface PunctuationDefinitiveModalProps {
  open: boolean
  data: PunctuationDefinitiveData | null
  projectTitle?: string
  onClose: () => void
  onDownloadText: () => void
  onDownloadNotes: () => void
}

export default function PunctuationDefinitiveModal({
  open,
  data,
  projectTitle,
  onClose,
  onDownloadText,
  onDownloadNotes,
}: PunctuationDefinitiveModalProps) {
  // 拖拽状态
  const [dragDisabled, setDragDisabled] = useState(true)
  const [bounds, setBounds] = useState({ left: 0, top: 0, bottom: 0, right: 0 })
  const dragRef = useRef<HTMLDivElement>(null)

  const onStartDrag = (_event: DraggableEvent, uiData: DraggableData) => {
    const { clientWidth, clientHeight } = window.document.documentElement
    const targetRect = dragRef.current?.getBoundingClientRect()
    if (!targetRect) return
    setBounds({
      left: -targetRect.left + uiData.x,
      right: clientWidth - (targetRect.right - uiData.x),
      top: -targetRect.top + uiData.y,
      bottom: clientHeight - (targetRect.bottom - uiData.y),
    })
  }

  // 改易记表格列配置
  const columns = [
    {
      title: '位置',
      dataIndex: 'position',
      key: 'position',
      width: 70,
      render: (pos: number) => <Tag color="purple">{pos}</Tag>,
    },
    {
      title: '改易类型',
      dataIndex: 'changeType',
      key: 'changeType',
      width: 80,
      render: (type: string) => {
        const colorMap: Record<string, string> = {
          '新增': 'green',
          '删除': 'red',
          '替换': 'orange',
        }
        return <Tag color={colorMap[type] || 'default'}>{type}</Tag>
      },
    },
    {
      title: '原标点',
      dataIndex: 'originalPunct',
      key: 'originalPunct',
      width: 80,
      render: (punct: string) => (
        <Text strong style={{ color: '#cf1322', fontSize: 16 }}>
          {punct || '∅'}
        </Text>
      ),
    },
    {
      title: '改后标点',
      dataIndex: 'changedPunct',
      key: 'changedPunct',
      width: 80,
      render: (punct: string) => (
        <Text strong style={{ color: '#389e0d', fontSize: 16 }}>
          {punct || '∅'}
        </Text>
      ),
    },
    {
      title: '上下文',
      dataIndex: 'context',
      key: 'context',
      ellipsis: true,
      render: (ctx: string) => (
        <Text type="secondary" style={{ fontSize: 12 }}>
          {ctx?.substring(0, 30) || '-'}
        </Text>
      ),
    },
    {
      title: '备注',
      dataIndex: 'note',
      key: 'note',
      width: 100,
      ellipsis: true,
      render: (note: string) => note || '-',
    },
  ]

  if (!data) return null

  return (
    <Modal
      title={
        <div
          style={{ cursor: 'move', width: '100%' }}
          onMouseOver={() => setDragDisabled(false)}
          onMouseOut={() => setDragDisabled(true)}
        >
          <Space>
            <span>标点定本预览</span>
            <Tooltip title="拖动标题栏可移动窗口">
              <DragOutlined style={{ color: '#999', fontSize: 12 }} />
            </Tooltip>
            {projectTitle && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                - {projectTitle}
              </Text>
            )}
          </Space>
        </div>
      }
      open={open}
      onCancel={onClose}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
        <Button
          key="download-notes"
          icon={<DownloadOutlined />}
          onClick={onDownloadNotes}
          disabled={!data.notes?.length}
        >
          下载标点改易记
        </Button>,
        <Button
          key="download"
          type="primary"
          icon={<DownloadOutlined />}
          onClick={onDownloadText}
        >
          下载标点定本
        </Button>,
      ]}
      width={900}
      modalRender={(modal) => (
        <Draggable
          disabled={dragDisabled}
          bounds={bounds}
          nodeRef={dragRef}
          onStart={(event, uiData) => onStartDrag(event, uiData)}
        >
          <div ref={dragRef}>{modal}</div>
        </Draggable>
      )}
    >
      {/* 统计信息 */}
      <Alert
        type="info"
        message="生成统计"
        description={
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="判取总数"
                value={data.statistics.total_decisions}
                suffix="条"
                valueStyle={{ fontSize: 16 }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title={`采用 ${data.version1_name}`}
                value={data.statistics.version1_adopted}
                suffix="处"
                valueStyle={{ fontSize: 16, color: '#1890ff' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title={`采用 ${data.version2_name}`}
                value={data.statistics.version2_adopted}
                suffix="处"
                valueStyle={{ fontSize: 16, color: '#52c41a' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="实际改动"
                value={data.statistics.applied_count}
                suffix="处"
                valueStyle={{ fontSize: 16, color: '#fa8c16' }}
              />
            </Col>
          </Row>
        }
        style={{ marginBottom: 16 }}
      />

      {/* 定本文本预览 */}
      <Card
        title="标点定本文本"
        size="small"
        style={{ marginBottom: 16 }}
        extra={
          <Text type="secondary">
            共 {data.text.length} 字
          </Text>
        }
      >
        <div
          style={{
            maxHeight: 200,
            overflow: 'auto',
            padding: 12,
            background: '#fafafa',
            borderRadius: 4,
            lineHeight: 1.8,
            fontSize: 14,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
          }}
        >
          {data.text}
        </div>
      </Card>

      {/* 标点改易记 */}
      {data.notes && data.notes.length > 0 && (
        <Card
          title={
            <Space>
              <span>标点改易记</span>
              <Tag color="blue">{data.notes.length} 条</Tag>
            </Space>
          }
          size="small"
        >
          <Table<PunctuationChangeNote>
            dataSource={data.notes}
            columns={columns}
            rowKey={(record, index) => `${record.position}-${index}`}
            size="small"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条改易`,
            }}
            scroll={{ y: 300 }}
          />
        </Card>
      )}
    </Modal>
  )
}
