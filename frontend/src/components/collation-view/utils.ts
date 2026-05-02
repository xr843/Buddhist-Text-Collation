/**
 * 文字校勘视图工具函数
 */

import type {
  AlignedSentence,
  CharSegment,
  CollationStatistics,
} from './types'

/**
 * 根据分类筛选过滤对齐句子
 */
export function filterByCategory(
  sentences: AlignedSentence[] | undefined,
  categoryFilter: string
): AlignedSentence[] {
  if (!sentences) return []

  if (categoryFilter === 'all') {
    return sentences
  }

  return sentences.filter(record => {
    if (!record.has_diff || !record.char_diff) return false

    const segments1 = record.char_diff.segments1 || []
    const segments2 = record.char_diff.segments2 || []
    const allSegments = [...segments1, ...segments2]

    return allSegments.some(seg => {
      if (seg.type === 'equal') return false

      if (categoryFilter === 'variant') {
        return seg.category === 'variant'
      } else if (categoryFilter === 'error') {
        return seg.category === 'error'
      } else if (categoryFilter === 'yanwen') {
        return seg.category === 'yanwen' || seg.type === 'insert'
      } else if (categoryFilter === 'tuowen') {
        return seg.category === 'tuowen' || seg.type === 'delete'
      }
      return false
    })
  })
}

/**
 * 查找包含指定差异的记录
 */
export function findMatchedRecords(
  sentences: AlignedSentence[] | undefined,
  type: 'replace' | 'delete' | 'insert',
  char?: string,
  from?: string,
  to?: string
): AlignedSentence[] {
  if (!sentences) return []

  const matchedRecords: AlignedSentence[] = []

  for (const record of sentences) {
    if (!record.has_diff || !record.char_diff) continue

    const segments1 = record.char_diff.segments1 || []
    const segments2 = record.char_diff.segments2 || []

    let found = false

    if (type === 'replace' && from && to) {
      const hasFrom = segments1.some(s => s.type === 'replace' && s.text === from)
      const hasTo = segments2.some(s => s.type === 'replace' && s.text === to)
      found = hasFrom && hasTo
    } else if (type === 'delete' && char) {
      found = segments1.some(s => s.type === 'delete' && s.text === char)
    } else if (type === 'insert' && char) {
      found = segments2.some(s => s.type === 'insert' && s.text === char)
    }

    if (found) {
      matchedRecords.push(record)
    }
  }

  return matchedRecords
}

/**
 * 计算目标页码
 */
export function calculateTargetPage(
  targetIndex: number,
  pageSize: number
): number {
  return Math.floor(targetIndex / pageSize) + 1
}

/**
 * 滚动到指定记录
 */
export function scrollToRecord(recordId: number): void {
  setTimeout(() => {
    const element = document.getElementById(`aligned-row-${recordId}`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      element.style.animation = 'highlight-flash 1.5s ease-in-out'
      setTimeout(() => {
        element.style.animation = ''
      }, 1500)
    }
  }, 100)
}

/**
 * 导出 CSV 报告
 */
