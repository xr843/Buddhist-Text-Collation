/**
 * 文字校勘视图常量
 */

/**
 * 默认分页大小
 */
export const DEFAULT_PAGE_SIZE = 50

/**
 * 分类颜色映射
 */
export const CATEGORY_COLORS = {
  variant: {
    bg: '#b7eb8f',
    text: '#135200',
    border: '#52c41a',
    label: '异体字',
  },
  error: {
    bg: '#ffa39e',
    text: '#a8071a',
    border: '#f5222d',
    label: '讹误',
  },
  yanwen: {
    bg: '#ffd591',
    text: '#ad4e00',
    border: '#fa8c16',
    label: '衍文',
  },
  tuowen: {
    bg: '#d3adf7',
    text: '#391085',
    border: '#722ed1',
    label: '脱文',
  },
} as const

/**
 * 差异类型边框颜色
 */
export const DIFF_TYPE_COLORS = {
  punct_only: '#1890ff',
  text_only: '#f5222d',
  mixed: '#722ed1',
  default: '#faad14',
} as const

/**
 * 差异类型标签
 */
export const DIFF_TYPE_LABELS = {
  punct_only: '标点差异',
  text_only: '文字差异',
  mixed: '混合差异',
  default: '文字差异',
} as const

/**
 * 获取分类颜色配置
 */
export function getCategoryColor(category: string | null | undefined) {
  if (category === 'variant') return CATEGORY_COLORS.variant
  if (category === 'error') return CATEGORY_COLORS.error
  if (category === 'yanwen') return CATEGORY_COLORS.yanwen
  if (category === 'tuowen') return CATEGORY_COLORS.tuowen
  return CATEGORY_COLORS.error // 默认使用讹误颜色
}

/**
 * 获取差异类型配置
 */
export function getDiffTypeConfig(diffType: string | null | undefined) {
  if (diffType === 'punct_only') {
    return {
      color: DIFF_TYPE_COLORS.punct_only,
      label: DIFF_TYPE_LABELS.punct_only,
    }
  }
  if (diffType === 'text_only') {
    return {
      color: DIFF_TYPE_COLORS.text_only,
      label: DIFF_TYPE_LABELS.text_only,
    }
  }
  if (diffType === 'mixed') {
    return {
      color: DIFF_TYPE_COLORS.mixed,
      label: DIFF_TYPE_LABELS.mixed,
    }
  }
  return {
    color: DIFF_TYPE_COLORS.default,
    label: DIFF_TYPE_LABELS.default,
  }
}

/**
 * 分类筛选选项
 */
export const CATEGORY_FILTER_OPTIONS = [
  { value: 'all', label: '全部' },
  { value: 'variant', label: '异体字' },
  { value: 'error', label: '讹误' },
  { value: 'yanwen', label: '衍文' },
  { value: 'tuowen', label: '脱文' },
] as const
