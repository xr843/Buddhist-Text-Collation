/**
 * 文字校勘视图类型定义
 */

/**
 * 字符片段
 */
export interface CharSegment {
  text: string
  type: string  // equal/delete/insert/replace
  is_punct: boolean  // 是否是标点符号
  category?: string | null  // variant/error/yanwen/tuowen (倒文已归入error)
}

/**
 * 对齐句子
 */
export interface AlignedSentence {
  id: number
  type: string
  sentence1: string
  sentence2: string
  has_diff: boolean
  char_diff: {
    segments1: CharSegment[]
    segments2: CharSegment[]
    diff_type?: 'punct_only' | 'text_only' | 'mixed' | null
  } | null
}

/**
 * 差异详情
 */
export interface DiffDetails {
  deleted: { char: string; count: number; category?: string }[]
  inserted: { char: string; count: number; category?: string }[]
  replaced: { from: string; to: string; count: number; category?: string; category_cn?: string }[]
  transposed?: { from: string; to: string; count: number; category?: string; category_cn?: string }[]
}

/**
 * 分类统计
 */
export interface CategoryStats {
  variant_chars: number    // 异体字数量
  error_chars: number      // 讹误数量（含倒文）
  yanwen_chars: number     // 衍文数量
  tuowen_chars: number     // 脱文数量
}

/**
 * 统计信息
 */
export interface CollationStatistics {
  version1_length: number
  version2_length: number
  total_differences: number
  insertions: number
  deletions: number
  replacements: number
  inserted_chars: number
  deleted_chars: number
  replaced_chars: number
  total_changed_chars: number
  category_stats?: CategoryStats
  diff_details?: DiffDetails
}

/**
 * 并排对比片段
 */
export interface SideBySideSegment {
  type: string  // equal/replace/delete/insert
  text1: string
  text2: string
}

/**
 * 并排对比数据
 */
export interface SideBySideData {
  segments: SideBySideSegment[]
  total_segments: number
}

/**
 * 校勘视图数据
 */
export interface CollationViewData {
  mode: string
  mode_description: string
  version1_name: string
  version2_name: string
  processing_time?: number
  text1?: string
  text2?: string
  statistics: CollationStatistics
  similarity: number
  aligned_sentences?: AlignedSentence[]
  side_by_side?: SideBySideData
}

/**
 * 组件属性
 */
export interface CollationViewProps {
  data: CollationViewData
  initialHighlight?: {
    char: string
    type?: 'replace' | 'delete' | 'insert'
  }
}

/**
 * 展示布局模式
 */
export type DisplayMode = 'side-by-side' | 'inline' | 'changes-only'

/**
 * 异文分类筛选
 */
export type CategoryFilter = 'all' | 'variant' | 'error' | 'yanwen' | 'tuowen'

/**
 * 高亮字符状态
 */
export interface HighlightedChar {
  type: 'replace' | 'delete' | 'insert'
  char?: string
  from?: string
  to?: string
}

/**
 * 差异导航状态
 */
export interface DiffNavigation {
  type: 'replace' | 'delete' | 'insert'
  char?: string
  from?: string
  to?: string
  matchedRecords: AlignedSentence[]
  currentIndex: number
}
