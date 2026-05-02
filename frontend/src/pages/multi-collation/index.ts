/**
 * 版本对勘模块
 * 导出所有公共类型、常量、工具函数和 Hooks
 */

// 类型
export type {
  CollationResult,
  VariantTableRow,
  PhylogenyNode,
  SharedErrors,
  PhylogenyData,
  MultiCollationResponse,
  ProjectSummary,
  FullProject,
  DefinitiveTextData,
  InitialHighlight,
  DecidedNote,
  CollationDecision,
  VariantItem,
} from './types'

// 常量
export {
  API_BASE,
  MAX_COLLATION_FILES,
  DEFAULT_PAGE_SIZE,
  SYSTEM_COLORS,
  MAX_SUTRA_NAME_LENGTH,
  SYSTEM_DISPLAY_ORDER,
  getCollationDisplayOrder,
  CATEGORY_COLORS,
  CATEGORY_LABELS,
} from './constants'

// API 服务
export {
  fetchProjectList,
  fetchProject,
  deleteProject,
  updateProjectTitle,
  fetchDecisions,
  saveDecisions,
  deleteDecision,
  generateDefinitiveText,
  addCollations,
  removeCollations,
  performCollation,
} from './api'

// 工具函数
export {
  createUploadFileFromText,
  downloadTextFile,
  copyToClipboard,
  getVersionHeaderInfo,
  getVariantRowByPosition,
  scrollToVariantRow,
  buildDecidedNotes,
  filterDecidedNotes,
  exportSummaryCSV,
  exportVariantTableCSV,
} from './utils'

// Hooks
export {
  useProjectManager,
  useDecisionManager,
  useVariantNavigation,
  useCollationOrder,
} from './hooks'
