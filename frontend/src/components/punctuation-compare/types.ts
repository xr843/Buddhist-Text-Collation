/**
 * 标点对比视图类型定义
 */

import type { SentenceAlignment, PunctuationDifference } from '../../types'

// 重新导出公共类型
export type { SentenceAlignment, PunctuationDifference }

/**
 * 组件属性
 */
export interface PunctuationCompareViewProps {
  sentenceAlignment: SentenceAlignment[]
  differences: PunctuationDifference[]
  version1Name: string
  version2Name: string
  onDiffClick?: (diff: PunctuationDifference) => void
  scrollToDiffId?: number | null
}

/**
 * 拆分后的行数据
 */
export interface SplitLine {
  id: string                 // 唯一ID
  lineNumber: number         // 全局行号
  alignmentId: number        // 原始对齐块ID
  text1: string              // 版本1文本片段
  text2: string              // 版本2文本片段
  startPosV1: number         // 版本1起始位置
  startPosV2: number         // 版本2起始位置
  diffPositionsV1: number[]  // 版本1差异位置
  diffPositionsV2: number[]  // 版本2差异位置
  hasDiff: boolean           // 是否包含差异
}

/**
 * 滚动目标
 */
export interface ScrollTarget {
  lineId: string
  page: number
}

/**
 * 位置映射
 */
export interface PositionMaps {
  positionToDiffMapV1: Map<number, PunctuationDifference>
  positionToDiffMapV2: Map<number, PunctuationDifference>
}
