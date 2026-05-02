/**
 * 版本对勘工具函数
 */

import type { UploadFile } from 'antd/es/upload/interface'
import type {
  MultiCollationResponse,
  VariantTableRow,
  CollationDecision,
  DecidedNote,
} from './types'
import { parseVersionInfo } from '../../utils/versionParser'
import { SYSTEM_COLORS } from './constants'

/**
 * 创建上传文件对象（从文本内容）
 */
export function createUploadFileFromText(name: string, text: string): UploadFile {
  const filename = name.trim().endsWith('.txt') ? name.trim() : `${name.trim()}.txt`
  const uid = `ocr-${Date.now()}-${Math.random().toString(16).slice(2)}`
  const file = new File([text], filename, { type: 'text/plain' })
  return {
    uid,
    name: filename,
    status: 'done',
    originFileObj: file as any,
    size: file.size,
    type: file.type,
  }
}

/**
 * 下载文本文件
 */
export function downloadTextFile(text: string, filename: string): void {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

/**
 * 复制文本到剪贴板
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    return true
  }
}

/**
 * 获取版本头部渲染信息
 */
export function getVersionHeaderInfo(fullName: string) {
  const info = parseVersionInfo(fullName)
  return {
    system: info.system,
    canon: info.canon,
    sutra: info.sutra,
    color: SYSTEM_COLORS[info.system] || '#8c8c8c',
  }
}

/**
 * 根据位置获取异文行
 */
export function getVariantRowByPosition(
  rows: VariantTableRow[] | undefined,
  position: number
): VariantTableRow | null {
  if (!rows) return null
  return rows.find((r) => r.position === position) || null
}

/**
 * 滚动到异文行
 */
export function scrollToVariantRow(position: number): boolean {
  const el = document.querySelector(`tr[data-row-key="${position}"]`) as HTMLElement | null
  if (!el) return false
  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  return true
}

/**
 * 构建已判取记录列表
 */
export function buildDecidedNotes(
  decisions: Record<number, CollationDecision>,
  rows: VariantTableRow[] | undefined
): DecidedNote[] {
  const rowMap = new Map(rows?.map((r) => [r.position, r]) || [])

  return Object.entries(decisions)
    .map(([posStr, d]) => {
      const position = parseInt(posStr)
      const row = rowMap.get(position)
      return {
        position,
        context: row?.context || '',
        category: row?.category || '',
        base_char: row?.base_char || '',
        selectedText: d.selectedText,
        selectedVersion: d.selectedVersion,
        uncertain: !!d.uncertain,
        note: d.note || '',
      }
    })
    .sort((a, b) => a.position - b.position)
}

/**
 * 过滤已判取记录
 */
export function filterDecidedNotes(notes: DecidedNote[], query: string): DecidedNote[] {
  const q = query.trim().toLowerCase()
  if (!q) return notes

  return notes.filter((r) => {
    const haystack = [
      r.position.toString(),
      r.context,
      r.category,
      r.base_char,
      r.selectedText,
      r.selectedVersion,
      r.note,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    return haystack.includes(q)
  })
}

/**
 * 导出汇总统计 CSV
 */
export function exportSummaryCSV(result: MultiCollationResponse): void {
  const BOM = '\uFEFF'
  const rows: string[] = []
  const { summary, base, collations, processing_time } = result

  // 标题
  rows.push('==================== 一底多校汇总统计 ====================')
  rows.push('')
  rows.push(`"生成时间","${new Date().toLocaleString()}"`)
  rows.push(`"处理耗时","${processing_time}秒"`)
  rows.push('')

  // 底本信息
  rows.push('---------- 底本信息 ----------')
  rows.push(`"底本名称","${base.name}"`)
  rows.push(`"底本字数","${base.char_count}"`)
  rows.push('')

  // 校本信息
  rows.push('---------- 校本信息 ----------')
  rows.push('"序号","校本名称","字数","相似度"')
  collations.forEach((coll, idx) => {
    const sim = (coll.result.similarity * 100).toFixed(1)
    rows.push(`"${idx + 1}","${coll.collation_name}","${coll.char_count}","${sim}%"`)
  })
  rows.push('')

  // 差异统计
  rows.push('---------- 差异统计 ----------')
  if (summary.stats_table) {
    const headers = ['差异类型', ...summary.stats_table.headers.slice(1)]
    rows.push(`"${headers.join('","')}"`)

    summary.stats_table.rows.forEach((row) => {
      const values = [row.type, ...row.values.map(String), row.total.toString()]
      rows.push(`"${values.join('","')}"`)
    })
  }
  rows.push('')

  // 生成下载
  const csvContent = BOM + rows.join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `一底多校汇总_${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 导出异文汇校表 CSV
 */
export function exportVariantTableCSV(
  result: MultiCollationResponse,
  categoryFilter: string = 'all'
): void {
  if (!result.variant_table) return

  const BOM = '\uFEFF'
  const rows: string[] = []
  const { variant_table, summary } = result

  // 过滤数据
  let filteredRows = variant_table.rows
  if (categoryFilter !== 'all') {
    filteredRows = filteredRows.filter((r) => r.category === categoryFilter)
  }

  // 标题
  rows.push('==================== 异文汇校表 ====================')
  rows.push('')
  rows.push(`"导出时间","${new Date().toLocaleString()}"`)
  rows.push(`"筛选条件","${categoryFilter === 'all' ? '全部' : categoryFilter}"`)
  rows.push(`"总记录数","${filteredRows.length}"`)
  rows.push('')

  // 表头
  const headers = ['位置', '上下文', '底本', ...summary.collation_names, '分类']
  rows.push(`"${headers.join('","')}"`)

  // 数据行
  filteredRows.forEach((row) => {
    const values = [
      row.position.toString(),
      row.context,
      row.base_char,
      ...row.coll_values,
      row.category,
    ]
    rows.push(`"${values.join('","')}"`)
  })

  // 生成下载
  const csvContent = BOM + rows.join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `异文汇校表_${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
