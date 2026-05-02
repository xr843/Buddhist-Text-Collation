/**
 * 标点版本对比页面 - 转发模块
 *
 * 此文件已重构为模块化结构，实际实现位于 ./comparison/ 目录
 * 保留此文件以维护向后兼容性
 *
 * @module Comparison
 * @see ./comparison/
 */

// 默认导出主页面组件
export { default } from './comparison'

// 导出子组件
export {
  PageHeader,
  ProjectDrawer,
  StatisticsCard,
  CompareWorkspace,
  KeyboardHints,
} from './comparison'

// 导出类型
export type {
  ProjectSummary,
  ProjectListResponse,
  ProjectDetailResponse,
  DecisionState,
  ReviewState,
  FilterState,
} from './comparison'

// 导出常量
export {
  API_BASE,
  PUNCTUATION_CATEGORIES,
  CATEGORY_DISPLAY,
  SENTENCE_END_PUNCTS,
  SENTENCE_INNER_PUNCTS,
  getCategoryForPunct,
} from './comparison'

// 导出 Hooks
export {
  useProjectManager,
  useDecisionManager,
  useReviewNavigation,
  useDifferenceFilter,
  useFileCompare,
} from './comparison'

// 导出 API 服务
export {
  fetchProjectList,
  fetchProject,
  deleteProject,
  updateProjectTitle,
  fetchDecisions,
  saveDecisions,
  generateDefinitive,
  compareFiles,
} from './comparison'

// 导出工具函数
export { exportComparisonReport } from './comparison'
