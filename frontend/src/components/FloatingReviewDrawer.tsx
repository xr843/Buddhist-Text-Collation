/**
 * 浮动审核抽屉组件
 * 可拖拽、可最小化的差异审核面板
 */
import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Card,
  Button,
  Space,
  Tag,
  Progress,
  Input,
  Typography,
  Tooltip,
} from 'antd'
import {
  CloseOutlined,
  CheckOutlined,
  StarOutlined,
  EyeInvisibleOutlined,
  LeftOutlined,
  RightOutlined,
  DragOutlined,
  MinusOutlined,
  ExpandOutlined,
  PushpinOutlined,
  PushpinFilled,
} from '@ant-design/icons'
import type { PunctuationDifference, PunctuationDecision } from '../types'
import './FloatingReviewDrawer.css'

const { TextArea } = Input
const { Text } = Typography

interface FloatingReviewDrawerProps {
  visible: boolean
  difference: PunctuationDifference | null
  currentIndex: number
  totalCount: number
  reviewedCount: number
  progress: number
  isReviewed: boolean
  note: string
  version1Name: string
  version2Name: string
  canGoPrev: boolean
  canGoNext: boolean
  onReview: () => void
  onPrevious: () => void
  onNext: () => void
  onSkip: () => void
  onNoteChange: (note: string) => void
  onClose: () => void
  // 判取功能（可选）
  decisionMode?: boolean                    // 是否启用判取模式
  currentDecision?: PunctuationDecision | null  // 当前差异的判取结果
  decisionCount?: number                    // 已判取数量
  onDecision?: (version: 'version1' | 'version2', note?: string) => void  // 判取回调
}

