/**
 * 版本对勘类型定义
 */

import type { CollationDecision, VariantItem } from '../../components/CollationDecisionModal'

// 重新导出公共类型
export type { CollationDecision, VariantItem }

/**
 * 校勘结果
 */
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

/**
 * 异文表行
 */
export interface VariantTableRow {
  position: number
  context: string
  base_char: string
  coll_values: string[]
  category: string
}

/**
 * 版本谱系节点
 */
export interface PhylogenyNode {
  name: string
  similarity?: number
  system?: string
  is_group?: boolean
  children: PhylogenyNode[]
}

/**
 * 共同错误
 */
export interface SharedErrors {
  names: string[]
  matrix: number[][]
  details?: Record<string, Array<{
    position: number
    base_char: string
    shared_error_char: string
  }>>
  total_by_version?: Record<string, number>
}

/**
 * 版本谱系数据
 */
export interface PhylogenyData {
  similarity_matrix: {
    names: string[]
    matrix: number[][]
    systems?: Record<string, string>
  }
  shared_errors?: SharedErrors
  tree: PhylogenyNode
  conclusions?: string[]
}

/**
 * 多版本校勘响应
 */
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
  phylogeny?: PhylogenyData
  project?: {
    id: string
    title: string
    created_at: string
    updated_at: string
  }
}

/**
 * 项目摘要（用于列表）
 */
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

/**
 * 完整项目（用于加载）
 */
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

/**
 * 定本数据
 */
export interface DefinitiveTextData {
  text: string
  notes: string
  statistics: {
    total_decisions: number
    certain_decisions: number
    uncertain_decisions: number
    remaining_variants: number
  }
}

/**
 * 初始高亮定位
 */
export interface InitialHighlight {
  char: string
  collationIdx: number
}

/**
 * 已判取记录（用于列表显示）
 */
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
