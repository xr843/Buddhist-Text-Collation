/**
 * 标点对比视图主组件
 * 显示两个版本文本的标点差异对比
 */

import { useMemo, useRef } from 'react'
import { Pagination } from 'antd'
import type { SentenceAlignment, PunctuationDifference } from '../../types'
import type { PositionMaps } from './types'
import { splitAlignmentIntoLines, buildPositionMaps } from './utils'
import { usePagination, useScrollToDiff, useViewMode } from './hooks'
import ControlBar from './ControlBar'
import CompareRow from './CompareRow'
import ColorHint from './ColorHint'

// 导出 Props 类型供外部使用
export interface PunctuationCompareViewProps {
  sentenceAlignment: SentenceAlignment[]
  differences: PunctuationDifference[]
  version1Name: string
  version2Name: string
  onDiffClick?: (diff: PunctuationDifference) => void
  scrollToDiffId?: number | null
}

export default function PunctuationCompareView({
  sentenceAlignment,
  differences,
  version1Name,
  version2Name,
  onDiffClick,
  scrollToDiffId,
}: PunctuationCompareViewProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // 视图模式管理
  const { diffOnlyMode, setDiffOnlyMode, charsPerLine, setCharsPerLine } = useViewMode()

  // 将对齐块拆分成固定字符数的行
  const splitLines = useMemo(
    () => splitAlignmentIntoLines(sentenceAlignment, charsPerLine),
    [sentenceAlignment, charsPerLine]
  )

  // 分页管理
  const { currentPage, setCurrentPage, filteredLines, paginatedData, pageSize } = usePagination(
    splitLines,
    diffOnlyMode
  )

  // 滚动到差异
  useScrollToDiff(
    scrollToDiffId,
    filteredLines,
    differences,
    diffOnlyMode,
    currentPage,
    setCurrentPage,
    scrollContainerRef as React.RefObject<HTMLDivElement>
  )

  // 构建位置到差异的映射
  const positionMaps: PositionMaps = useMemo(
    () => buildPositionMaps(differences),
    [differences]
  )

  return (
    <div
      style={{
        border: '1px solid #d9d9d9',
        borderRadius: 4,
        overflow: 'hidden',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* 高亮闪烁动画样式 */}
      <style>
        {`
          @keyframes highlight-flash {
            0%, 100% { box-shadow: none; }
            25%, 75% { box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.6); }
            50% { box-shadow: 0 0 0 5px rgba(24, 144, 255, 0.8); }
          }
        `}
      </style>

      {/* 表头 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '48px minmax(0, 1fr) minmax(0, 1fr)',
          borderBottom: '2px solid #d9d9d9',
          background: '#fafafa',
        }}
      >
        <div
          style={{
            padding: '12px 4px',
            borderRight: '2px solid #d9d9d9',
            fontWeight: 600,
            fontSize: 12,
            color: '#666',
            textAlign: 'center',
          }}
        >
          序号
        </div>
        <div
          style={{
            padding: '12px 16px',
            borderRight: '2px solid #d9d9d9',
            fontWeight: 600,
            fontSize: 14,
            color: '#000',
          }}
        >
          {version1Name}
        </div>
        <div
          style={{
            padding: '12px 16px',
            fontWeight: 600,
            fontSize: 14,
            color: '#000',
          }}
        >
          {version2Name}
        </div>
      </div>

      {/* 控制栏 */}
      <ControlBar
        diffOnlyMode={diffOnlyMode}
        charsPerLine={charsPerLine}
        filteredLinesCount={filteredLines.length}
        totalLinesCount={splitLines.length}
        onDiffOnlyModeChange={setDiffOnlyMode}
        onCharsPerLineChange={setCharsPerLine}
      />

      {/* 数据行 */}
      <div ref={scrollContainerRef} style={{ flex: 1, overflow: 'auto' }}>
        {paginatedData.map((line, index) => (
          <CompareRow
            key={line.id}
            line={line}
            index={index}
            positionMaps={positionMaps}
            scrollToDiffId={scrollToDiffId}
            onDiffClick={onDiffClick}
          />
        ))}
      </div>

      {/* 分页组件 */}
      {filteredLines.length > pageSize && (
        <div
          style={{
            padding: '12px 16px',
            borderTop: '1px solid #d9d9d9',
            textAlign: 'center',
            background: '#fafafa',
          }}
        >
          <Pagination
            current={currentPage}
            total={filteredLines.length}
            pageSize={pageSize}
            onChange={(page) => {
              setCurrentPage(page)
              scrollContainerRef.current?.scrollTo(0, 0)
            }}
            showSizeChanger={false}
            showQuickJumper
            showTotal={(total, range) => `第 ${range[0]}-${range[1]} 行，共 ${total} 行`}
          />
        </div>
      )}

      {/* 颜色提示 */}
      <ColorHint />
    </div>
  )
}
