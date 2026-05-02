/**
 * 标点迁移类型定义
 */

export interface TransferRequest {
  source_text: string
  target_text: string
  preserve_existing?: boolean
}

export interface TransferResponse {
  result_text: string
  transferred_count: number
  total_punctuation_count: number
  alignment_score: number
  warnings: string[]
}

export interface RemovePunctuationRequest {
  text: string
}

export interface RemovePunctuationResponse {
  result_text: string
  removed_count: number
}

export interface ExampleResponse {
  source: string
  target: string
}
