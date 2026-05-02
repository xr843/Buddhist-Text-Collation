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
