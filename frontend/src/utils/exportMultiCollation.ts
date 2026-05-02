/**
 * 版本对勘导出功能
 * 从 MultiCollation.tsx 中提取的导出相关逻辑
 */
import { message } from 'antd'
import type { MultiCollationResponse, CollationResult } from '../types/multiCollation'
import { parseVersionInfo } from './versionParser'

// ==================== 辅助函数 ====================

/**
 * 下载文件
 */
export function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 格式化日期
 */
export function formatDate(): string {
  return new Date().toISOString().slice(0, 10)
}

/**
 * 获取校本展示顺序
 */
export function getCollationDisplayOrder(names: string[]): number[] {
  const SYSTEM_DISPLAY_ORDER: Record<string, number> = {
    '中系': 0,
    '南系': 1,
    '北系': 2,
    '未知': 3,
  }

  return names
    .map((name, idx) => ({ idx, system: parseVersionInfo(name).system }))
    .sort((a, b) => {
      const sa = SYSTEM_DISPLAY_ORDER[a.system] ?? SYSTEM_DISPLAY_ORDER['未知']
      const sb = SYSTEM_DISPLAY_ORDER[b.system] ?? SYSTEM_DISPLAY_ORDER['未知']
      if (sa !== sb) return sa - sb
      return a.idx - b.idx
    })
    .map(({ idx }) => idx)
}

// ==================== 导出函数 ====================

/**
 * 导出汇总统计 CSV
 */
export function exportSummaryCSV(result: MultiCollationResponse): void {
  const BOM = '\uFEFF'
  const rows: string[] = []
  const { summary, base, collations, processing_time } = result

  // 标题
  rows.push('==================== 版本对勘汇总报告 ====================')
  rows.push('')

  // 基本信息
  rows.push('"项目","数值"')
  rows.push(`"底本","${base.name}"`)
  rows.push(`"底本字数","${base.char_count}"`)
  rows.push(`"校本数量","${collations.length}"`)
  rows.push(`"处理耗时","${processing_time}秒"`)
  rows.push('')

  // 各校本差异统计表
  rows.push('==================== 各校本差异统计 ====================')
  rows.push('')

  const order = getCollationDisplayOrder(summary.collation_names)

  // 表头
  const headers = ['版本信息', ...order.map(i => parseVersionInfo(summary.collation_names[i]).canon), '合计']
  rows.push(headers.map(h => `"${h}"`).join(','))

  // 数据行
  summary.stats_table.rows.forEach(row => {
    const rowData = [row.type, ...order.map(i => String(row.values[i])), String(row.total)]
    rows.push(rowData.map(d => `"${d}"`).join(','))
  })

  // 下载
  const csvContent = BOM + rows.join('\n')
  downloadFile(csvContent, `版本对勘_汇总统计_${formatDate()}.csv`, 'text/csv;charset=utf-8;')
  message.success('汇总统计已导出')
}

/**
 * 导出异文汇校表 CSV
 */
export function exportVariantTableCSV(result: MultiCollationResponse): void {
  if (!result?.variant_table) {
    message.warning('暂无异文汇校表数据')
    return
  }

  const BOM = '\uFEFF'
  const rows: string[] = []
  const { variant_table, base, summary } = result

  // 标题
  rows.push('==================== 异文汇校表 ====================')
  rows.push('')
  rows.push(`"底本","${base.name}"`)
  rows.push(`"异文总数","${variant_table.total}"`)
  rows.push('')

  const order = getCollationDisplayOrder(summary.collation_names)

  // 表头
  const headers = ['序号', '上下文', base.name, ...order.map(i => summary.collation_names[i]), '类型']
  rows.push(headers.map(h => `"${h}"`).join(','))

  // 数据行
  variant_table.rows.forEach((row, idx) => {
    const rowData = [
      String(idx + 1),
      row.context,
      row.base_char,
      ...order.map(i => row.coll_values[i]),
      row.category
    ]
    rows.push(rowData.map(d => `"${d}"`).join(','))
  })

  // 下载
  const csvContent = BOM + rows.join('\n')
  downloadFile(csvContent, `版本对勘_异文汇校表_${formatDate()}.csv`, 'text/csv;charset=utf-8;')
  message.success('异文汇校表已导出')
}

/**
 * 导出综合报告 CSV（包含所有数据）
 */
