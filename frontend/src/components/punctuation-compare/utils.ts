/**
 * 标点对比视图工具函数
 */

import type { SentenceAlignment, PunctuationDifference, SplitLine, PositionMaps } from './types'
import { PUNCT_MARKS_REGEX } from './constants'

/**
 * 获取文本的纯字符长度（不含标点和空白）
 */
export function getCleanLength(text: string): number {
  if (!text) return 0
  let count = 0
  for (const char of text) {
    if (!PUNCT_MARKS_REGEX.test(char) && !/\s/.test(char)) {
      count++
    }
  }
  return count
}

/**
 * 从文本中按纯文本位置提取片段
 * @param text 原始文本
 * @param startCleanPos 起始纯文本位置
 * @param endCleanPos 结束纯文本位置
 */
export function extractByCleanPos(text: string, startCleanPos: number, endCleanPos: number): string {
  if (!text) return ''
  let result = ''
  let cleanIndex = 0
  let started = false

  for (let i = 0; i < text.length; i++) {
    const char = text[i]
    const isPunct = PUNCT_MARKS_REGEX.test(char) || /\s/.test(char)

    if (!isPunct) {
      // 非标点字符
      if (cleanIndex >= startCleanPos && cleanIndex < endCleanPos) {
        started = true
        result += char
      }
      cleanIndex++
      if (cleanIndex >= endCleanPos) {
        // 收集紧跟的标点
        let j = i + 1
        while (j < text.length && (PUNCT_MARKS_REGEX.test(text[j]) || /\s/.test(text[j]))) {
          result += text[j]
          j++
        }
        break
      }
    } else {
      // 标点字符：如果已经开始收集，则包含进去
      if (started) {
        result += char
      } else if (cleanIndex === startCleanPos) {
        // 起始位置的前置标点也要包含
        result += char
      }
    }
  }

  return result
}

/**
 * 将对齐块拆分成固定字符数的行
 */
export function splitAlignmentIntoLines(
  sentenceAlignment: SentenceAlignment[],
  charsPerLine: number
): SplitLine[] {
  const lines: SplitLine[] = []
  let lineNumber = 1

  sentenceAlignment.forEach(alignment => {
    const text1 = alignment.sentence1 || ''
    const text2 = alignment.sentence2 || ''
    const startPosV1 = alignment.clean_start_pos_v1 ?? alignment.clean_start_pos
    const startPosV2 = alignment.clean_start_pos_v2 ?? alignment.clean_start_pos
    const diffPosV1 = alignment.diff_positions_v1 ?? alignment.diff_positions ?? []
    const diffPosV2 = alignment.diff_positions_v2 ?? alignment.diff_positions ?? []

    const cleanLen1 = getCleanLength(text1)
    const cleanLen2 = getCleanLength(text2)
    const maxCleanLen = Math.max(cleanLen1, cleanLen2)

    if (maxCleanLen === 0) {
      // 空文本块
      lines.push({
        id: `${alignment.id}-0`,
        lineNumber: lineNumber++,
        alignmentId: alignment.id,
        text1: text1,
        text2: text2,
        startPosV1: startPosV1,
        startPosV2: startPosV2,
        diffPositionsV1: diffPosV1,
        diffPositionsV2: diffPosV2,
        hasDiff: diffPosV1.length > 0 || diffPosV2.length > 0,
      })
      return
    }

    // 按固定字符数拆分，两边同步
    let currentCleanStart = 0
    let lineIndex = 0

    while (currentCleanStart < maxCleanLen) {
      const currentCleanEnd = Math.min(currentCleanStart + charsPerLine, maxCleanLen)

      // 提取两边对应位置的文本
      const lineText1 = extractByCleanPos(text1, currentCleanStart, currentCleanEnd)
      const lineText2 = extractByCleanPos(text2, currentCleanStart, currentCleanEnd)

      const lineStartPosV1 = startPosV1 + currentCleanStart
      const lineStartPosV2 = startPosV2 + currentCleanStart
      const lineEndPosV1 = startPosV1 + currentCleanEnd
      const lineEndPosV2 = startPosV2 + currentCleanEnd

      // 筛选出属于这一行的差异位置
      const lineDiffPosV1 = diffPosV1.filter(pos =>
        pos >= lineStartPosV1 && pos < lineEndPosV1
      )
      const lineDiffPosV2 = diffPosV2.filter(pos =>
        pos >= lineStartPosV2 && pos < lineEndPosV2
      )

      const hasDiff = lineDiffPosV1.length > 0 || lineDiffPosV2.length > 0

      lines.push({
        id: `${alignment.id}-${lineIndex}`,
        lineNumber: lineNumber++,
        alignmentId: alignment.id,
        text1: lineText1,
        text2: lineText2,
        startPosV1: lineStartPosV1,
        startPosV2: lineStartPosV2,
        diffPositionsV1: lineDiffPosV1,
        diffPositionsV2: lineDiffPosV2,
        hasDiff,
      })

      currentCleanStart = currentCleanEnd
      lineIndex++
    }
  })

  return lines
}

/**
 * 构建位置到差异的映射
 */
export function buildPositionMaps(differences: PunctuationDifference[]): PositionMaps {
  const mapV1 = new Map<number, PunctuationDifference>()
  const mapV2 = new Map<number, PunctuationDifference>()

  differences.forEach((diff) => {
    // 版本1位置映射
    const posV1 = diff.position_v1 ?? diff.position
    mapV1.set(posV1, diff)

    // 版本2位置映射
    const posV2 = diff.position_v2 ?? diff.position
    mapV2.set(posV2, diff)
  })

  return { positionToDiffMapV1: mapV1, positionToDiffMapV2: mapV2 }
}

/**
 * 分页数据
 */
export function paginateLines(
  lines: SplitLine[],
  currentPage: number,
  pageSize: number
): SplitLine[] {
  const startIndex = (currentPage - 1) * pageSize
  const endIndex = startIndex + pageSize
  return lines.slice(startIndex, endIndex)
}

/**
 * 查找差异所在的行索引
 */
export function findLineIndexForDiff(
  lines: SplitLine[],
  diff: PunctuationDifference
): number {
  const diffPosition = diff.position_v1 ?? diff.position

  return lines.findIndex(line => {
    const lineTextClean = line.text1?.replace(PUNCT_MARKS_REGEX, '').replace(/\s/g, '') || ''
    return (
      diffPosition >= line.startPosV1 &&
      diffPosition < line.startPosV1 + lineTextClean.length
    )
  })
}
