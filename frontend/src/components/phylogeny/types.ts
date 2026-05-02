/**
 * 版本谱系分析 - 类型定义
 */

export interface PhylogenyNode {
  name: string
  similarity?: number
  system?: string
  is_group?: boolean
  children: PhylogenyNode[]
}

export interface SimilarityMatrix {
  names: string[]
  matrix: number[][]
  systems?: Record<string, string>
}

export interface SharedErrorDetail {
  position: number | string
  base_char: string
  shared_char?: string
  shared_error_char?: string
  category?: string
}

export interface SharedErrors {
  names: string[]
  matrix: number[][]
  details?: Record<string, SharedErrorDetail[]>
  total_by_version?: Record<string, number>
  variant_matrix?: number[][]
  variant_details?: Record<string, SharedErrorDetail[]>
  variant_total_by_version?: Record<string, number>
  yantuo_matrix?: number[][]
  yantuo_details?: Record<string, SharedErrorDetail[]>
  yantuo_total_by_version?: Record<string, number>
  combined_matrix?: number[][]
  combined_total_by_version?: Record<string, number>
}

export interface PhylogenyData {
  similarity_matrix: SimilarityMatrix
  shared_errors?: SharedErrors
  tree: PhylogenyNode
  conclusions?: string[]
}

export interface PhylogenyAnalysisProps {
  data: PhylogenyData
  baseName?: string
  projectId?: string | null
}

export type VariantType = 'error' | 'variant' | 'yantuo' | 'combined'

// ==================== 版本源流图 / Lineage Graph ====================

/**
 * 单个版本节点
 */
export interface LineageNode {
  id: string
  name: string
  year: number | string
  system?: string
  city?: string
  period?: string
  is_ancestor?: boolean
}

/**
 * 版本之间的传承关系（有向边）
 */
export interface LineageEdge {
  source: string
  target: string
  confidence: number
  similarity?: number
  shared_errors?: number
  evidence?: string[]
  is_known?: boolean
}

/**
 * 版本源流图完整数据
 */
export interface LineageData {
  nodes: LineageNode[]
  edges: LineageEdge[]
  conclusions?: string[]
}