export function exportToCSV(
  statistics: CollationStatistics,
  similarity: number,
  version1Name: string,
  version2Name: string,
  processingTime?: number
): void {
  if (!statistics.diff_details) {
    return
  }

  const rows: string[] = []
  const BOM = '\uFEFF'

  // 统计摘要
  rows.push('==================== 统计摘要 ====================')
  rows.push('')
  rows.push('"项目","数值"')
  rows.push(`"底本（${version1Name}）字数","${statistics.version1_length}"`)
  rows.push(`"校本（${version2Name}）字数","${statistics.version2_length}"`)
  rows.push(`"总差异处数","${statistics.total_differences}"`)
  rows.push(`"文本相似度","${(similarity * 100).toFixed(1)}%"`)
  if (processingTime !== undefined) {
    rows.push(`"处理耗时","${processingTime}秒"`)
  }
  rows.push('')

  // 分类统计
  if (statistics.category_stats) {
    rows.push('==================== 校勘分类统计 ====================')
    rows.push('')
    rows.push('"分类","数量","说明"')
    rows.push(`"异体字","${statistics.category_stats.variant_chars}","同字异形，非错误"`)
    rows.push(`"讹误","${statistics.category_stats.error_chars}","非异体字的文字差异（含倒文）"`)
    rows.push(`"衍文","${statistics.category_stats.yanwen_chars}","校本有，底本无"`)
    rows.push(`"脱文","${statistics.category_stats.tuowen_chars}","底本有，校本无"`)
    rows.push('')
  }

  // 替换详情
  rows.push('==================== 替换详情 ====================')
  rows.push('')
  rows.push(`"序号","底本（${version1Name}）","校本（${version2Name}）","出现次数","分类"`)
  const replaced = statistics.diff_details.replaced || []
  if (replaced.length > 0) {
    replaced.forEach((item, idx) => {
      const category = item.category === 'variant' ? '异体字' : '讹误'
      rows.push(`"${idx + 1}","${item.from}","${item.to}","${item.count}","${category}"`)
    })
  } else {
    rows.push('"","（无替换）","","",""')
  }
  rows.push('')

  // 脱文详情
  rows.push(`==================== 脱文详情（底本有，校本无） ====================`)
  rows.push('')
  rows.push(`"序号","底本有/校本无","出现次数"`)
  const deleted = statistics.diff_details.deleted || []
  if (deleted.length > 0) {
    deleted.forEach((item, idx) => {
      rows.push(`"${idx + 1}","${item.char}","${item.count}"`)
    })
  } else {
    rows.push('"","（无脱文）",""')
  }
  rows.push('')

  // 衍文详情
  rows.push(`==================== 衍文详情（校本有，底本无） ====================`)
  rows.push('')
  rows.push(`"序号","校本有/底本无","出现次数"`)
  const inserted = statistics.diff_details.inserted || []
  if (inserted.length > 0) {
    inserted.forEach((item, idx) => {
      rows.push(`"${idx + 1}","${item.char}","${item.count}"`)
    })
  } else {
    rows.push('"","（无衍文）",""')
  }
  rows.push('')

  // 逐条差异记录
  rows.push('==================== 逐条差异记录 ====================')
  rows.push('')
  rows.push(`"序号","差异类型","底本文字","校本文字","分类"`)

  let diffIdx = 0

  // 替换记录
  replaced.forEach(item => {
    const category = item.category === 'variant' ? '异体字' : '讹误'
    for (let i = 0; i < item.count; i++) {
      diffIdx++
      rows.push(`"${diffIdx}","替换","${item.from}","${item.to}","${category}"`)
    }
  })

  // 脱文记录
  deleted.forEach(item => {
    for (let i = 0; i < item.count; i++) {
      diffIdx++
      rows.push(`"${diffIdx}","脱文","${item.char}","（无）","脱文"`)
    }
  })

  // 衍文记录
  inserted.forEach(item => {
    for (let i = 0; i < item.count; i++) {
      diffIdx++
      rows.push(`"${diffIdx}","衍文","（无）","${item.char}","衍文"`)
    }
  })

  // 倒文记录
  const transposed = statistics.diff_details.transposed || []
  transposed.forEach(item => {
    for (let i = 0; i < item.count; i++) {
      diffIdx++
      rows.push(`"${diffIdx}","讹误","${item.from}","${item.to}","讹误（倒文）"`)
    }
  })

  if (diffIdx === 0) {
    rows.push('"","（无差异）","","",""')
  }

  rows.push('')
  rows.push(`"说明：逐条差异记录共 ${diffIdx} 条"`)
  rows.push(`"分类说明：异体字=同字异形（非错误），讹误=非异体字的文字差异（含倒文），脱文=底本有校本无，衍文=校本有底本无"`)

  // 生成下载
  const csvContent = BOM + rows.join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `文字校勘报告_底本vs校本_${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 获取字符高亮样式
 */
export function getCharHighlightStyle(
  segment: CharSegment
): { bgColor: string; color: string } {
  if (segment.type === 'equal') {
    return { bgColor: 'transparent', color: 'inherit' }
  }

  if (segment.is_punct) {
    // 标点差异：蓝色系弱高亮
    return { bgColor: '#e6f7ff', color: '#096dd9' }
  }

  // 文字差异：根据 category 使用不同颜色
  if (segment.category === 'variant') {
    return { bgColor: '#b7eb8f', color: '#135200' }
  } else if (segment.category === 'error') {
    return { bgColor: '#ffa39e', color: '#a8071a' }
  } else if (segment.category === 'yanwen' || segment.type === 'insert') {
    return { bgColor: '#ffd591', color: '#ad4e00' }
  } else if (segment.category === 'tuowen' || segment.type === 'delete') {
    return { bgColor: '#d3adf7', color: '#391085' }
  }

  // 默认（replace 无 category）：红色
  return { bgColor: '#ffa39e', color: '#a8071a' }
}
