/**
 * 标点对比模块常量
 */

/**
 * API 基础地址
 */
export const API_BASE = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').trim()

/**
 * 标点分类
 */
export const PUNCTUATION_CATEGORIES = ['句末点号', '句内点号', '标号'] as const

/**
 * 分类显示配置
 */
export const CATEGORY_DISPLAY: Record<string, string> = {
  '句末点号': '（。？）',
  '句内点号': '（，、；：）',
  '标号': '（《》""）',
}

/**
 * 句末点号字符
 */
export const SENTENCE_END_PUNCTS = '。？！?!'

/**
 * 句内点号字符
 */
export const SENTENCE_INNER_PUNCTS = '，、；：,;:'

/**
 * 获取标点分类
 */
export function getCategoryForPunct(char: string): string | null {
  if (SENTENCE_END_PUNCTS.includes(char)) return '句末点号'
  if (SENTENCE_INNER_PUNCTS.includes(char)) return '句内点号'
  return '标号'
}
