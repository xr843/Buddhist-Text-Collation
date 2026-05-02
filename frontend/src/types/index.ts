/**
 * 类型定义 - MVP版本
 */

// 导出版本对勘模块类型
export * from './multiCollation'

// 导出校勘视图模块类型（排除与 multiCollation 重名的 InitialHighlight；
// 校勘视图组件内部使用时直接 import './collationView' 拿原始版）
export type {
  CollationViewData,
  CollationViewProps,
  DiffNavigation,
  CharSegment,
  CollationStatistics,
  AlignedSentence,
  SideBySideResult,
} from './collationView'

// 标点请求
export interface PunctuationRequest {
  text: string
  context?: string
}

// 标点响应
export interface PunctuationResponse {
  success: boolean
  punctuated_text: string
  model_used: string
  confidence: number
  processing_time: number
  tokens_used: number
}

// 文件内容提取响应
export interface FileExtractResponse {
  success: boolean
  text: string
  filename: string
  char_count: number
}

// 对比请求
export interface ComparisonRequest {
  text1: string
  text2: string
  version1_name?: string
  version2_name?: string
}

// 差异项
export interface Difference {
  type: 'insert' | 'delete' | 'replace' | 'equal'
  position: number
  text1: string
  text2: string
  context_before: string
  context_after: string
  text1_range: [number, number]
  text2_range: [number, number]
}

// 统计信息
export interface Statistics {
  text1_length: number
  text2_length: number
  total_differences: number
  insertions: number
  deletions: number
  replacements: number
}

// 对比响应
export interface ComparisonResponse {
  success: boolean
  version1_name: string
  version2_name: string
  differences: Difference[]
  statistics: Statistics
  similarity: number
}

// AI分析结果 - 版本信息
export interface VersionAnalysis {
  name: string
  score: number  // 0-100评分
  strengths: string[]  // 优点列表
  weaknesses: string[]  // 不足列表
}

// AI分析结果 - 推荐信息
export interface Recommendation {
  preferred_version: string  // "version1" | "version2" | "unknown"
  reason: string  // 推荐理由
}

// AI分析结果 - 结构化数据
export interface StructuredAnalysis {
  version1: VersionAnalysis
  version2: VersionAnalysis
  recommendation: Recommendation
}

// AI分析结果
export interface AIAnalysis {
  analysis: string  // AI生成的markdown格式分析文本
  model_used: string
  processing_time: number
  tokens_used: number
  structured_analysis?: StructuredAnalysis  // 结构化分析数据（可选，向后兼容）
}

// 标点差异项
export interface PunctuationDifference {
  id: number
  position: number  // 兼容性：等同于 position_v1
  position_v1: number  // 版本1中的位置
  position_v2: number  // 版本2中的位置
  character: string  // 版本1中的字符
  character_v2?: string  // 版本2中的字符
  version1_punct: string
  version2_punct: string
  context: string
  diff_type: string  // "新增标点" | "删除标点" | "替换标点"
  category: string   // "句号" | "逗号" | "引号" | "括号" | "其他"
  punctuation_name: string  // 具体的标点符号名称，如"逗号"、"顿号"、"分号"
}

// 差异分类统计
export interface CategoryStats {
  count: number
  items: PunctuationDifference[]
}

// 标点风格报告
export interface StyleReport {
  version1: {
    name: string
    total_punctuation: number
    punctuation_density: number
    punctuation_distribution: Record<string, number>
  }
  version2: {
    name: string
    total_punctuation: number
    punctuation_density: number
    punctuation_distribution: Record<string, number>
  }
}

// 标点研究统计
export interface ResearchStats {
  total_count: number           // 总差异数
  sentence_end_count: number    // 句末点号差异
  sentence_inner_count: number  // 句内点号差异
  mark_count: number            // 标号差异
}

// 上下文切片
export interface ContextSlice {
  id: number
  position: number
  character: string
  version1_context: string
  version2_context: string
  version1_punct: string
  version2_punct: string
  category: string
  diff_type: string
  punctuation_name: string
}

// 块内句子对（用于块内句子对齐）
export interface SentencePair {
  sentence1: string  // 版本1的句子
  sentence2: string  // 版本2的句子
  clean_start_pos: number
  clean_end_pos: number
  diff_positions: number[]
}

// 句子对齐（用于逐句对比视图）
export interface SentenceAlignment {
  id: number
  sentence1: string  // 版本1的句子（带标点）
  sentence2: string  // 版本2的句子（带标点）
  sentence_pairs?: SentencePair[]  // 块内句子对齐（可选）
  has_diff: boolean  // 该句子是否有标点差异
  // 兼容性字段
  diff_positions: number[]  // 差异位置列表（基于版本1）
  clean_start_pos: number  // 版本1的起始位置
  clean_end_pos: number    // 版本1的结束位置
  // 双向位置索引（新增）
  diff_positions_v1?: number[]  // 版本1中的差异位置
  diff_positions_v2?: number[]  // 版本2中的差异位置
  clean_start_pos_v1?: number  // 版本1纯文本的起始位置
  clean_start_pos_v2?: number  // 版本2纯文本的起始位置
  clean_end_pos_v1?: number    // 版本1纯文本的结束位置
  clean_end_pos_v2?: number    // 版本2纯文本的结束位置
}

// 标点分析结果
export interface PunctuationAnalysis {
  version1_name: string
  version2_name: string
  differences: PunctuationDifference[]
  categories: Record<string, CategoryStats>
  style_report: StyleReport
  context_slices: ContextSlice[]
  sentence_alignment: SentenceAlignment[]  // 句子级别对齐数据
  research_stats: ResearchStats  // 标点研究统计
}

// 标点对比响应（带AI分析）
export interface PunctuationComparisonResponse {
  success: boolean
  version1_name: string
  version2_name: string
  text1: string
  text2: string
  ai_analysis: AIAnalysis  // AI标点质量分析
  differences: Difference[]  // diff差异
  similarity: number  // 相似度
  punctuation_analysis: PunctuationAnalysis  // 标点分析工作台数据
}

// ==================== 标点判取与定本生成 ====================

// 标点判取结果
export interface PunctuationDecision {
  diffId: number           // 差异ID
  position: number         // 位置
  selectedVersion: 'version1' | 'version2'  // 采用的版本
  selectedPunct: string    // 采用的标点
  note?: string            // 备注
  createdAt?: string       // 创建时间
  updatedAt?: string       // 更新时间
}

// 标点改易记条目
export interface PunctuationChangeNote {
  position: number         // 位置
  context: string          // 上下文
  originalPunct: string    // 原标点
  changedPunct: string     // 改后标点
  changeType: string       // 改易类型：新增/删除/替换
  note?: string            // 备注
}

// 标点定本数据
export interface PunctuationDefinitiveData {
  text: string             // 定本文本
  notes: PunctuationChangeNote[]  // 标点改易记
  statistics: {
    total_decisions: number     // 判取总数
    applied_count: number       // 应用数量
    version1_adopted: number    // 采用版本1数量
    version2_adopted: number    // 采用版本2数量
    skipped_count: number       // 跳过数量
  }
  version1_name: string    // 版本1名称
  version2_name: string    // 版本2名称
}
