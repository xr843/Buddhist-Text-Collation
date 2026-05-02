/**
 * 标点对比视图常量
 */

/**
 * 全文模式每页行数
 */
export const PAGE_SIZE = 30

/**
 * 仅差异模式每页行数
 */
export const DIFF_ONLY_PAGE_SIZE = 40

/**
 * 默认每行字符数
 */
export const DEFAULT_CHARS_PER_LINE = 60

/**
 * 标点符号正则（匹配全角、半角、各类引号括号）
 */
export const PUNCT_MARKS_REGEX = /[。，、；：？！""''（）《》【】「」『』:;,?!＂＇〈〉〝〞〟｢｣‚„‹›«»〔〕〖〗]/

/**
 * 标点符号正则（用于渲染）
 */
export const PUNCT_MARKS_RENDER_REGEX = /[。，、；：？！\u201c\u201d\u2018\u2019\"'（）《》【】「」『』:;,?!＂＇〈〉〝〞〟｢｣\u201a\u201e‹›«»〔〕〖〗]/

/**
 * 标点颜色映射
 */
export const PUNCT_COLORS = {
  // 句末点号：深红色
  sentenceEnd: '#c62828',
  // 句内点号：蓝色
  sentenceInner: '#1565c0',
  // 标号：紫色
  mark: '#7b1fa2',
} as const

/**
 * 句末点号字符集
 */
export const SENTENCE_END_PUNCTS = '。？！?!'

/**
 * 句内点号字符集
 */
export const SENTENCE_INNER_PUNCTS = '，、；：,;:'

/**
 * 获取标点符号对应的颜色
 */
export function getPunctuationColor(punct: string): string {
  // 句末点号：红色
  if (SENTENCE_END_PUNCTS.includes(punct)) {
    return PUNCT_COLORS.sentenceEnd
  }
  // 句内点号：蓝色
  if (SENTENCE_INNER_PUNCTS.includes(punct)) {
    return PUNCT_COLORS.sentenceInner
  }
  // 标号：紫色
  return PUNCT_COLORS.mark
}

/**
 * 高亮闪烁动画样式
 */
export const HIGHLIGHT_ANIMATION_CSS = `
  @keyframes highlight-flash {
    0%, 100% { box-shadow: none; }
    25%, 75% { box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.6); }
    50% { box-shadow: 0 0 0 5px rgba(24, 144, 255, 0.8); }
  }
`
