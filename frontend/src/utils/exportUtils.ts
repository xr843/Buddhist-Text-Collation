/**
 * 导出工具函数
 * 负责生成和下载校勘定本、校勘记等文件
 */

import { message } from 'antd'

/**
 * 定本数据结构
 */
export interface DefinitiveTextData {
  /** 定本文本内容 */
  text: string
  /** 校勘记列表 */
  notes: CollationNote[]
  /** 统计信息 */
  statistics: {
    base_char_count?: number
    definitive_char_count?: number
    total_decisions: number
    applied_count: number
    skipped_uncertain_count?: number
    unchanged_count?: number
  }
}

/**
 * 校勘记条目
 */
export interface CollationNote {
  /** 异文位置 */
  position: number
  /** 异文内容 */
  text: string
  /** 采用的版本 */
  version: string
  /** 判取依据 */
  basis: string
  /** 备注说明 */
  note?: string
}

/**
 * 下载定本文本文件
 *
 * @param definitiveTextData - 定本数据
 * @param projectTitle - 项目标题，用于文件命名
 *
 * @example
 * downloadDefinitiveText(data, "妙法莲华经")
 * // 下载文件名: 妙法莲华经_校勘定本.txt
 */
export function downloadDefinitiveText(
  definitiveTextData: DefinitiveTextData | null,
  projectTitle?: string
): void {
  if (!definitiveTextData) return

  const blob = new Blob([definitiveTextData.text], {
    type: 'text/plain;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${projectTitle || '定本'}_校勘定本.txt`
  a.click()
  URL.revokeObjectURL(url)
  message.success('定本已下载')
}

/**
 * 下载校勘记文件
 *
 * @param definitiveTextData - 定本数据
 * @param projectTitle - 项目标题，用于文件命名
 *
 * @example
 * downloadCollationNotes(data, "妙法莲华经")
 * // 下载文件名: 妙法莲华经_校勘记.txt
 */
export function downloadCollationNotes(
  definitiveTextData: DefinitiveTextData | null,
  projectTitle?: string
): void {
  if (!definitiveTextData || !definitiveTextData.notes.length) return

  const lines: string[] = [
    '==================== 校勘记 ====================',
    `项目：${projectTitle || '未命名'}`,
    `生成时间：${new Date().toLocaleString('zh-CN')}`,
    `总判取数：${definitiveTextData.statistics.total_decisions}`,
    `已应用：${definitiveTextData.statistics.applied_count}`,
    '',
    '==================== 详细记录 ====================',
    '',
  ]

  definitiveTextData.notes.forEach((note, idx) => {
    lines.push(`${idx + 1}. 位置 ${note.position}：${note.text}`)
    lines.push(`   采用版本：${note.version}`)
    lines.push(`   判取依据：${note.basis}`)
    if (note.note) {
      lines.push(`   说明：${note.note}`)
    }
    lines.push('')
  })

  const content = lines.join('\n')
  // 添加 BOM 以确保 UTF-8 编码被正确识别
  const blob = new Blob(['\uFEFF' + content], {
    type: 'text/plain;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${projectTitle || '校勘记'}_校勘记.txt`
  a.click()
  URL.revokeObjectURL(url)
  message.success('校勘记已下载')
}

/**
 * 创建并触发文件下载
 *
 * @param content - 文件内容
 * @param filename - 文件名
 * @param mimeType - MIME类型，默认为 text/plain
 */
export function downloadFile(
  content: string,
  filename: string,
  mimeType: string = 'text/plain;charset=utf-8'
): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

/**
 * 导出CSV格式数据
 *
 * @param headers - CSV表头
 * @param rows - 数据行（二维数组）
 * @param filename - 文件名
 *
 * @example
 * exportToCSV(
 *   ['位置', '底本', '校本1', '校本2'],
 *   [['1', '妙', '妙', '玅'], ['2', '法', '法', '灋']],
 *   '异文表.csv'
 * )
 */
export function exportToCSV(
  headers: string[],
  rows: string[][],
  filename: string
): void {
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
  ].join('\n')

  // 添加 BOM 以确保 Excel 正确识别 UTF-8
  downloadFile('\uFEFF' + csvContent, filename, 'text/csv;charset=utf-8')
  message.success('CSV已导出')
}


// ==================== 标点定本导出函数 ====================

import type { PunctuationDefinitiveData, PunctuationChangeNote } from '../types'

/**
 * 下载标点定本文本文件
 *
 * @param data - 标点定本数据
 * @param projectTitle - 项目标题，用于文件命名
 */
export function downloadPunctuationDefinitiveText(
  data: PunctuationDefinitiveData | null,
  projectTitle?: string
): void {
  if (!data) return

  const blob = new Blob([data.text], {
    type: 'text/plain;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${projectTitle || '标点定本'}_标点定本.txt`
  a.click()
  URL.revokeObjectURL(url)
  message.success('标点定本已下载')
}

/**
 * 下载标点改易记文件
 *
 * @param data - 标点定本数据
 * @param projectTitle - 项目标题，用于文件命名
 */
export function downloadPunctuationChangeNotes(
  data: PunctuationDefinitiveData | null,
  projectTitle?: string
): void {
  if (!data || !data.notes?.length) {
    message.warning('没有标点改易记录')
    return
  }

  const lines: string[] = [
    '==================== 标点改易记 ====================',
    `项目：${projectTitle || '未命名'}`,
    `生成时间：${new Date().toLocaleString('zh-CN')}`,
    `基准版本：${data.version1_name}`,
    `参照版本：${data.version2_name}`,
    '',
    '==================== 统计信息 ====================',
    `判取总数：${data.statistics.total_decisions} 条`,
    `采用 ${data.version1_name}：${data.statistics.version1_adopted} 处`,
    `采用 ${data.version2_name}：${data.statistics.version2_adopted} 处`,
    `实际改动：${data.statistics.applied_count} 处`,
    '',
    '==================== 改易详情 ====================',
    '',
  ]

  data.notes.forEach((note: PunctuationChangeNote, idx: number) => {
    const originalDisplay = note.originalPunct === '∅' ? '（无）' : `「${note.originalPunct}」`
    const changedDisplay = note.changedPunct === '∅' ? '（无）' : `「${note.changedPunct}」`

    lines.push(`${idx + 1}. 位置 ${note.position}`)
    lines.push(`   改易类型：${note.changeType}`)
    lines.push(`   原标点：${originalDisplay} → 改为：${changedDisplay}`)
    if (note.context) {
      lines.push(`   上下文：${note.context.substring(0, 40)}`)
    }
    if (note.note) {
      lines.push(`   备注：${note.note}`)
    }
    lines.push('')
  })

  const content = lines.join('\n')
  // 添加 BOM 以确保 UTF-8 编码被正确识别
  const blob = new Blob(['\uFEFF' + content], {
    type: 'text/plain;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${projectTitle || '标点改易记'}_标点改易记.txt`
  a.click()
  URL.revokeObjectURL(url)
  message.success('标点改易记已下载')
}
