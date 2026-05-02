/**
 * 版本对勘模块类型定义
 * 从 MultiCollation.tsx 中提取
 */

// ==================== 校勘结果相关类型 ====================

export interface CollationResult {
  collation_name: string
  collation_file: string
  char_count: number
  result: {
    mode: string
    mode_description: string
    version1_name: string
    version2_name: string
    statistics: any
    similarity: number
    aligned_sentences: any[]
    side_by_side: any
  }
}

export interface VariantTableRow {
  position: number
  context: string
  base_char: string
  coll_values: string[]
  category: string
}

export interface PhylogenyNode {
  name: string
  similarity?: number
  system?: string
  is_group?: boolean
  children: PhylogenyNode[]
}

/**
 * 共同异文详情项
 *
 * 后端历史上字段名变过：旧版返回 `shared_error_char`，新版改用 `shared_char`。
 * 这里两个都声明为可选，前端代码做 fallback：`detail.shared_error_char ?? detail.shared_char`
 */
export interface SharedErrorDetail {
  position: number
  base_char: string
  shared_error_char?: string
  shared_char?: string
  category?: string  // 仅 yantuo_details 用：'衍'/'脱' 等
}

export interface SharedErrors {
  names: string[]
  // 讹误（默认）
  matrix: number[][]
  details?: Record<string, SharedErrorDetail[]>
  total_by_version?: Record<string, number>
  // 异体字
  variant_matrix?: number[][]
  variant_details?: Record<string, SharedErrorDetail[]>
  variant_total_by_version?: Record<string, number>
  // 衍脱
  yantuo_matrix?: number[][]
  yantuo_details?: Record<string, SharedErrorDetail[]>
  yantuo_total_by_version?: Record<string, number>
}

// ==================== API 响应类型 ====================

export interface MultiCollationResponse {
  success: boolean
  mode: string
  mode_description: string
  processing_time: number
  base: {
    name: string
    file: string
    char_count: number
    text: string
  }
  collations: CollationResult[]
  summary: {
    base_name: string
    collation_names: string[]
    stats_table: {
      headers: string[]
      rows: {
        type: string
        type_key: string
        values: number[]
        total: number
      }[]
    }
  }
  variant_table?: {
    headers: string[]
    rows: VariantTableRow[]
    total: number
  }
  phylogeny?: {
    similarity_matrix: {
      names: string[]
      matrix: number[][]
      systems?: Record<string, string>
    }
    shared_errors?: SharedErrors
    tree: PhylogenyNode
    conclusions?: string[]
  }
  project?: {
    id: string
    title: string
    created_at: string
    updated_at: string
  }
}

// ==================== 项目管理类型 ====================

export interface ProjectSummary {
  id: string
  title: string
  description: string
  status: string
  created_at: string
  updated_at: string
  metadata: {
    base_name?: string
    collation_count?: number
    collation_names?: string[]
    variant_count?: number
    diff_total?: number
  }
}

export interface FullProject {
  id: string
  type: string
  title: string
  description: string
  status: string
  created_at: string
  updated_at: string
  metadata: any
  data: {
    base: MultiCollationResponse['base']
    collations: CollationResult[]
    summary: MultiCollationResponse['summary']
    variant_table: MultiCollationResponse['variant_table']
    phylogeny: MultiCollationResponse['phylogeny']
  }
}

// ==================== 校勘判取类型 ====================

export interface CollationDecision {
  position: number
  selectedText: string
  selectedVersion: string
  uncertain?: boolean
  note?: string
}

export interface VariantItem {
  position: number
  context: string
  base_char: string
  coll_values: string[]
  category: string
}

export interface DecidedNote {
  position: number
  context: string
  category: string
  base_char: string
  selectedText: string
  selectedVersion: string
  uncertain: boolean
  note: string
}

// ==================== 定本生成类型 ====================

export interface DefinitiveTextStatistics {
  total_positions: number
  decided_count: number
  uncertain_count: number
  applied_count: number
}

export interface CollationNote {
  position: number
  context: string
  base_char: string
  selected_char: string
  selected_version: string
  note?: string
}

export interface DefinitiveTextData {
  text: string
  notes: CollationNote[]
  statistics: DefinitiveTextStatistics
}

// ==================== UI 状态类型 ====================

export interface InitialHighlight {
  char: string
  collationIdx: number
}

export interface DragBounds {
  left: number
  top: number
  bottom: number
  right: number
}

// ==================== 版本系统展示顺序 ====================

export const SYSTEM_DISPLAY_ORDER: Record<string, number> = {
  '中系': 0,
  '南系': 1,
  '北系': 2,
  '未知': 3,
}
