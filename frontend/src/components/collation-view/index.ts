/**
 * 文字校勘视图模块
 * 导出所有公共类型、常量、工具函数和 Hooks
 */

// 类型
export type {
  CharSegment,
  AlignedSentence,
  DiffDetails,
  CategoryStats,
  CollationStatistics,
  SideBySideSegment,
  SideBySideData,
  CollationViewData,
  CollationViewProps,
  DisplayMode,
  CategoryFilter,
  HighlightedChar,
  DiffNavigation,
} from './types'

// 常量
export {
  DEFAULT_PAGE_SIZE,
  CATEGORY_COLORS,
  DIFF_TYPE_COLORS,
  DIFF_TYPE_LABELS,
  getCategoryColor,
  getDiffTypeConfig,
  CATEGORY_FILTER_OPTIONS,
} from './constants'

// 工具函数
export {
  filterByCategory,
  findMatchedRecords,
  calculateTargetPage,
  scrollToRecord,
  exportToCSV,
  getCharHighlightStyle,
} from './utils'

// Hooks
export {
  usePagination,
  useViewMode,
  useDiffNavigation,
  useInitialHighlight,
  useFilteredData,
} from './hooks'
