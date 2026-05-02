/**
 * 并排对比视图组件
 * 左右分屏显示两个版本的文本，差异标记可点击
 */

import { Row, Col, Card, Checkbox } from 'antd'
import type { PunctuationDifference } from '../types'

interface SideBySideViewProps {
  differences: PunctuationDifference[]
  version1Name: string
  version2Name: string
  text1: string
  text2: string
  currentIndex: number
  reviewStatus: boolean[]
  selectedDiffs: Set<number>
  onDiffClick: (index: number) => void
  onCheckboxChange: (index: number, checked: boolean) => void
}

export default function SideBySideView({
  differences,
  version1Name,
  version2Name,
  text1: _text1,
  text2: _text2,
  currentIndex,
  reviewStatus,
  selectedDiffs,
  onDiffClick,
  onCheckboxChange
}: SideBySideViewProps) {
  const getDiffClass = (type: string) => {
    if (type === '删除标点') return 'deleted'
    if (type === '新增标点') return 'added'
    if (type === '替换标点') return 'replaced'
    return 'none'
  }

  // 构建带差异标记的文本
  const buildAnnotatedText = (version: 'A' | 'B') => {
    const segments: JSX.Element[] = []

    differences.forEach((diff, index) => {
      const punct = version === 'A' ? diff.version1_punct : diff.version2_punct
      const diffClass = getDiffClass(diff.diff_type)
      const isCurrent = index === currentIndex
      const isReviewed = reviewStatus[index]
      const isSelected = selectedDiffs.has(index)

      // 添加前置文本（简化处理，实际应该根据position计算）
      // 这里为了演示，直接使用context
      segments.push(
        <span key={`text-${index}`}>
          {diff.context.substring(0, 15)}
        </span>
      )

      // 添加差异标记
      segments.push(
        <span
          key={`diff-${index}`}
          id={`diff-${index}-${version.toLowerCase()}`}
          className={`diff-marker ${diffClass} ${isCurrent ? 'current' : ''} ${isReviewed ? 'reviewed' : ''} ${isSelected ? 'selected' : ''}`}
          onClick={() => onDiffClick(index)}
          title="点击查看详情"
          style={{ position: 'relative', cursor: 'pointer' }}
        >
          {/* 复选框 */}
          <Checkbox
            checked={isSelected}
            onChange={e => {
              e.stopPropagation()
              onCheckboxChange(index, e.target.checked)
            }}
            style={{
              position: 'absolute',
              left: -20,
              top: '50%',
              transform: 'translateY(-50%)',
              opacity: isSelected ? 1 : 0
            }}
            className="diff-checkbox"
          />
          {punct || '无'}
          {isReviewed && <span style={{ marginLeft: 4, color: '#67C23A' }}>✓</span>}
        </span>
      )

      // 添加后置文本
      segments.push(
        <span key={`after-${index}`}>
          {diff.context.substring(15)}
          。
        </span>
      )
    })

    return <div className="version-content">{segments}</div>
  }

  return (
    <div className="side-by-side-view">
      <Row gutter={1} style={{ height: '100%' }}>
        {/* 版本A */}
        <Col span={12}>
          <Card
            title={`版本A - ${version1Name}`}
            style={{ height: '100%' }}
            bodyStyle={{ overflow: 'auto', maxHeight: 'calc(100vh - 300px)' }}
          >
            {buildAnnotatedText('A')}
          </Card>
        </Col>

        {/* 版本B */}
        <Col span={12}>
          <Card
            title={`版本B - ${version2Name}`}
            style={{ height: '100%' }}
            bodyStyle={{ overflow: 'auto', maxHeight: 'calc(100vh - 300px)' }}
          >
            {buildAnnotatedText('B')}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
