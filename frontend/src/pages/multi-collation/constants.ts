/**
 * 版本对勘常量
 */

import {
  MAX_COLLATION_FILES as MAX_FILES,
  DEFAULT_PAGE_SIZE as PAGE_SIZE,
  SYSTEM_COLORS as COLORS,
  MAX_SUTRA_NAME_LENGTH,
} from '../../constants/multiCollation'
import { parseVersionInfo } from '../../utils/versionParser'

// 重新导出常量
export { MAX_FILES as MAX_COLLATION_FILES }
export { PAGE_SIZE as DEFAULT_PAGE_SIZE }
export { COLORS as SYSTEM_COLORS }
export { MAX_SUTRA_NAME_LENGTH }

/**
 * API 基础地址（使用 Vite 代理，留空使用相对路径）
 */
export const API_BASE = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').trim()

/**
 * 版本系统展示顺序：中系 → 南系 → 北系 → 未知
 */
export const SYSTEM_DISPLAY_ORDER: Record<string, number> = {
  '中系': 0,
  '南系': 1,
  '北系': 2,
  '未知': 3,
}

/**
 * 获取校本展示顺序
 */
export const getCollationDisplayOrder = (names: string[]): number[] =>
  names
    .map((name, idx) => ({ idx, system: parseVersionInfo(name).system }))
    .sort((a, b) => {
      const sa = SYSTEM_DISPLAY_ORDER[a.system] ?? SYSTEM_DISPLAY_ORDER['未知']
      const sb = SYSTEM_DISPLAY_ORDER[b.system] ?? SYSTEM_DISPLAY_ORDER['未知']
      if (sa !== sb) return sa - sb
      return a.idx - b.idx
    })
    .map(({ idx }) => idx)

/**
 * 异文分类颜色
 */
export const CATEGORY_COLORS: Record<string, string> = {
  '异体字': '#52c41a',
  '讹误': '#f5222d',
  '衍文': '#faad14',
  '脱文': '#722ed1',
}

/**
 * 异文分类标签
 */
export const CATEGORY_LABELS: Record<string, string> = {
  variant: '异体字',
  error: '讹误',
  yanwen: '衍文',
  tuowen: '脱文',
}
