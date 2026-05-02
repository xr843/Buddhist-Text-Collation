/**
 * 版本谱系分析模块
 *
 * 此模块已重构为子组件结构：
 * - constants.ts: 常量定义
 * - types.ts: 类型定义
 * - utils.ts: 工具函数
 * - SimilarityHeatmap.tsx: 相似度热力图
 * - SimilarityTable.tsx: 相似度数值表
 * - SharedErrorHeatmap.tsx: 共同异文热力图
 * - PhylogenyTree.tsx: 谱系树
 * - ErrorDetailsTable.tsx: 异文详情表格
 */

export { default } from './PhylogenyAnalysis'

// 导出子组件
export { default as SimilarityHeatmap } from './SimilarityHeatmap'
export { default as SimilarityTable } from './SimilarityTable'
export { default as SharedErrorHeatmap } from './SharedErrorHeatmap'
export { default as PhylogenyTree, SystemInfoCard } from './PhylogenyTree'
export { default as ErrorDetailsTable, VersionTotalTable } from './ErrorDetailsTable'

// 导出常量
export * from './constants'

// 导出类型
export * from './types'

// 导出工具函数
export * from './utils'