export function exportFullReportCSV(result: MultiCollationResponse): void {
  const BOM = '\uFEFF'
  const rows: string[] = []
  const { summary, base, collations, processing_time, variant_table } = result

  // ===== 第一部分：基本信息 =====
  rows.push('##################################################')
  rows.push('# 版本对勘综合报告')
  rows.push('##################################################')
  rows.push('')
  rows.push('"项目","数值"')
  rows.push(`"底本","${base.name}"`)
  rows.push(`"底本字数","${base.char_count}"`)
  rows.push(`"校本数量","${collations.length}"`)
  rows.push(`"处理耗时","${processing_time}秒"`)
  rows.push(`"导出时间","${new Date().toLocaleString('zh-CN')}"`)
  rows.push('')

  // ===== 第二部分：各校本差异统计 =====
  rows.push('##################################################')
  rows.push('# 各校本差异统计')
  rows.push('##################################################')
  rows.push('')

  const order = getCollationDisplayOrder(summary.collation_names)
  const headers2 = ['版本信息', ...order.map(i => parseVersionInfo(summary.collation_names[i]).canon), '合计']
  rows.push(headers2.map(h => `"${h}"`).join(','))

  summary.stats_table.rows.forEach(row => {
    const rowData = [row.type, ...order.map(i => String(row.values[i])), String(row.total)]
    rows.push(rowData.map(d => `"${d}"`).join(','))
  })
  rows.push('')

  // ===== 第三部分：异文汇校表 =====
  if (variant_table && variant_table.rows.length > 0) {
    rows.push('##################################################')
    rows.push('# 异文汇校表')
    rows.push('##################################################')
    rows.push('')
    rows.push(`"异文总数","${variant_table.total}"`)
    rows.push('')

    const vtHeaders = ['序号', '上下文', base.name, ...order.map(i => summary.collation_names[i]), '类型']
    rows.push(vtHeaders.map(h => `"${h}"`).join(','))

    variant_table.rows.forEach((row, idx) => {
      const rowData = [
        String(idx + 1),
        row.context,
        row.base_char,
        ...order.map(i => row.coll_values[i]),
        row.category
      ]
      rows.push(rowData.map(d => `"${d}"`).join(','))
    })
    rows.push('')
  }

  // ===== 第四部分：各校本详细统计 =====
  rows.push('##################################################')
  rows.push('# 各校本详细统计')
  rows.push('##################################################')
  rows.push('')

  collations.forEach((coll: CollationResult, idx: number) => {
    const stats = coll.result.statistics
    rows.push(`"校本 ${idx + 1}","${coll.collation_name}"`)
    rows.push(`"字数","${coll.char_count}"`)
    rows.push(`"相似度","${(coll.result.similarity * 100).toFixed(1)}%"`)

    if (stats.category_stats) {
      rows.push(`"异体字","${stats.category_stats.variant_chars}"`)
      rows.push(`"讹误","${stats.category_stats.error_chars}"`)
      rows.push(`"衍文","${stats.category_stats.yanwen_chars}"`)
      rows.push(`"脱文","${stats.category_stats.tuowen_chars}"`)
    }
    rows.push('')
  })

  // 下载
  const csvContent = BOM + rows.join('\n')
  downloadFile(csvContent, `版本对勘_综合报告_${formatDate()}.csv`, 'text/csv;charset=utf-8;')
  message.success('综合报告已导出')
}

/**
 * 导出全量对照表 CSV（包含所有字符位置，无论是否有异文）
 */