export default function FloatingReviewDrawer({
  visible,
  difference,
  currentIndex,
  totalCount,
  reviewedCount,
  progress,
  isReviewed,
  note,
  version1Name,
  version2Name,
  canGoPrev,
  canGoNext,
  onReview,
  onPrevious,
  onNext,
  onSkip,
  onNoteChange,
  onClose,
  // 判取功能
  decisionMode = false,
  currentDecision = null,
  decisionCount = 0,
  onDecision,
}: FloatingReviewDrawerProps) {
  // 拖拽状态
  const [position, setPosition] = useState({ x: 0, y: 100 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })

  // 最小化状态
  const [isMinimized, setIsMinimized] = useState(false)

  // 固定状态（固定后不可拖拽）
  const [isPinned, setIsPinned] = useState(false)

  const drawerRef = useRef<HTMLDivElement>(null)

  // 初始化位置（右侧）
  useEffect(() => {
    if (visible && drawerRef.current) {
      const savedPosition = localStorage.getItem('floatingReviewDrawerPosition')
      if (savedPosition) {
        try {
          const parsed = JSON.parse(savedPosition)
          setPosition(parsed)
        } catch {
          // 默认位置：右侧
          setPosition({
            x: window.innerWidth - 380,
            y: 100,
          })
        }
      } else {
        setPosition({
          x: window.innerWidth - 380,
          y: 100,
        })
      }
    }
  }, [visible])

  // 保存位置到 localStorage
  useEffect(() => {
    if (!isDragging && position.x !== 0) {
      localStorage.setItem('floatingReviewDrawerPosition', JSON.stringify(position))
    }
  }, [position, isDragging])

  // 拖拽开始
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (isPinned) return
    if ((e.target as HTMLElement).closest('.no-drag')) return

    setIsDragging(true)
    setDragOffset({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    })
    e.preventDefault()
  }, [isPinned, position])

  // 拖拽移动
  useEffect(() => {
    if (!isDragging) return

    const handleMouseMove = (e: MouseEvent) => {
      const newX = Math.max(0, Math.min(window.innerWidth - 360, e.clientX - dragOffset.x))
      const newY = Math.max(0, Math.min(window.innerHeight - 100, e.clientY - dragOffset.y))
      setPosition({ x: newX, y: newY })
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging, dragOffset])

  // 获取差异类型样式
  const diffClassMap: Record<string, string> = {
    '删除标点': 'deleted',
    '新增标点': 'added',
    '替换标点': 'replaced',
  }
  const getDiffClass = (type: string): string => diffClassMap[type] ?? 'none'

  // 渲染上下文
  const renderContext = (version: 'A' | 'B') => {
    if (!difference) return null

    const punct = version === 'A' ? difference.version1_punct : difference.version2_punct
    const diffClass = getDiffClass(difference.diff_type)

    const contextEnd = Math.min(difference.context.length, 45)
    const sentenceContext = difference.context.substring(0, contextEnd)
    const punctPosition = 15

    return (
      <div className="floating-drawer-context">
        <span className="context-before">{sentenceContext.substring(0, punctPosition)}</span>
        <span className={`floating-drawer-diff ${diffClass}`}>
          {punct === '无' || !punct ? '∅' : punct}
        </span>
        <span className="context-after">{sentenceContext.substring(punctPosition)}</span>
      </div>
    )
  }

  if (!visible) return null

  return (
    <div
      ref={drawerRef}
      className={`floating-review-drawer ${isMinimized ? 'minimized' : ''} ${isDragging ? 'dragging' : ''} ${isPinned ? 'pinned' : ''}`}
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      {/* 标题栏（可拖拽区域） */}
      <div
        className="floating-drawer-header"
        onMouseDown={handleMouseDown}
      >
        <div className="floating-drawer-title">
          {!isPinned && <DragOutlined style={{ marginRight: 8, opacity: 0.5 }} />}
          <span>差异审核</span>
          <Tag color="blue" style={{ marginLeft: 8 }}>
            {currentIndex + 1}/{totalCount}
          </Tag>
        </div>
        <Space className="no-drag" size={4}>
          <Tooltip title={isPinned ? '取消固定' : '固定位置'}>
            <Button
              type="text"
              size="small"
              icon={isPinned ? <PushpinFilled /> : <PushpinOutlined />}
              onClick={() => setIsPinned(!isPinned)}
              style={{ color: isPinned ? '#1890ff' : 'inherit' }}
            />
          </Tooltip>
          <Tooltip title={isMinimized ? '展开' : '最小化'}>
            <Button
              type="text"
              size="small"
              icon={isMinimized ? <ExpandOutlined /> : <MinusOutlined />}
              onClick={() => setIsMinimized(!isMinimized)}
            />
          </Tooltip>
          <Tooltip title="关闭">
            <Button
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={onClose}
            />
          </Tooltip>
        </Space>
      </div>

      {/* 最小化时只显示进度 */}
      {isMinimized ? (
        <div className="floating-drawer-minimized">
          <Progress
            percent={progress}
            size="small"
            showInfo={false}
            strokeColor="#52c41a"
          />
          <Text type="secondary" style={{ fontSize: 12 }}>
            已审核 {reviewedCount}/{totalCount}
          </Text>
        </div>
      ) : (
        /* 完整内容 */
        <div className="floating-drawer-content no-drag">
          {/* 进度条 */}
          <div className="floating-drawer-progress">
            <div className="progress-info">
              <span>已审核 {reviewedCount}/{totalCount}</span>
              <span>{progress}%</span>
            </div>
            <Progress
              percent={progress}
              showInfo={false}
              strokeColor={{ '0%': '#52c41a', '100%': '#73d13d' }}
              size="small"
            />
          </div>

          {difference ? (
            <>
              {/* 差异详情 */}
              <div className="floating-drawer-detail">
                {/* 标签 */}
                <Space wrap size={4} style={{ marginBottom: 8 }}>
                  <Tag color="orange">{difference.diff_type}</Tag>
                  <Tag color="blue">{difference.category}</Tag>
                  <Tag color="purple">位置: {difference.position}</Tag>
                </Space>

                {/* 对比展示 */}
                <Card size="small" bodyStyle={{ padding: 8 }}>
                  <Space direction="vertical" style={{ width: '100%' }} size={8}>
                    <div>
                      <Tag color="blue" style={{ marginBottom: 4 }}>{version1Name}</Tag>
                      {renderContext('A')}
                    </div>
                    <div>
                      <Tag color="green" style={{ marginBottom: 4 }}>{version2Name}</Tag>
                      {renderContext('B')}
                    </div>
                  </Space>
                </Card>
              </div>

              {/* 操作按钮 */}
              <div className="floating-drawer-actions">
                {decisionMode && onDecision ? (
                  /* 判取模式：显示版本选择按钮 */
                  <>
                    <div style={{ marginBottom: 8 }}>
                      <Text strong style={{ fontSize: 12, color: '#666' }}>
                        选择采用的标点版本：
                      </Text>
                      {currentDecision && (
                        <Tag color="green" style={{ marginLeft: 8 }}>
                          已判取: {currentDecision.selectedVersion === 'version1' ? version1Name : version2Name}
                        </Tag>
                      )}
                    </div>
                    <Space style={{ width: '100%' }} size={8}>
                      <Button
                        type={currentDecision?.selectedVersion === 'version1' ? 'primary' : 'default'}
                        size="small"
                        style={{ flex: 1 }}
                        onClick={() => onDecision('version1', note)}
                      >
                        采用 {version1Name}
                        <br />
                        <span style={{ fontSize: 16, fontWeight: 'bold' }}>
                          {difference?.version1_punct === '无' || !difference?.version1_punct ? '∅' : difference?.version1_punct}
                        </span>
                      </Button>
                      <Button
                        type={currentDecision?.selectedVersion === 'version2' ? 'primary' : 'default'}
                        size="small"
                        style={{ flex: 1 }}
                        onClick={() => onDecision('version2', note)}
                      >
                        采用 {version2Name}
                        <br />
                        <span style={{ fontSize: 16, fontWeight: 'bold' }}>
                          {difference?.version2_punct === '无' || !difference?.version2_punct ? '∅' : difference?.version2_punct}
                        </span>
                      </Button>
                    </Space>
                    <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
                      已判取 {decisionCount}/{totalCount} 条
                    </div>
                  </>
                ) : (
                  /* 审核模式：显示原有按钮 */
                  <>
                    <Button
                      type={isReviewed ? 'default' : 'primary'}
                      block
                      size="small"
                      icon={<CheckOutlined />}
                      onClick={onReview}
                    >
                      {isReviewed ? '已审核 ✓' : '标记已审核'}
                    </Button>
                    <Space style={{ width: '100%', marginTop: 8 }} size={4}>
                      <Button size="small" icon={<StarOutlined />} style={{ flex: 1 }}>
                        重要
                      </Button>
                      <Button size="small" icon={<EyeInvisibleOutlined />} onClick={onSkip} style={{ flex: 1 }}>
                        忽略
                      </Button>
                    </Space>
                  </>
                )}
              </div>

              {/* 备注 */}
              <div className="floating-drawer-note">
                <Text strong style={{ fontSize: 12 }}>备注</Text>
                <TextArea
                  value={note}
                  onChange={e => onNoteChange(e.target.value)}
                  placeholder="记录审核意见..."
                  rows={2}
                  size="small"
                  style={{ marginTop: 4 }}
                />
              </div>

              {/* 导航 */}
              <div className="floating-drawer-nav">
                <Button
                  icon={<LeftOutlined />}
                  onClick={onPrevious}
                  disabled={!canGoPrev}
                  size="small"
                >
                  上一个
                </Button>
                <Button
                  type="primary"
                  icon={<RightOutlined />}
                  iconPosition="end"
                  onClick={onNext}
                  disabled={!canGoNext}
                  size="small"
                >
                  下一个
                </Button>
              </div>
            </>
          ) : (
            <div style={{ padding: 20, textAlign: 'center', color: '#999' }}>
              点击对比视图中的差异开始审核
            </div>
          )}
        </div>
      )}
    </div>
  )
}
