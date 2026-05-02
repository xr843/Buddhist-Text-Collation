/**
 * 审核面板组件（合并版）
 * 右侧统一的差异审核面板
 */

import { Card, Button, Space, Tag, Progress, Input, Typography } from 'antd'
import {
  CloseOutlined,
  CheckOutlined,
  StarOutlined,
  EyeInvisibleOutlined,
  LeftOutlined,
  RightOutlined
} from '@ant-design/icons'
import type { PunctuationDifference } from '../types'

const { TextArea } = Input
const { Text } = Typography

interface ReviewPanelProps {
  difference: PunctuationDifference
  allDifferences: PunctuationDifference[]
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
  reviewStatus: boolean[]
  onReview: () => void
  onPrevious: () => void
  onNext: () => void
  onSkip: () => void
  onNoteChange: (note: string) => void
  onDifferenceSelect: (index: number) => void
  onClose: () => void
}

export default function ReviewPanel({
  difference,
  allDifferences: _allDifferences,
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
  reviewStatus: _reviewStatus,
  onReview,
  onPrevious,
  onNext,
  onSkip,
  onNoteChange,
  onDifferenceSelect: _onDifferenceSelect,
  onClose
}: ReviewPanelProps) {
  const getDiffClass = (type: string) => {
    if (type === '删除标点') return 'deleted'
    if (type === '新增标点') return 'added'
    if (type === '替换标点') return 'replaced'
    return 'none'
  }

  const renderContext = (version: 'A' | 'B') => {
    const punct = version === 'A' ? difference.version1_punct : difference.version2_punct
    const diffClass = getDiffClass(difference.diff_type)

    // 从完整上下文中提取一句话（简化版：取前后各30个字符作为一句）
    const contextStart = Math.max(0, 15 - 30)
    const contextEnd = Math.min(difference.context.length, 15 + 30)
    const sentenceContext = difference.context.substring(contextStart, contextEnd)

    // 计算标点在句子中的相对位置
    const punctPosition = 15 - contextStart

    return (
      <div className="panel-context">
        <span className="context-before">{sentenceContext.substring(0, punctPosition)}</span>
        <span className={`panel-diff ${diffClass}`}>{punct === '无' || !punct ? '∅' : punct}</span>
        <span className="context-after">{sentenceContext.substring(punctPosition)}</span>
      </div>
    )
  }

  return (
    <div className="review-panel">
      {/* 面板头部 */}
      <div className="panel-header">
        <div className="panel-title">🎯 差异审核</div>
        <Button
          type="text"
          icon={<CloseOutlined />}
          onClick={onClose}
          style={{ color: 'white' }}
        />
      </div>

      {/* 进度条 */}
      <div className="panel-progress">
        <div className="progress-info">
          <span>已审核 {reviewedCount} / {totalCount}</span>
          <span>{progress}%</span>
        </div>
        <Progress
          percent={progress}
          showInfo={false}
          strokeColor={{
            '0%': '#67C23A',
            '100%': '#85CE61'
          }}
        />
      </div>

      {/* 面板内容 */}
      <div className="panel-content">
        {/* 当前差异详情 */}
        <div style={{
          padding: 10,
          background: '#f5f5f5',
          borderRadius: 6,
          marginBottom: 10
        }}>
          <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
            当前差异 {currentIndex + 1} / {totalCount}
          </Text>

          {/* 标签 */}
          <Space wrap style={{ marginBottom: 8 }} size="small">
            <Tag color="orange" style={{ fontSize: 11 }}>🏷️ {difference.diff_type}</Tag>
            <Tag color="blue" style={{ fontSize: 11 }}>📍 {difference.category}</Tag>
            <Tag color="purple" style={{ fontSize: 11 }}>📌 位置：第{difference.position}字后</Tag>
          </Space>

          {/* 对比展示 */}
          <Card size="small" style={{ marginBottom: 8, background: 'white' }} bodyStyle={{ padding: 8 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              {/* 版本A */}
              <div>
                <div className="version-label" style={{ marginBottom: 4 }}>
                  <Tag color="blue" style={{ fontSize: 11 }}>{version1Name}</Tag>
                </div>
                {renderContext('A')}
              </div>

              {/* 版本B */}
              <div>
                <div className="version-label" style={{ marginBottom: 4 }}>
                  <Tag color="blue" style={{ fontSize: 11 }}>{version2Name}</Tag>
                </div>
                {renderContext('B')}
              </div>
            </Space>
          </Card>
        </div>

        {/* 操作按钮 */}
        <Space direction="vertical" style={{ width: '100%', marginBottom: 10 }} size="small">
          <Button
            type={isReviewed ? 'default' : 'primary'}
            block
            size="small"
            icon={<CheckOutlined />}
            onClick={onReview}
          >
            {isReviewed ? '已审核' : '标记为已审核'}
          </Button>
          <Button block size="small" icon={<StarOutlined />}>
            标记为重要
          </Button>
          <Button block size="small" icon={<EyeInvisibleOutlined />} onClick={onSkip}>
            忽略此差异
          </Button>
        </Space>

        {/* 备注 */}
        <div style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6 }}>
            📝 审核备注
          </div>
          <TextArea
            value={note}
            onChange={e => onNoteChange(e.target.value)}
            placeholder="记录审核意见..."
            rows={2}
            style={{ fontSize: 12 }}
          />
        </div>

        {/* 导航 */}
        <Space style={{ width: '100%' }} size="small">
          <Button
            icon={<LeftOutlined />}
            onClick={onPrevious}
            disabled={!canGoPrev}
            size="small"
            style={{ flex: 1 }}
          >
            上一个
          </Button>
          <Button onClick={onSkip} size="small" style={{ flex: 1 }}>
            跳过
          </Button>
          <Button
            type="primary"
            icon={<RightOutlined />}
            iconPosition="end"
            onClick={onNext}
            disabled={!canGoNext}
            size="small"
            style={{ flex: 1 }}
          >
            下一个
          </Button>
        </Space>
      </div>
    </div>
  )
}
