/**
 * 版本谱系分析 - 工具函数
 */
import { KNOWN_CANONS } from './constants'
import type { SharedErrors, SharedErrorDetail, VariantType } from './types'

/**
 * 创建版本名称简化器（工厂函数）
 */
export function createVersionNameSimplifier(maxLen: number) {
  return function simplifyVersionName(fullName: string): string {
    // 优先从名称中提取已知藏经名称
    for (const canon of KNOWN_CANONS) {
      if (fullName.includes(canon)) {
        return canon.slice(0, maxLen)
      }
    }

    // 匹配【系●藏名】或【系●藏名版】格式，提取藏经核心名称
    const bracketMatch = fullName.match(/【([^】]+)】/)
    if (bracketMatch) {
      const innerText = bracketMatch[1]
      const parts = innerText.split(/[●•·]/)

      if (parts.length > 1) {
        let versionName = parts[1].trim()

        // 移除末尾的"版"字
        if (versionName.endsWith('版')) {
          versionName = versionName.slice(0, -1)
        }

        if (versionName.length > maxLen) {
          return versionName.slice(0, maxLen) + '…'
        }
        return versionName
      }
    }

    // 清理无效内容
    const cleaned = fullName
      .replace(/【[^】]*】/g, '')
      .replace(/《[^》]*》/g, '')
      .replace(/[（(][^）)]*[）)]/g, '')
      .replace(/卷\d+/g, '')
      .replace(/第\d+卷/g, '')
      .replace(/底本|校本|对校本|參校本/g, '')
      .replace(/[-_—]/g, '')
      .replace(/^\d+/, '')
      .trim()

    if (cleaned && cleaned.length > 0) {
      return cleaned.slice(0, maxLen)
    }

    return fullName.slice(0, maxLen)
  }
}

/**
 * 按字符数换行文本
 */
export function wrapTextByChars(text: string, charsPerLine: number): string {
  const value = String(text ?? '')
  if (!charsPerLine || charsPerLine <= 0 || value.length <= charsPerLine) return value
  const chunks: string[] = []
  for (let i = 0; i < value.length; i += charsPerLine) {
    chunks.push(value.slice(i, i + charsPerLine))
  }
  return chunks.join('\n')
}

/**
 * 合并不同类型的variant details
 */
export function mergeVariantDetails(
  shared_errors: SharedErrors,
  variantType: VariantType
): Record<string, SharedErrorDetail[]> | undefined {
  if (variantType === 'error') {
    return shared_errors.details
  }

  if (variantType === 'variant') {
    return shared_errors.variant_details
  }

  if (variantType === 'yantuo') {
    return shared_errors.yantuo_details
  }

  // combined: 合并所有 details
  const details: Record<string, SharedErrorDetail[]> = { ...shared_errors.details }
  const sources = [shared_errors.variant_details, shared_errors.yantuo_details]

  for (const source of sources) {
    if (!source) continue
    for (const [key, value] of Object.entries(source)) {
      if (details[key]) {
        details[key] = [...details[key], ...value]
      } else {
        details[key] = value
      }
    }
  }

  return details
}

/**
 * 获取类型中文名
 */
export function getTypeName(type: string): string {
  const typeNames: Record<string, string> = {
    error: '讹误',
    variant: '异体字',
    yantuo: '衍脱',
    tuowen: '脱文',
    yanwen: '衍文',
  }
  return typeNames[type] || '异文'
}

/**
 * 获取当前类型的矩阵
 */
export function getMatrixByType(shared_errors: SharedErrors, variantType: VariantType): number[][] {
  switch (variantType) {
    case 'error':
      return shared_errors.matrix
    case 'variant':
      return shared_errors.variant_matrix || shared_errors.matrix
    case 'yantuo':
      return shared_errors.yantuo_matrix || shared_errors.matrix
    case 'combined':
      return shared_errors.combined_matrix || shared_errors.matrix
    default:
      return shared_errors.matrix
  }
}

/**
 * 获取当前类型的总数统计
 */
export function getTotalByVersionForType(
  shared_errors: SharedErrors,
  variantType: VariantType
): Record<string, number> {
  switch (variantType) {
    case 'error':
      return shared_errors.total_by_version || {}
    case 'variant':
      return shared_errors.variant_total_by_version || {}
    case 'yantuo':
      return shared_errors.yantuo_total_by_version || {}
    case 'combined':
      return shared_errors.combined_total_by_version || {}
    default:
      return {}
  }
}
