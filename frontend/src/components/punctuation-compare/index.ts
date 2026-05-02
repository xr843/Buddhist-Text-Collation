/**
 * 标点对比视图模块
 * 导出所有公共组件和工具
 */

// 主组件
export { default } from './PunctuationCompareView'
export { default as PunctuationCompareView } from './PunctuationCompareView'

// 子组件
export { default as SentenceRenderer } from './SentenceRenderer'
export { default as ControlBar } from './ControlBar'
export { default as CompareRow } from './CompareRow'
export { default as ColorHint } from './ColorHint'

// 类型
export type {
  SplitLine,
  PositionMaps,
  ScrollTarget,
  PunctuationCompareViewProps,
} from './types'

// 常量
export {
  PAGE_SIZE,
  DIFF_ONLY_PAGE_SIZE,
  DEFAULT_CHARS_PER_LINE,
  PUNCT_COLORS,
  PUNCT_MARKS_REGEX,
  PUNCT_MARKS_RENDER_REGEX,
  getPunctuationColor,
} from './constants'

// 工具函数
export {
  getCleanLength,
  extractByCleanPos,
  splitAlignmentIntoLines,
  buildPositionMaps,
  findLineIndexForDiff,
} from './utils'

// Hooks
export {
  usePagination,
  useScrollToDiff,
  useViewMode,
} from './hooks'
