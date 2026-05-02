/**
 * CollationView 组件类型定义
 */

export interface CharSegment {
  text: string
  type: string  // equal/delete/insert/replace
  is_punct: boolean  // 是否是标点符号
  category?: string | null  // variant/error/yanwen/tuowen (倒文已归入error)
}

export interface AlignedSentence {
  id: number
  type: string
  sentence1: string
  sentence2: string
  has_diff: boolean
  char_diff: {
    segments1: CharSegment[]
    segments2: CharSegment[]
    diff_type?: 'punct_only' | 'text_only' | 'mixed' | null  // 差异类型
  } | null
}

// 展示布局模式
export type DisplayMode = 'side-by-side' | 'inline' | 'changes-only'

// 异文分类筛选（倒文已归入讹误）
export type CategoryFilter = 'all' | 'variant' | 'error' | 'yanwen' | 'tuowen'

export interface DiffDetails {
  deleted: { char: string; count: number; category?: string }[]
  inserted: { char: string; count: number; category?: string }[]
  replaced: { from: string; to: string; count: number; category?: string; category_cn?: string }[]
  transposed?: { from: string; to: string; count: number; category?: string; category_cn?: string }[]
}

export interface CategoryStats {
  variant_chars: number    // 异体字数量
  error_chars: number      // 讹误数量（含倒文）
  yanwen_chars: number     // 衍文数量
  tuowen_chars: number     // 脱文数量
}

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

export interface SideBySideResult {
  segments: Array<{
    type: string  // equal/replace/delete/insert
    text1: string
    text2: string
  }>
  total_segments: number
}

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
  side_by_side?: SideBySideResult
}

export interface InitialHighlight {
  char: string  // 要定位的字符
  type?: 'replace' | 'delete' | 'insert'
}

export interface CollationViewProps {
  data: CollationViewData
  initialHighlight?: InitialHighlight
}

export interface DiffNavigation {
  type: 'replace' | 'delete' | 'insert'
  char?: string
  from?: string
  to?: string
  matchedRecords: AlignedSentence[]  // 所有匹配的记录
  currentIndex: number               // 当前查看的索引
}

export interface HighlightedChar {
  type: 'replace' | 'delete' | 'insert'
  char?: string
  from?: string
  to?: string
}
