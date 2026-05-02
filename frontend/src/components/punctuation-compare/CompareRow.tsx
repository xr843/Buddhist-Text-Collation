/**
 * 对比行组件
 */

import type { PunctuationDifference, SplitLine, PositionMaps } from './types'
import SentenceRenderer from './SentenceRenderer'

interface CompareRowProps {
  line: SplitLine
  index: number
  positionMaps: PositionMaps
  scrollToDiffId?: number | null
  onDiffClick?: (diff: PunctuationDifference) => void
}

export default function CompareRow({
  line,
  index,
  positionMaps,
  scrollToDiffId,
  onDiffClick,
}: CompareRowProps) {
  // 斑马纹背景色
  const isEvenRow = index % 2 === 1
  const rowBgColor = line.hasDiff
    ? isEvenRow
      ? '#fff7e6'
      : '#fffbe6' // 有差异：淡橙色
    : isEvenRow
      ? '#f0f5ff'
      : '#ffffff' // 无差异：淡蓝色/白色
  const hoverBgColor = line.hasDiff ? '#ffe7ba' : '#d6e4ff'

  return (
    <div
      key={line.id}
      data-line-id={line.id}
      style={{
        display: 'grid',
        gridTemplateColumns: '48px minmax(0, 1fr) minmax(0, 1fr)',
        borderBottom: '1px solid #e8e8e8',
        background: rowBgColor,
        transition: 'background 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = hoverBgColor
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = rowBgColor
      }}
    >
      {/* 序号列 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRight: '1px solid #e8e8e8',
          background: line.hasDiff ? '#fa8c16' : '#f0f0f0',
          color: line.hasDiff ? '#fff' : '#666',
          fontWeight: 500,
          fontSize: 12,
          minHeight: 32,
        }}
        title={line.hasDiff ? `第 ${line.lineNumber} 行（有差异）` : `第 ${line.lineNumber} 行`}
      >
        {line.lineNumber}
      </div>

      {/* 版本1 */}
      <div
        style={{
          padding: '6px 10px',
          borderRight: '2px solid #e8e8e8',
          fontFamily: "'Noto Serif SC', serif",
          fontSize: 15,
          lineHeight: 1.6,
          wordBreak: 'break-all',
          overflowWrap: 'break-word',
          whiteSpace: 'pre-wrap',
          background: !line.text1 ? '#fff7e6' : 'transparent',
          minHeight: 32,
        }}
      >
        {line.text1 ? (
          <SentenceRenderer
            sentence={line.text1}
            cleanStartPos={line.startPosV1}
            version="version1"
            positionMaps={positionMaps}
            scrollToDiffId={scrollToDiffId}
            onDiffClick={onDiffClick}
          />
        ) : (
          <span style={{ color: '#999', fontStyle: 'italic', fontSize: 12 }}>(无)</span>
        )}
      </div>

      {/* 版本2 */}
      <div
        style={{
          padding: '6px 10px',
          fontFamily: "'Noto Serif SC', serif",
          fontSize: 15,
          lineHeight: 1.6,
          wordBreak: 'break-all',
          overflowWrap: 'break-word',
          whiteSpace: 'pre-wrap',
          background: !line.text2 ? '#fff7e6' : 'transparent',
          minHeight: 32,
        }}
      >
        {line.text2 ? (
          <SentenceRenderer
            sentence={line.text2}
            cleanStartPos={line.startPosV2}
            version="version2"
            positionMaps={positionMaps}
            scrollToDiffId={scrollToDiffId}
            onDiffClick={onDiffClick}
          />
        ) : (
          <span style={{ color: '#999', fontStyle: 'italic', fontSize: 12 }}>(无)</span>
        )}
      </div>
    </div>
  )
}
