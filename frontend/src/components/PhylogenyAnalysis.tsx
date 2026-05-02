/**
 * 版本谱系分析组件 - 转发模块
 *
 * 此文件已重构为模块化结构，实际实现位于 ./phylogeny/ 目录
 * 保留此文件以维护向后兼容性
 *
 * @module PhylogenyAnalysis
 * @see ./phylogeny/
 */

// 默认导出主组件
export { default } from './phylogeny'

// 导出子组件
export {
  SimilarityHeatmap,
  SimilarityTable,
  SharedErrorHeatmap,
  PhylogenyTree,
  SystemInfoCard,
  ErrorDetailsTable,
  VersionTotalTable,
} from './phylogeny'

// 导出常量
export {
  SYSTEM_COLORS,
  KNOWN_CANONS,
  SIMILARITY_COLOR_SCHEME,
  VARIANT_TYPE_CONFIG,
  CATEGORY_COLOR_MAP,
} from './phylogeny'

// 导出类型
export type {
  PhylogenyNode,
  SimilarityMatrix,
  SharedErrors,
  SharedErrorDetail,
  PhylogenyData,
  PhylogenyAnalysisProps,
  VariantType,
} from './phylogeny'

// 导出工具函数
export {
  createVersionNameSimplifier,
  wrapTextByChars,
  mergeVariantDetails,
  getTypeName,
  getTotalByVersionForType,
} from './phylogeny'