export function exportFullAlignmentTableCSV(result: MultiCollationResponse): void {
  if (!result?.collations || result.collations.length === 0) {
    message.warning('暂无校勘数据')
    return
  }

  const BOM = '\uFEFF'
  const rows: string[] = []
  const { base, collations, summary } = result

  // 标题
  rows.push('==================== 全量对照表 ====================')
  rows.push('')
  rows.push(`"底本","${base.name}"`)
  rows.push(`"底本字数","${base.char_count}"`)
  rows.push(`"校本数量","${collations.length}"`)
  rows.push('')

  const order = getCollationDisplayOrder(summary.collation_names)

  // 表头：位置 | 底本 | 校本1 | 校本2 | ... | 类型
  const headers = ['位置', base.name, ...order.map(i => summary.collation_names[i]), '类型']
  rows.push(headers.map(h => `"${h}"`).join(','))

  // 从第一个校本的 side_by_side 获取对齐数据作为基准
  // 然后合并所有校本的对应位置数据
  const baseText = base.text || ''

  // 构建全量对照数据
  // 使用底本文本的每个字符位置作为基准
  const alignmentData: Array<{
    position: number
    baseChar: string
    collValues: string[]
    category: string
  }> = []

  // 遍历底本的每个字符
  for (let pos = 0; pos < baseText.length; pos++) {
    const baseChar = baseText[pos]
    const collValues: string[] = []
    let category = '相同'

    // 从每个校本的对齐数据中找到对应位置的字符
    for (const orderIdx of order) {
      const coll = collations[orderIdx]
      if (!coll?.result?.side_by_side?.segments) {
        collValues.push(baseChar)
        continue
      }

      // 在 segments 中查找对应位置
      const segments = coll.result.side_by_side.segments
      let currentPos = 0
      let foundChar = ''
      let foundCategory = ''

      for (const seg of segments) {
        const text1 = seg.text1 || ''
        const text2 = seg.text2 || ''
        const segType = seg.type

        if (segType === 'equal') {
          // 相同部分
          for (let i = 0; i < text1.length; i++) {
            if (currentPos === pos) {
              foundChar = text2[i] || text1[i]
              foundCategory = '相同'
              break
            }
            currentPos++
          }
        } else if (segType === 'delete') {
          // 脱文：底本有，校本无
          for (let i = 0; i < text1.length; i++) {
            if (currentPos === pos) {
              foundChar = '□'  // 脱文标记
              foundCategory = '脱文'
              break
            }
            currentPos++
          }
        } else if (segType === 'insert') {
          // 衍文：底本无，校本有 - 不增加底本位置计数
          // 这些字符不对应底本的任何位置
        } else if (segType === 'replace') {
          // 替换
          const len1 = text1.length
          const len2 = text2.length
          for (let i = 0; i < len1; i++) {
            if (currentPos === pos) {
              if (i < len2) {
                foundChar = text2[i]
                // 判断是异体字还是讹误（简化判断）
                foundCategory = '异文'
              } else {
                foundChar = '□'
                foundCategory = '脱文'
              }
              break
            }
            currentPos++
          }
        }

        if (foundChar !== '') break
      }

      collValues.push(foundChar || baseChar)
      if (foundCategory && foundCategory !== '相同') {
        category = foundCategory
      }
    }

    // 检查是否所有校本都与底本相同
    const allSame = collValues.every(v => v === baseChar)
    if (allSame) {
      category = '相同'
    } else if (category === '相同') {
      category = '异文'
    }

    alignmentData.push({
      position: pos + 1,
      baseChar,
      collValues,
      category
    })
  }

  // 输出数据行
  alignmentData.forEach(item => {
    const rowData = [
      String(item.position),
      item.baseChar,
      ...item.collValues,
      item.category
    ]
    rows.push(rowData.map(d => `"${d}"`).join(','))
  })

  // 统计信息
  rows.push('')
  rows.push('==================== 统计 ====================')
  const sameCount = alignmentData.filter(d => d.category === '相同').length
  const diffCount = alignmentData.filter(d => d.category !== '相同').length
  rows.push(`"相同字数","${sameCount}"`)
  rows.push(`"异文字数","${diffCount}"`)
  rows.push(`"总字数","${alignmentData.length}"`)

  // 下载
  const csvContent = BOM + rows.join('\n')
  downloadFile(csvContent, `版本对勘_全量对照表_${formatDate()}.csv`, 'text/csv;charset=utf-8;')
  message.success('全量对照表已导出')
}

/**
 * 创建导出菜单项
 */
export function createExportMenuItems(result: MultiCollationResponse | null) {
  if (!result) return []

  return [
    {
      key: 'summary',
      label: '汇总统计',
      onClick: () => exportSummaryCSV(result),
    },
    {
      key: 'variant',
      label: '异文汇校表',
      onClick: () => exportVariantTableCSV(result),
    },
    {
      key: 'fullAlignment',
      label: '全量对照表',
      onClick: () => exportFullAlignmentTableCSV(result),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'full',
      label: '综合报告（全部）',
      onClick: () => exportFullReportCSV(result),
    },
  ]
}
