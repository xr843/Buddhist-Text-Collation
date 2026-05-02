/**
 * 标点对比模块入口
 */

// 默认导出主页面组件
export { default } from './ComparisonPage'

// 导出子组件
export { default as PageHeader } from './PageHeader'
export { default as ProjectDrawer } from './ProjectDrawer'
export { default as StatisticsCard } from './StatisticsCard'
export { default as CompareWorkspace } from './CompareWorkspace'
export { default as KeyboardHints } from './KeyboardHints'

// 导出类型
export * from './types'

// 导出常量
export * from './constants'

// 导出 API 服务
export * from './api'

// 导出 Hooks
export * from './hooks'

// 导出工具函数
export { exportComparisonReport } from './exportUtils'
