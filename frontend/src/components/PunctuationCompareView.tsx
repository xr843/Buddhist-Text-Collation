/**
 * 标点对比视图组件
 *
 * 此文件现在是一个转发模块，实际实现已移至 ./punctuation-compare/ 目录
 * 保留此文件以保持向后兼容性
 */

// 导出默认组件
export { default } from './punctuation-compare'

// 导出命名组件
export {
  PunctuationCompareView,
  SentenceRenderer,
  ControlBar,
  CompareRow,
  ColorHint,
} from './punctuation-compare'

// 导出类型
export type {
  SplitLine,
  PositionMaps,
  ScrollTarget,
  PunctuationCompareViewProps,
} from './punctuation-compare'

// 导出常量
export {
  PAGE_SIZE,
  DIFF_ONLY_PAGE_SIZE,
  DEFAULT_CHARS_PER_LINE,
  PUNCT_COLORS,
  getPunctuationColor,
} from './punctuation-compare'

// 导出工具函数
export {
  getCleanLength,
  extractByCleanPos,
  splitAlignmentIntoLines,
  buildPositionMaps,
} from './punctuation-compare'

// 导出 Hooks
export {
  usePagination,
  useScrollToDiff,
  useViewMode,
} from './punctuation-compare'
