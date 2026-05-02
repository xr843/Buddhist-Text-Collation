/**
 * 报告导出工具
 */

import { message } from 'antd'
import type { PunctuationComparisonResponse } from './types'

/**
 * 导出标点对比报告（CSV格式）
 */
export function exportComparisonReport(result: PunctuationComparisonResponse) {
  const { punctuation_analysis } = result
  const differences = punctuation_analysis?.differences || []
  const stats = punctuation_analysis?.research_stats
  const styleReport = punctuation_analysis?.style_report

  // CSV 内容构建
  const rows: string[] = []

  // 添加 BOM 以支持 Excel 正确识别 UTF-8
  const BOM = '\uFEFF'

  // ===== 第一部分：基本信息 =====
  rows.push('==================== 基本信息 ====================')
  rows.push(`"版本A","${result.version1_name}"`)
  rows.push(`"版本B","${result.version2_name}"`)
  rows.push(`"分析时间","${new Date().toLocaleString('zh-CN')}"`)
  rows.push(`"文本相似度","${(result.similarity * 100).toFixed(2)}%"`)
  rows.push('')

  // ===== 第二部分：差异统计 =====
  rows.push('==================== 差异统计 ====================')
  rows.push(`"总差异数","${stats?.total_count || differences.length}"`)
  rows.push(`"句末点号差异","${stats?.sentence_end_count || 0}"`)
  rows.push(`"句内点号差异","${stats?.sentence_inner_count || 0}"`)
  rows.push(`"标号差异","${stats?.mark_count || 0}"`)
  rows.push('')

  // ===== 第三部分：标点使用统计 =====
  if (styleReport) {
    rows.push('==================== 标点使用统计 ====================')
    rows.push('"指标","版本A","版本B"')
    rows.push(
      `"标点总数","${styleReport.version1.total_punctuation}","${styleReport.version2.total_punctuation}"`
    )
    rows.push(
      `"标点密度","${styleReport.version1.punctuation_density}%","${styleReport.version2.punctuation_density}%"`
    )
    rows.push('')

    // 各类标点使用频率
    rows.push('==================== 各类标点使用频率 ====================')
    rows.push('"标点符号","版本A数量","版本B数量","差值"')

    const freq1 = styleReport.version1.punctuation_distribution || {}
    const freq2 = styleReport.version2.punctuation_distribution || {}
    const allPuncts = new Set([...Object.keys(freq1), ...Object.keys(freq2)])

    allPuncts.forEach((punct) => {
      const count1 = freq1[punct] || 0
      const count2 = freq2[punct] || 0
      const diff = count2 - count1
      const diffStr = diff > 0 ? `+${diff}` : `${diff}`
      rows.push(`"${punct}","${count1}","${count2}","${diffStr}"`)
    })
    rows.push('')
  }

  // ===== 第四部分：逐条差异明细 =====
  rows.push('==================== 逐条差异明细 ====================')
  rows.push('"序号","位置","前后字符","版本A标点","版本B标点","差异类型","分类","上下文"')

  differences.forEach((diff, index) => {
    const position = diff.position_v1 ?? diff.position
    const char = diff.character || ''
    const punct1 = diff.version1_punct || '无'
    const punct2 = diff.version2_punct || '无'
    const diffType = diff.diff_type || ''
    const category = diff.category || ''
    // 转义上下文中的双引号
    const context = (diff.context || '').replace(/"/g, '""')

    rows.push(
      `"${index + 1}","${position}","${char}","${punct1}","${punct2}","${diffType}","${category}","${context}"`
    )
  })

  rows.push('')
  rows.push(`"说明：共导出 ${differences.length} 条差异记录"`)
  rows.push(`"导出时间：${new Date().toLocaleString('zh-CN')}"`)

  // 生成CSV文件
  const csvContent = BOM + rows.join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `标点对比报告_${result.version1_name}_vs_${result.version2_name}_${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  message.success(`报告导出成功，共 ${differences.length} 条差异记录`)
}
