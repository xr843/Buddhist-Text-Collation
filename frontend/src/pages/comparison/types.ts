/**
 * 标点对比模块类型定义
 */

import type {
  PunctuationComparisonResponse,
  PunctuationDifference,
  PunctuationDecision,
  PunctuationDefinitiveData,
} from '../../types'

// 重新导出公共类型
export type {
  PunctuationComparisonResponse,
  PunctuationDifference,
  PunctuationDecision,
  PunctuationDefinitiveData,
}

/**
 * 项目摘要
 */
export interface ProjectSummary {
  id: string
  title: string
  description: string
  status: string
  created_at: string
  updated_at: string
  metadata: {
    version1_name?: string
    version2_name?: string
    total_differences?: number
  }
}

/**
 * 项目列表响应
 */
export interface ProjectListResponse {
  items?: ProjectSummary[]
  total?: number
}

/**
 * 项目详情响应
 */
export interface ProjectDetailResponse {
  project: {
    id: string
    title: string
    data: {
      result: PunctuationComparisonResponse
    }
  }
}

/**
 * 判取状态
 */
export interface DecisionState {
  decisions: Record<number, PunctuationDecision>
  decisionCount: number
}

/**
 * 审核状态
 */
export interface ReviewState {
  reviewStatus: boolean[]
  currentDiffIndex: number
  reviewedCount: number
  reviewProgress: number
}

/**
 * 差异过滤器状态
 */
export interface FilterState {
  selectedCategories: string[]
  filteredDifferences: PunctuationDifference[]
}
