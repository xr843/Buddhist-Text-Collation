/**
 * 文字校勘模式展示组件 - 逐句对齐 + 字符级高亮
 */
import { useState, useMemo, useEffect, useCallback } from 'react'
import { Card, Typography, Row, Col, Statistic, Tag, Space, Pagination, Radio, Button, message, InputNumber, Dropdown, Modal, Spin } from 'antd'
import type { MenuProps } from 'antd'
import {
  DownloadOutlined,
  SplitCellsOutlined,
  MenuOutlined,
  DiffOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import { comparisonApi } from '../services/api'

const { Text } = Typography

interface CharSegment {
  text: string
  type: string  // equal/delete/insert/replace
  is_punct: boolean  // 是否是标点符号
  category?: string | null  // variant/error/yanwen/tuowen (倒文已归入error)
}

interface AlignedSentence {
  id: number
  type: string
  sentence1: string
  sentence2: string
  has_diff: boolean
  char_diff: {
    segments1: CharSegment[]
    segments2: CharSegment[]
    diff_type?: 'punct_only' | 'text_only' | 'mixed' | null  // 差异类型
  } | null
}

// 展示布局模式
type DisplayMode = 'side-by-side' | 'inline' | 'changes-only'

// 异文分类筛选（倒文已归入讹误）
type CategoryFilter = 'all' | 'variant' | 'error' | 'yanwen' | 'tuowen'

interface CollationViewProps {
  data: {
    mode: string
    mode_description: string
    version1_name: string
    version2_name: string
    processing_time?: number  // 处理耗时（秒）
    // 原始文本（用于导出校勘记）
    text1?: string
    text2?: string
    statistics: {
      version1_length: number
      version2_length: number
      total_differences: number
      insertions: number
      deletions: number
      replacements: number
      inserted_chars: number
      deleted_chars: number
      replaced_chars: number
      total_changed_chars: number
      // 分类统计（倒文已合并到讹误中）
      category_stats?: {
        variant_chars: number    // 异体字数量
        error_chars: number      // 讹误数量（含倒文）
        yanwen_chars: number     // 衍文数量
        tuowen_chars: number     // 脱文数量
      }
      diff_details?: {
        deleted: { char: string; count: number; category?: string }[]
        inserted: { char: string; count: number; category?: string }[]
        replaced: { from: string; to: string; count: number; category?: string; category_cn?: string }[]
        transposed?: { from: string; to: string; count: number; category?: string; category_cn?: string }[]
      }
    }
    similarity: number
    aligned_sentences?: AlignedSentence[]
    // 原始全局对齐结果（用于导出）
    side_by_side?: {
      segments: Array<{
        type: string  // equal/replace/delete/insert
        text1: string
        text2: string
      }>
      total_segments: number
    }
  }
  // 初始高亮定位（从异文汇校表跳转时使用）
  initialHighlight?: {
    char: string  // 要定位的字符
    type?: 'replace' | 'delete' | 'insert'
  }
}

export default function CollationView({ data, initialHighlight }: CollationViewProps) {
  const { statistics, similarity, aligned_sentences, version1_name, version2_name, side_by_side, processing_time, text1, text2 } = data

  // 【调试】打印接收到的数据
  useEffect(() => {
    console.log('='.repeat(80))
    console.log('CollationView 数据调试')
    console.log('='.repeat(80))
    console.log('aligned_sentences 数量:', aligned_sentences?.length || 0)

    if (aligned_sentences && aligned_sentences.length > 0) {
      const first = aligned_sentences[0]
      console.log('\n第一条对齐记录:')
      console.log('- sentence1 存在:', !!first.sentence1)
      console.log('- sentence2 存在:', !!first.sentence2)
      console.log('- sentence1 长度:', first.sentence1?.length || 0)
      console.log('- sentence2 长度:', first.sentence2?.length || 0)
      console.log('- sentence1:', first.sentence1?.substring(0, 30) + '...')
      console.log('- sentence2:', first.sentence2?.substring(0, 30) + '...')
      console.log('- has_diff:', first.has_diff)
      console.log('- char_diff exists:', !!first.char_diff)
      if (first.char_diff) {
        console.log('- segments1 数量:', first.char_diff.segments1?.length || 0)
        console.log('- segments2 数量:', first.char_diff.segments2?.length || 0)
      }
    }
    console.log('='.repeat(80))
  }, [aligned_sentences])

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)

  // 展示布局模式（并排/逐行/仅差异）
  const [displayMode, setDisplayMode] = useState<DisplayMode>('side-by-side')

  // 异文分类筛选
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>('all')

  // 校勘记预览
  const [previewModalVisible, setPreviewModalVisible] = useState(false)
  const [previewContent, setPreviewContent] = useState<string>('')
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewFormat, setPreviewFormat] = useState<'txt' | 'tei-xml'>('txt')

  // 高亮的差异字符（用于从详细差异表格跳转）
  const [_highlightedChar, setHighlightedChar] = useState<{
    type: 'replace' | 'delete' | 'insert'
    char?: string
    from?: string
    to?: string
  } | null>(null)

  // 差异导航状态（用于同一差异的多处跳转）
  const [diffNavigation, setDiffNavigation] = useState<{
    type: 'replace' | 'delete' | 'insert'
    char?: string
    from?: string
    to?: string
    matchedRecords: AlignedSentence[]  // 所有匹配的记录
    currentIndex: number               // 当前查看的索引
  } | null>(null)

  // 跳转到指定索引的匹配记录
  const navigateToMatch = (index: number) => {
    if (!diffNavigation || index < 0 || index >= diffNavigation.matchedRecords.length) {
      return
    }

    const targetRecord = diffNavigation.matchedRecords[index]

    // 更新当前索引
    setDiffNavigation(prev => prev ? { ...prev, currentIndex: index } : null)

    // 在 filteredData 中查找该记录的索引
    const targetIndexInFiltered = filteredData.findIndex(r => r.id === targetRecord.id)

    if (targetIndexInFiltered >= 0) {
      // 计算目标页码
      const targetPage = Math.floor(targetIndexInFiltered / pageSize) + 1
      setCurrentPage(targetPage)

      // 设置高亮字符
      setHighlightedChar({
        type: diffNavigation.type,
        char: diffNavigation.char,
        from: diffNavigation.from,
        to: diffNavigation.to
      })

      // 滚动到目标行
      setTimeout(() => {
        const element = document.getElementById(`aligned-row-${targetRecord.id}`)
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' })
          element.style.animation = 'highlight-flash 1.5s ease-in-out'
          setTimeout(() => {
            element.style.animation = ''
          }, 1500)
        }
      }, 100)

      // 3秒后清除高亮（但保留导航状态）
      setTimeout(() => {
        setHighlightedChar(null)
      }, 3000)
    }
  }

  // 上一处
  const navigateToPrevMatch = () => {
    if (diffNavigation && diffNavigation.currentIndex > 0) {
      navigateToMatch(diffNavigation.currentIndex - 1)
    }
  }

  // 下一处
  const navigateToNextMatch = () => {
    if (diffNavigation && diffNavigation.currentIndex < diffNavigation.matchedRecords.length - 1) {
      navigateToMatch(diffNavigation.currentIndex + 1)
    }
  }

  // 关闭导航
  const closeDiffNavigation = () => {
    setDiffNavigation(null)
    setHighlightedChar(null)
  }

  // 处理从异文汇校表跳转时的初始定位
  useEffect(() => {
    if (initialHighlight && initialHighlight.char && aligned_sentences && aligned_sentences.length > 0) {
      console.log('[初始定位] 接收到定位请求:', initialHighlight)

      // 延迟执行，确保组件渲染完成
      setTimeout(() => {
        // 查找包含该字符的差异记录
        const matchedRecords: AlignedSentence[] = []

        for (const record of aligned_sentences) {
          if (!record.has_diff || !record.char_diff) continue

          const segments1 = record.char_diff.segments1 || []
          const segments2 = record.char_diff.segments2 || []

          // 检查是否包含该字符
          const hasInSegments1 = segments1.some(s =>
            s.type !== 'equal' && s.text.includes(initialHighlight.char)
          )
          const hasInSegments2 = segments2.some(s =>
            s.type !== 'equal' && s.text.includes(initialHighlight.char)
          )

          if (hasInSegments1 || hasInSegments2) {
            matchedRecords.push(record)
          }
        }

        console.log('[初始定位] 找到匹配记录数:', matchedRecords.length)

        if (matchedRecords.length > 0) {
          const targetRecord = matchedRecords[0]

          // 设置导航状态
          setDiffNavigation({
            type: initialHighlight.type || 'replace',
            char: initialHighlight.char,
            matchedRecords,
            currentIndex: 0
          })

          // 计算目标页码
          const targetIndex = aligned_sentences.findIndex(r => r.id === targetRecord.id)
          if (targetIndex >= 0) {
            const targetPage = Math.floor(targetIndex / pageSize) + 1
            setCurrentPage(targetPage)

            // 设置高亮
            setHighlightedChar({
              type: initialHighlight.type || 'replace',
              char: initialHighlight.char
            })

            // 滚动到目标行
            setTimeout(() => {
              const element = document.getElementById(`aligned-row-${targetRecord.id}`)
              if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'center' })
                element.style.animation = 'highlight-flash 1.5s ease-in-out'
                setTimeout(() => {
                  element.style.animation = ''
                }, 1500)
              }
            }, 200)

            // 3秒后清除高亮
            setTimeout(() => {
              setHighlightedChar(null)
            }, 3000)
          }
        }
      }, 300)
    }
  }, [initialHighlight, aligned_sentences])

  // 跳转到包含指定差异字符的段落
  const jumpToCharDiff = (
    type: 'replace' | 'delete' | 'insert',
    char?: string,
    from?: string,
    to?: string
  ) => {
    console.log('=== jumpToCharDiff 调用 ===')
    console.log('type:', type, 'char:', char, 'from:', from, 'to:', to)

    if (!aligned_sentences) {
      console.log('aligned_sentences 为空')
      return
    }

    console.log('aligned_sentences 数量:', aligned_sentences.length)

    // 查找所有包含该差异字符的段落（而不是只找第一个）
    const matchedRecords: AlignedSentence[] = []

    for (let i = 0; i < aligned_sentences.length; i++) {
      const record = aligned_sentences[i]
      if (!record.has_diff || !record.char_diff) continue

      const segments1 = record.char_diff.segments1 || []
      const segments2 = record.char_diff.segments2 || []

      // 检查是否包含该差异
      let found = false

      if (type === 'replace' && from && to) {
        // 替换（异体字/讹误）：精确匹配
        const hasFrom = segments1.some(s => s.type === 'replace' && s.text === from)
        const hasTo = segments2.some(s => s.type === 'replace' && s.text === to)
        found = hasFrom && hasTo
      } else if (type === 'delete' && char) {
        // 脱文：精确匹配 type='delete' 且 text===char
        found = segments1.some(s => s.type === 'delete' && s.text === char)
      } else if (type === 'insert' && char) {
        // 衍文：精确匹配 type='insert' 且 text===char
        found = segments2.some(s => s.type === 'insert' && s.text === char)
      }

      if (found) {
        matchedRecords.push(record)
      }
    }

    console.log('找到匹配记录数:', matchedRecords.length)

    if (matchedRecords.length > 0) {
      // 设置导航状态
      setDiffNavigation({
        type,
        char,
        from,
        to,
        matchedRecords,
        currentIndex: 0
      })

      // 跳转到第一处
      const targetRecord = matchedRecords[0]
      const targetIndexInFiltered = filteredData.findIndex(r => r.id === targetRecord.id)
      console.log('在 filteredData 中的索引:', targetIndexInFiltered)

      if (targetIndexInFiltered >= 0) {
        // 计算目标页码（基于 filteredData）
        const targetPage = Math.floor(targetIndexInFiltered / pageSize) + 1
        console.log('目标页码:', targetPage)
        setCurrentPage(targetPage)

        // 设置高亮字符
        setHighlightedChar({ type, char, from, to })

        // 滚动到目标行
        setTimeout(() => {
          const element = document.getElementById(`aligned-row-${targetRecord.id}`)
          console.log('目标元素:', element)
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' })
            // 添加闪烁效果
            element.style.animation = 'highlight-flash 1.5s ease-in-out'
            setTimeout(() => {
              element.style.animation = ''
            }, 1500)
          }
        }, 100)

        // 3秒后清除高亮（但保留导航状态）
        setTimeout(() => {
          setHighlightedChar(null)
        }, 3000)
      } else {
        // 目标不在当前过滤结果中，提示用户
        console.log('目标差异不在当前过滤结果中，请切换到"全部"视图')
      }
    } else {
      console.log('未找到包含该差异的记录')
      setDiffNavigation(null)
    }
  }

  // CSV 导出函数
  const exportToCSV = useCallback(() => {
    if (!statistics.diff_details) {
      message.warning('没有差异数据可导出')
      return
    }

    const rows: string[] = []

    // 添加 BOM 以支持 Excel 正确识别 UTF-8
    const BOM = '\uFEFF'

    // ===== 第一部分：统计摘要 =====
    rows.push('==================== 统计摘要 ====================')
    rows.push('')
    rows.push('"项目","数值"')
    rows.push(`"底本（${version1_name}）字数","${statistics.version1_length}"`)
    rows.push(`"校本（${version2_name}）字数","${statistics.version2_length}"`)
    rows.push(`"总差异处数","${statistics.total_differences}"`)
    rows.push(`"文本相似度","${(similarity * 100).toFixed(1)}%"`)
    if (processing_time !== undefined) {
      rows.push(`"处理耗时","${processing_time}秒"`)
    }
    rows.push('')

    // 分类统计（倒文已合并到讹误中）
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

    // ===== 第二部分：替换详情（含分类） =====
    rows.push('==================== 替换详情 ====================')
    rows.push('')
    rows.push(`"序号","底本（${version1_name}）","校本（${version2_name}）","出现次数","分类"`)
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

    // ===== 第三部分：脱文详情 =====
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

    // ===== 第四部分：衍文详情 =====
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

    // ===== 第五部分：逐条差异记录（含分类） =====
    rows.push('==================== 逐条差异记录 ====================')
    rows.push('')
    rows.push(`"序号","差异类型","底本文字","校本文字","分类"`)

    let diffIdx = 0

    // 直接使用 diff_details 展开，这样数量就和"详细差异"统计一致
    const diffDetails = statistics.diff_details

    if (diffDetails) {
      // 1. 替换记录
      diffDetails.replaced.forEach(item => {
        const category = item.category === 'variant' ? '异体字' : '讹误'
        for (let i = 0; i < item.count; i++) {
          diffIdx++
          rows.push(`"${diffIdx}","替换","${item.from}","${item.to}","${category}"`)
        }
      })

      // 2. 脱文记录
      diffDetails.deleted.forEach(item => {
        for (let i = 0; i < item.count; i++) {
          diffIdx++
          rows.push(`"${diffIdx}","脱文","${item.char}","（无）","脱文"`)
        }
      })

      // 3. 衍文记录
      diffDetails.inserted.forEach(item => {
        for (let i = 0; i < item.count; i++) {
          diffIdx++
          rows.push(`"${diffIdx}","衍文","（无）","${item.char}","衍文"`)
        }
      })

      // 4. 倒文记录（归类为讹误）
      const transposedItems = diffDetails.transposed || []
      transposedItems.forEach(item => {
        for (let i = 0; i < item.count; i++) {
          diffIdx++
          rows.push(`"${diffIdx}","讹误","${item.from}","${item.to}","讹误（倒文）"`)
        }
      })
    }

    if (diffIdx === 0) {
      rows.push('"","（无差异）","","",""')
    }

    // 添加说明
    rows.push('')
    rows.push(`"说明：逐条差异记录共 ${diffIdx} 条"`)
    rows.push(`"分类说明：异体字=同字异形（非错误），讹误=非异体字的文字差异（含倒文），脱文=底本有校本无，衍文=校本有底本无"`)

    // 生成 CSV 内容
    const csvContent = BOM + rows.join('\n')

    // 创建下载链接
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `文字校勘报告_底本vs校本_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    message.success('CSV 文件已下载')
  }, [statistics, similarity, version1_name, version2_name, aligned_sentences, side_by_side])

  // 导出校勘记（学术格式）
  const exportCollationNotes = useCallback(async (format: 'txt' | 'tei-xml' | 'json' | 'csv') => {
    if (!text1 || !text2) {
      message.warning('无法导出：原始文本数据不可用')
      return
    }

    try {
      message.loading({ content: '正在生成校勘记...', key: 'export' })

      const result = await comparisonApi.exportCollationNotes({
        text1,
        text2,
        version1_name,
        version2_name,
        format,
        include_context: true,
        title: `${version1_name} 与 ${version2_name} 校勘记`
      })

      if (result.success) {
        // 下载文件
        const blob = new Blob([result.content], { type: result.content_type })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = result.filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)

        message.success({ content: `校勘记已导出（${result.note_count} 条）`, key: 'export' })
      }
    } catch (error) {
      console.error('导出校勘记失败:', error)
      message.error({ content: '导出失败，请重试', key: 'export' })
    }
  }, [text1, text2, version1_name, version2_name])

  // 预览校勘记
  const previewCollationNotes = useCallback(async (format: 'txt' | 'tei-xml') => {
    if (!text1 || !text2) {
      message.warning('无法预览：原始文本数据不可用')
      return
    }

    setPreviewFormat(format)
    setPreviewLoading(true)
    setPreviewModalVisible(true)

    try {
      const result = await comparisonApi.exportCollationNotes({
        text1,
        text2,
        version1_name,
        version2_name,
        format,
        include_context: true,
        title: `${version1_name} 与 ${version2_name} 校勘记`
      })

      if (result.success) {
        setPreviewContent(result.content)
      }
    } catch (error) {
      console.error('预览校勘记失败:', error)
      message.error('预览失败，请重试')
      setPreviewModalVisible(false)
    } finally {
      setPreviewLoading(false)
    }
  }, [text1, text2, version1_name, version2_name])

  // 导出菜单项
  const exportMenuItems: MenuProps['items'] = [
    {
      key: 'preview',
      label: '预览校勘记',
      icon: <EyeOutlined />,
      children: [
        {
          key: 'preview-txt',
          label: '预览 TXT 格式（陈垣体例）',
          onClick: () => previewCollationNotes('txt')
        },
        {
          key: 'preview-tei',
          label: '预览 TEI-XML 格式',
          onClick: () => previewCollationNotes('tei-xml')
        },
      ]
    },
    { type: 'divider' },
    {
      key: 'csv-simple',
      label: '导出 CSV（简易报告）',
      onClick: () => exportToCSV()
    },
    { type: 'divider' },
    {
      key: 'notes-txt',
      label: '导出 TXT 校勘记（陈垣体例）',
      onClick: () => exportCollationNotes('txt')
    },
    {
      key: 'notes-tei',
      label: '导出 TEI-XML（数字人文标准）',
      onClick: () => exportCollationNotes('tei-xml')
    },
    {
      key: 'notes-csv',
      label: '导出 CSV 校勘记（学术格式）',
      onClick: () => exportCollationNotes('csv')
    },
    {
      key: 'notes-json',
      label: '导出 JSON（结构化数据）',
      onClick: () => exportCollationNotes('json')
    }
  ]

  // 根据分类筛选过滤数据
  const filteredData = useMemo(() => {
    if (!aligned_sentences) return []

    // 分类筛选
    if (categoryFilter !== 'all') {
      return aligned_sentences.filter(record => {
        if (!record.has_diff || !record.char_diff) return false

        const segments1 = record.char_diff.segments1 || []
        const segments2 = record.char_diff.segments2 || []
        const allSegments = [...segments1, ...segments2]

        // 检查是否包含指定分类的差异
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

    return aligned_sentences
  }, [aligned_sentences, categoryFilter])

  // 计算当前页的数据
  const startIndex = (currentPage - 1) * pageSize
  const endIndex = startIndex + pageSize
  const currentPageData = filteredData.slice(startIndex, endIndex)

  // 渲染字符级高亮
  const renderCharHighlight = (segments: CharSegment[] | undefined) => {
    if (!segments || segments.length === 0) {
      return null
    }

    return (
      <span>
        {segments.map((seg, idx) => {
          let bgColor = 'transparent'
          let color = 'inherit'

          // 设置颜色（根据差异类型）
          if (seg.type !== 'equal') {
            if (seg.is_punct) {
              // 标点差异：蓝色系弱高亮
              bgColor = '#e6f7ff'
              color = '#096dd9'
            } else {
              // 文字差异：根据 category 使用不同颜色
              if (seg.category === 'variant') {
                // 异体字：绿色
                bgColor = '#b7eb8f'
                color = '#135200'
              } else if (seg.category === 'error') {
                // 讹误：红色
                bgColor = '#ffa39e'
                color = '#a8071a'
              } else if (seg.category === 'yanwen' || seg.type === 'insert') {
                // 衍文：橙色
                bgColor = '#ffd591'
                color = '#ad4e00'
              } else if (seg.category === 'tuowen' || seg.type === 'delete') {
                // 脱文：紫色
                bgColor = '#d3adf7'
                color = '#391085'
              } else {
                // 默认（replace 无 category）：红色
                bgColor = '#ffa39e'
                color = '#a8071a'
              }
            }
          }

          return (
            <span
              key={idx}
              style={{
                background: bgColor,
                color: color,
                fontWeight: bgColor !== 'transparent' ? 500 : 'normal',
              }}
            >
              {seg.text}
            </span>
          )
        })}
      </span>
    )
  }

  // 渲染普通文本
  const renderPlainText = (text: string | undefined, emptySymbol: string = '∅') => {
    if (!text) return <span style={{ color: '#999' }}>{emptySymbol}</span>
    return text
  }

  return (
    <div>
      {/* 闪烁动画样式 */}
      <style>
        {`
          @keyframes highlight-flash {
            0% { background-color: inherit; box-shadow: none; }
            25% { background-color: #bae7ff; box-shadow: 0 0 10px #1890ff; }
            50% { background-color: inherit; box-shadow: none; }
            75% { background-color: #bae7ff; box-shadow: 0 0 10px #1890ff; }
            100% { background-color: inherit; box-shadow: none; }
          }
        `}
      </style>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 差异统计 */}
        <Card
          title={
            <Space>
              <span>差异统计</span>
              {processing_time !== undefined && (
                <Tag color="blue">耗时 {processing_time}s</Tag>
              )}
              {categoryFilter !== 'all' && (
                <Tag
                  color="orange"
                  closable
                  onClose={() => setCategoryFilter('all')}
                >
                  筛选中: {
                    categoryFilter === 'variant' ? '异体字' :
                    categoryFilter === 'error' ? '讹误' :
                    categoryFilter === 'yanwen' ? '衍文' :
                    categoryFilter === 'tuowen' ? '脱文' : ''
                  }
                </Tag>
              )}
            </Space>
          }
          extra={
            <Dropdown menu={{ items: exportMenuItems }} placement="bottomRight">
              <Button type="primary" icon={<DownloadOutlined />}>
                导出 ▼
              </Button>
            </Dropdown>
          }
        >
          {/* 精简统计：相似度 + 五类分类（可点击筛选） */}
          {statistics.category_stats && (
            <>
              <div style={{ marginBottom: 8, fontSize: 12, color: '#999' }}>
                点击下方分类可快速筛选对应类型的差异
              </div>
              <Row gutter={[16, 16]} align="middle">
                <Col xs={24} sm={8} md={4}>
                  <Statistic
                    title="文本相似度"
                    value={similarity * 100}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: similarity > 0.8 ? '#3f8600' : '#cf1322' }}
                  />
                </Col>
                <Col xs={12} sm={8} md={4}>
                  <div
                    onClick={() => setCategoryFilter(categoryFilter === 'variant' ? 'all' : 'variant')}
                    style={{
                      cursor: 'pointer',
                      padding: '8px',
                      borderRadius: 8,
                      background: categoryFilter === 'variant' ? '#f6ffed' : 'transparent',
                      border: categoryFilter === 'variant' ? '2px solid #52c41a' : '2px solid transparent',
                      transition: 'all 0.2s',
                    }}
                  >
                    <Statistic
                      title="异体字"
                      value={statistics.category_stats.variant_chars}
                      suffix="处"
                      valueStyle={{ color: '#52c41a' }}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>同字异形</Text>
                  </div>
                </Col>
                <Col xs={12} sm={8} md={4}>
                  <div
                    onClick={() => setCategoryFilter(categoryFilter === 'error' ? 'all' : 'error')}
                    style={{
                      cursor: 'pointer',
                      padding: '8px',
                      borderRadius: 8,
                      background: categoryFilter === 'error' ? '#fff1f0' : 'transparent',
                      border: categoryFilter === 'error' ? '2px solid #f5222d' : '2px solid transparent',
                      transition: 'all 0.2s',
                    }}
                  >
                    <Statistic
                      title="讹误"
                      value={statistics.category_stats.error_chars}
                      suffix="处"
                      valueStyle={{ color: '#f5222d' }}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>文字错误</Text>
                  </div>
                </Col>
                <Col xs={12} sm={8} md={4}>
                  <div
                    onClick={() => setCategoryFilter(categoryFilter === 'yanwen' ? 'all' : 'yanwen')}
                    style={{
                      cursor: 'pointer',
                      padding: '8px',
                      borderRadius: 8,
                      background: categoryFilter === 'yanwen' ? '#fff7e6' : 'transparent',
                      border: categoryFilter === 'yanwen' ? '2px solid #fa8c16' : '2px solid transparent',
                      transition: 'all 0.2s',
                    }}
                  >
                    <Statistic
                      title="衍文"
                      value={statistics.category_stats.yanwen_chars}
                      suffix="字"
                      valueStyle={{ color: '#fa8c16' }}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>校本有底本无</Text>
                  </div>
                </Col>
                <Col xs={12} sm={8} md={4}>
                  <div
                    onClick={() => setCategoryFilter(categoryFilter === 'tuowen' ? 'all' : 'tuowen')}
                    style={{
                      cursor: 'pointer',
                      padding: '8px',
                      borderRadius: 8,
                      background: categoryFilter === 'tuowen' ? '#f9f0ff' : 'transparent',
                      border: categoryFilter === 'tuowen' ? '2px solid #722ed1' : '2px solid transparent',
                      transition: 'all 0.2s',
                    }}
                  >
                    <Statistic
                      title="脱文"
                      value={statistics.category_stats.tuowen_chars}
                      suffix="字"
                      valueStyle={{ color: '#722ed1' }}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>底本有校本无</Text>
                  </div>
                </Col>
                <Col xs={12} sm={8} md={4}>
                  <div
                    onClick={() => setCategoryFilter('all')}
                    style={{
                      cursor: 'pointer',
                      padding: '8px',
                      borderRadius: 8,
                      background: categoryFilter === 'all' ? '#e6f7ff' : 'transparent',
                      border: categoryFilter === 'all' ? '2px solid #1890ff' : '2px solid transparent',
                      transition: 'all 0.2s',
                    }}
                  >
                    <Statistic
                      title="总数"
                      value={
                        statistics.category_stats.variant_chars +
                        statistics.category_stats.error_chars +
                        statistics.category_stats.yanwen_chars +
                        statistics.category_stats.tuowen_chars
                      }
                      suffix="处"
                      valueStyle={{ color: '#1890ff', fontWeight: 'bold' }}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>四类差异合计</Text>
                  </div>
                </Col>
              </Row>
            </>
          )}
        </Card>

        {/* 详细文字差异统计 */}
        {statistics.diff_details && (
          <Card title="详细文字差异" size="small">
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {/* 异体字 - 表格形式 */}
              <div style={{ flex: '1 1 18%', minWidth: 200 }}>
                {(() => {
                  const variantItems = statistics.diff_details.replaced.filter(item => item.category === 'variant')
                  const variantCount = variantItems.reduce((sum, item) => sum + item.count, 0)
                  return (
                    <>
                      <div style={{ marginBottom: 12 }}>
                        <Tag color="success" style={{ marginRight: 8 }}>异体字</Tag>
                        <Text type="secondary">共 {variantItems.length} 种，{variantCount} 处</Text>
                      </div>
                      <div style={{
                        border: '1px solid #f0f0f0',
                        borderRadius: 6,
                        minHeight: 300,
                        maxHeight: 300,
                        overflowY: 'auto'
                      }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                          <thead>
                            <tr style={{ background: '#fafafa', position: 'sticky', top: 0, zIndex: 1, minHeight: 60 }}>
                              <th style={{ padding: '8px 12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', width: 60, verticalAlign: 'middle' }}>序号</th>
                              <th style={{ padding: '8px 12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', verticalAlign: 'middle' }}>
                                <div style={{ fontSize: 11, color: '#1890ff', fontWeight: 'bold', marginBottom: 2 }}>底本 → 校本</div>
                                <div style={{ fontSize: 11, color: '#999', fontWeight: 'normal', lineHeight: 1.2 }}>{version1_name}</div>
                                <div style={{ fontSize: 11, color: '#999', fontWeight: 'normal', lineHeight: 1.2 }}>→ {version2_name}</div>
                              </th>
                              <th style={{ padding: '8px 12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', width: 60, verticalAlign: 'middle' }}>次数</th>
                            </tr>
                          </thead>
                          <tbody>
                            {variantItems.length > 0 ? (
                              variantItems.map((item, idx) => (
                                <tr
                                  key={idx}
                                  style={{
                                    background: idx % 2 === 0 ? '#fff' : '#fafafa',
                                    cursor: 'pointer',
                                    transition: 'background 0.2s'
                                  }}
                                  onClick={() => jumpToCharDiff('replace', undefined, item.from, item.to)}
                                  onMouseEnter={(e) => { e.currentTarget.style.background = '#f6ffed' }}
                                  onMouseLeave={(e) => { e.currentTarget.style.background = idx % 2 === 0 ? '#fff' : '#fafafa' }}
                                  title="点击跳转到正文对应位置"
                                >
                                  <td style={{ padding: '6px 12px', textAlign: 'center', color: '#999' }}>{idx + 1}</td>
                                  <td style={{ padding: '6px 12px', textAlign: 'center' }}>
                                    <span style={{
                                      background: '#d9f7be',
                                      color: '#389e0d',
                                      padding: '2px 8px',
                                      borderRadius: 4,
                                      fontWeight: 500,
                                      fontSize: 16
                                    }}>{item.from}→{item.to}</span>
                                  </td>
                                  <td style={{ padding: '6px 12px', textAlign: 'center', color: '#52c41a', fontWeight: 500 }}>{item.count}</td>
                                </tr>
                              ))
                            ) : (
                              <tr>
                                <td colSpan={3} style={{ padding: 40, textAlign: 'center', color: '#999' }}>无异体字</td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )
                })()}
              </div>

              {/* 讹误 - 表格形式 */}
              <div style={{ flex: '1 1 18%', minWidth: 200 }}>
                {(() => {
                  const errorItems = statistics.diff_details.replaced.filter(item => item.category === 'error')
                  const errorCount = errorItems.reduce((sum, item) => sum + item.count, 0)
                  return (
                    <>
                      <div style={{ marginBottom: 12 }}>
                        <Tag color="error" style={{ marginRight: 8 }}>讹误</Tag>
                        <Text type="secondary">共 {errorItems.length} 种，{errorCount} 处</Text>
                      </div>
                      <div style={{
                        border: '1px solid #f0f0f0',
                        borderRadius: 6,
                        minHeight: 300,
                        maxHeight: 300,
                        overflowY: 'auto'
                      }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                          <thead>
                            <tr style={{ background: '#fafafa', position: 'sticky', top: 0, zIndex: 1, minHeight: 60 }}>
                              <th style={{ padding: '8px 12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', width: 60, verticalAlign: 'middle' }}>序号</th>
                              <th style={{ padding: '8px 12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', verticalAlign: 'middle' }}>
                                <div style={{ fontSize: 11, color: '#1890ff', fontWeight: 'bold', marginBottom: 2 }}>底本 → 校本</div>
                                <div style={{ fontSize: 11, color: '#999', fontWeight: 'normal', lineHeight: 1.2 }}>{version1_name}</div>
                                <div style={{ fontSize: 11, color: '#999', fontWeight: 'normal', lineHeight: 1.2 }}>→ {version2_name}</div>
                              </th>
                              <th style={{ padding: '8px 12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', width: 60, verticalAlign: 'middle' }}>次数</th>
                            </tr>
                          </thead>
                          <tbody>
                            {errorItems.length > 0 ? (
                              errorItems.map((item, idx) => (
                                <tr
                                  key={idx}
                                  style={{
                                    background: idx % 2 === 0 ? '#fff' : '#fafafa',
                                    cursor: 'pointer',
                                    transition: 'background 0.2s'
                                  }}
                                  onClick={() => jumpToCharDiff('replace', undefined, item.from, item.to)}
                                  onMouseEnter={(e) => { e.currentTarget.style.background = '#fff1f0' }}
                                  onMouseLeave={(e) => { e.currentTarget.style.background = idx % 2 === 0 ? '#fff' : '#fafafa' }}
                                  title="点击跳转到正文对应位置"
                                >
                                  <td style={{ padding: '6px 12px', textAlign: 'center', color: '#999' }}>{idx + 1}</td>
                                  <td style={{ padding: '6px 12px', textAlign: 'center' }}>
                                    <span style={{
                                      background: '#ffccc7',
                                      color: '#cf1322',
                                      padding: '2px 8px',
                                      borderRadius: 4,
                                      fontWeight: 500,
                                      fontSize: 16
                                    }}>{item.from}→{item.to}</span>
                                  </td>
                                  <td style={{ padding: '6px 12px', textAlign: 'center', color: '#f5222d', fontWeight: 500 }}>{item.count}</td>
                                </tr>
                              ))
                            ) : (
                              <tr>
                                <td colSpan={3} style={{ padding: 40, textAlign: 'center', color: '#999' }}>无讹误</td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )
                })()}
              </div>

              {/* 衍文 - 表格形式 */}
              <div style={{ flex: '1 1 18%', minWidth: 200 }}>
                <div style={{ marginBottom: 12 }}>
                  <Tag color="warning" style={{ marginRight: 8 }}>衍文</Tag>
                  <Text type="secondary">共 {statistics.diff_details.inserted.length} 种，
                    {statistics.diff_details.inserted.reduce((sum, item) => sum + item.count, 0)} 处
                  </Text>
                </div>
                <div style={{
                  border: '1px solid #f0f0f0',
                  borderRadius: 6,
                  minHeight: 300,
                        maxHeight: 300,
                  overflowY: 'auto'
                }}>
                  {statistics.diff_details.inserted.length > 0 ? (
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                      <thead>
                        <tr style={{ background: '#fafafa', position: 'sticky', top: 0, zIndex: 1 }}>
                          <th style={{ padding: '8px 12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', width: 60, verticalAlign: 'middle' }}>序号</th>
                          <th style={{ padding: '8px 12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', verticalAlign: 'middle' }}>
                            <div style={{ fontSize: 11, color: '#1890ff', fontWeight: 'bold', marginBottom: 2 }}>底本 → 校本</div>
                            <div style={{ fontSize: 11, color: '#999', fontWeight: 'normal', lineHeight: 1.2 }}>{version1_name}</div>
                            <div style={{ fontSize: 11, color: '#999', fontWeight: 'normal', lineHeight: 1.2 }}>→ {version2_name}</div>
                          </th>
                          <th style={{ padding: '8px 12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', width: 60, verticalAlign: 'middle' }}>次数</th>
                        </tr>
                      </thead>
                      <tbody>
                        {statistics.diff_details.inserted.map((item, idx) => (
                          <tr
                            key={idx}
                            style={{
                              background: idx % 2 === 0 ? '#fff' : '#fafafa',
                              cursor: 'pointer',
                              transition: 'background 0.2s'
                            }}
                            onClick={() => jumpToCharDiff('insert', item.char)}
                            onMouseEnter={(e) => { e.currentTarget.style.background = '#fff7e6' }}
                            onMouseLeave={(e) => { e.currentTarget.style.background = idx % 2 === 0 ? '#fff' : '#fafafa' }}
                            title="点击跳转到正文对应位置"
                          >
                            <td style={{ padding: '6px 12px', textAlign: 'center', color: '#999' }}>{idx + 1}</td>
                            <td style={{ padding: '6px 12px', textAlign: 'center' }}>
                              <span style={{
                                background: '#ffe7ba',
                                color: '#d46b08',
                                padding: '2px 8px',
                                borderRadius: 4,
                                fontWeight: 500,
                                fontSize: 16
                              }}>{item.char}</span>
                            </td>
                            <td style={{ padding: '6px 12px', textAlign: 'center', color: '#fa8c16', fontWeight: 500 }}>{item.count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div style={{ padding: 16, textAlign: 'center', color: '#999' }}>无衍文</div>
                  )}
                </div>
              </div>

              {/* 脱文 - 表格形式 */}
              <div style={{ flex: '1 1 18%', minWidth: 200 }}>
                <div style={{ marginBottom: 12 }}>
                  <Tag color="purple" style={{ marginRight: 8 }}>脱文</Tag>
                  <Text type="secondary">共 {statistics.diff_details.deleted.length} 种，
                    {statistics.diff_details.deleted.reduce((sum, item) => sum + item.count, 0)} 处
                  </Text>
                </div>
                <div style={{
                  border: '1px solid #f0f0f0',
                  borderRadius: 6,
                  minHeight: 300,
                        maxHeight: 300,
                  overflowY: 'auto'
                }}>
                  {statistics.diff_details.deleted.length > 0 ? (
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                      <thead>
                        <tr style={{ background: '#fafafa', position: 'sticky', top: 0, zIndex: 1 }}>
                          <th style={{ padding: '8px 12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', width: 60, verticalAlign: 'middle' }}>序号</th>
                          <th style={{ padding: '8px 12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', verticalAlign: 'middle' }}>
                            <div style={{ fontSize: 11, color: '#1890ff', fontWeight: 'bold', marginBottom: 2 }}>底本 → 校本</div>
                            <div style={{ fontSize: 11, color: '#999', fontWeight: 'normal', lineHeight: 1.2 }}>{version1_name}</div>
                            <div style={{ fontSize: 11, color: '#999', fontWeight: 'normal', lineHeight: 1.2 }}>→ {version2_name}</div>
                          </th>
                          <th style={{ padding: '8px 12px', textAlign: 'center', borderBottom: '1px solid #f0f0f0', width: 60, verticalAlign: 'middle' }}>次数</th>
                        </tr>
                      </thead>
                      <tbody>
                        {statistics.diff_details.deleted.map((item, idx) => (
                          <tr
                            key={idx}
                            style={{
                              background: idx % 2 === 0 ? '#fff' : '#fafafa',
                              cursor: 'pointer',
                              transition: 'background 0.2s'
                            }}
                            onClick={() => jumpToCharDiff('delete', item.char)}
                            onMouseEnter={(e) => { e.currentTarget.style.background = '#f9f0ff' }}
                            onMouseLeave={(e) => { e.currentTarget.style.background = idx % 2 === 0 ? '#fff' : '#fafafa' }}
                            title="点击跳转到正文对应位置"
                          >
                            <td style={{ padding: '6px 12px', textAlign: 'center', color: '#999' }}>{idx + 1}</td>
                            <td style={{ padding: '6px 12px', textAlign: 'center' }}>
                              <span style={{
                                background: '#efdbff',
                                color: '#722ed1',
                                padding: '2px 8px',
                                borderRadius: 4,
                                fontWeight: 500,
                                fontSize: 16
                              }}>{item.char}</span>
                            </td>
                            <td style={{ padding: '6px 12px', textAlign: 'center', color: '#722ed1', fontWeight: 500 }}>{item.count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div style={{ padding: 16, textAlign: 'center', color: '#999' }}>无脱文</div>
                  )}
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* 逐句对齐对比 */}
        <Card
          title={
            <Space>
              <span>逐句对齐对比</span>
              <Tag color={categoryFilter !== 'all' ? 'blue' : 'default'}>
                {categoryFilter !== 'all'
                  ? `筛选后 ${filteredData.length} 条`
                  : `全部 ${aligned_sentences?.length || 0} 条`}
              </Tag>
            </Space>
          }
          extra={
            <Space size="large" wrap>
              {/* 展示布局切换 */}
              <Space>
                <span style={{ fontSize: 14, color: '#666' }}>布局：</span>
                <Radio.Group
                  value={displayMode}
                  onChange={e => {
                    setDisplayMode(e.target.value)
                    setCurrentPage(1)
                  }}
                  size="small"
                  optionType="button"
                  buttonStyle="solid"
                >
                  <Radio.Button value="side-by-side">
                    <SplitCellsOutlined /> 并排
                  </Radio.Button>
                  <Radio.Button value="inline">
                    <MenuOutlined /> 逐行
                  </Radio.Button>
                  <Radio.Button value="changes-only">
                    <DiffOutlined /> 聚焦
                  </Radio.Button>
                </Radio.Group>
              </Space>
            </Space>
          }
        >
          {aligned_sentences && aligned_sentences.length > 0 ? (
            <>
              {/* 差异定位导航条（从详细差异表格点击后显示） */}
              {diffNavigation && (
                <div style={{
                  marginBottom: 12,
                  padding: '10px 16px',
                  background: 'linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%)',
                  borderRadius: 6,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  border: '1px solid #91d5ff',
                  boxShadow: '0 2px 4px rgba(24, 144, 255, 0.1)'
                }}>
                  <Space size="middle">
                    <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                      🔍 定位差异：
                    </span>
                    <Tag color="blue" style={{ fontSize: 14, padding: '2px 10px' }}>
                      {diffNavigation.from && diffNavigation.to
                        ? `${diffNavigation.from}→${diffNavigation.to}`
                        : diffNavigation.char
                      }
                    </Tag>
                  </Space>

                  <Space size="middle">
                    <Button
                      size="small"
                      icon={<span>◀</span>}
                      onClick={navigateToPrevMatch}
                      disabled={diffNavigation.currentIndex === 0}
                    >
                      上一处
                    </Button>
                    <Space size={4}>
                      <InputNumber
                        size="small"
                        min={1}
                        max={diffNavigation.matchedRecords.length}
                        value={diffNavigation.currentIndex + 1}
                        onChange={(value) => {
                          if (value && value >= 1 && value <= diffNavigation.matchedRecords.length) {
                            navigateToMatch(value - 1)
                          }
                        }}
                        style={{ width: 60 }}
                      />
                      <span style={{ color: '#666' }}>/</span>
                      <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                        {diffNavigation.matchedRecords.length}
                      </span>
                    </Space>
                    <Button
                      size="small"
                      onClick={navigateToNextMatch}
                      disabled={diffNavigation.currentIndex === diffNavigation.matchedRecords.length - 1}
                    >
                      下一处 <span>▶</span>
                    </Button>
                    <Button
                      size="small"
                      type="text"
                      onClick={closeDiffNavigation}
                      style={{ color: '#999' }}
                    >
                      ✕ 关闭
                    </Button>
                  </Space>
                </div>
              )}

                            {/* 颜色图例说明 */}
              <div style={{
                marginBottom: 12,
                padding: '8px 16px',
                background: '#fafafa',
                borderRadius: 4,
                display: 'flex',
                alignItems: 'center',
                gap: 24,
                fontSize: 13,
                flexWrap: 'wrap'
              }}>
                <span style={{ color: '#666', fontWeight: 'bold' }}>颜色说明：</span>
                <span>
                  <span style={{
                    background: '#b7eb8f',
                    color: '#135200',
                    padding: '2px 6px',
                    borderRadius: 3,
                    fontWeight: 500,
                    marginRight: 4
                  }}>异体字</span>
                  同字异形
                </span>
                <span>
                  <span style={{
                    background: '#ffa39e',
                    color: '#a8071a',
                    padding: '2px 6px',
                    borderRadius: 3,
                    fontWeight: 500,
                    marginRight: 4
                  }}>讹误</span>
                  文字差异
                </span>
                <span>
                  <span style={{
                    background: '#ffd591',
                    color: '#ad4e00',
                    padding: '2px 6px',
                    borderRadius: 3,
                    fontWeight: 500,
                    marginRight: 4
                  }}>衍文</span>
                  校本有底本无
                </span>
                <span>
                  <span style={{
                    background: '#d3adf7',
                    color: '#391085',
                    padding: '2px 6px',
                    borderRadius: 3,
                    fontWeight: 500,
                    marginRight: 4
                  }}>脱文</span>
                  底本有校本无
                </span>
              </div>

              {/* 根据展示模式渲染不同布局 */}
              {displayMode === 'side-by-side' && (
                /* 左右并排布局 */
                <div style={{ border: '1px solid #d9d9d9', borderRadius: 4, overflow: 'hidden', width: '100%' }}>
                  {/* 表头 */}
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '60px minmax(0, 1fr) minmax(0, 1fr)',
                      borderBottom: '2px solid #d9d9d9',
                      background: '#fafafa',
                    }}
                  >
                    <div style={{ padding: '12px 16px', borderRight: '1px solid #d9d9d9', fontWeight: 600, fontSize: 14, textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      序号
                    </div>
                    <div style={{ padding: '12px 16px', borderRight: '1px solid #d9d9d9', fontWeight: 600, fontSize: 14, textAlign: 'center' }}>
                      <div style={{ color: '#333', fontSize: 12, marginBottom: 4 }}>底本</div>
                      <div style={{ fontSize: 14, color: '#333', fontWeight: 600 }}>{version1_name}</div>
                    </div>
                    <div style={{ padding: '12px 16px', fontWeight: 600, fontSize: 14, textAlign: 'center' }}>
                      <div style={{ color: '#333', fontSize: 12, marginBottom: 4 }}>校本</div>
                      <div style={{ fontSize: 14, color: '#333', fontWeight: 600 }}>{version2_name}</div>
                    </div>
                  </div>

                  {/* 对齐句子列表 */}
                  <div>
                    {currentPageData.map((record, index) => {
                      // 奇偶交替底色，不再根据差异类型染色（字符级高亮已足够）
                      const isEvenRow = index % 2 === 1
                      const rowBgColor = isEvenRow ? '#fafafa' : '#ffffff'
                      const hoverBgColor = '#e6f7ff'

                      return (
                        <div
                          key={record.id}
                          id={`aligned-row-${record.id}`}
                          style={{
                            display: 'grid',
                            gridTemplateColumns: '60px minmax(0, 1fr) minmax(0, 1fr)',
                            borderBottom: '1px solid #f0f0f0',
                            background: rowBgColor,
                            transition: 'background 0.2s',
                          }}
                          onMouseEnter={(e) => { e.currentTarget.style.background = hoverBgColor }}
                          onMouseLeave={(e) => { e.currentTarget.style.background = rowBgColor }}
                        >
                          <div style={{ padding: '8px 12px', borderRight: '1px solid #e8e8e8', textAlign: 'center', color: '#666', fontSize: 14 }}>
                            {record.id}
                          </div>
                          <div style={{ padding: '8px 16px', borderRight: '1px solid #e8e8e8', fontFamily: "'Noto Serif SC', serif", fontSize: 16, lineHeight: 2, wordBreak: 'break-word', overflowWrap: 'break-word', whiteSpace: 'pre-wrap', overflow: 'hidden', color: record.sentence1 ? 'inherit' : '#999' }}>
                            {record.has_diff && record.char_diff && record.char_diff.segments1
                              ? renderCharHighlight(record.char_diff.segments1)
                              : renderPlainText(record.sentence1)}
                          </div>
                          <div style={{ padding: '8px 16px', fontFamily: "'Noto Serif SC', serif", fontSize: 16, lineHeight: 2, wordBreak: 'break-word', overflowWrap: 'break-word', whiteSpace: 'pre-wrap', overflow: 'hidden', color: record.sentence2 ? 'inherit' : '#999' }}>
                            {record.has_diff && record.char_diff && record.char_diff.segments2
                              ? renderCharHighlight(record.char_diff.segments2)
                              : renderPlainText(record.sentence2)}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {displayMode === 'inline' && (
                /* 逐行视图：上下排列 */
                <div style={{ border: '1px solid #d9d9d9', borderRadius: 4, overflow: 'hidden', width: '100%' }}>
                  {currentPageData.map((record, index) => {
                    // 奇偶交替底色，不再根据差异染色
                    const isEvenRow = index % 2 === 1
                    const cardBgColor = isEvenRow ? '#fafafa' : '#ffffff'

                    return (
                      <div
                        key={record.id}
                        id={`aligned-row-${record.id}`}
                        style={{
                          borderBottom: '1px solid #e8e8e8',
                          background: cardBgColor,
                          padding: '12px 16px',
                        }}
                      >
                        {/* 序号标签 */}
                        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                          <Tag color={record.has_diff ? 'orange' : 'default'}>#{record.id}</Tag>
                          {record.has_diff && <Tag color="warning" style={{ marginLeft: 8 }}>有差异</Tag>}
                        </div>

                        {/* 底本行 */}
                        <div style={{ display: 'flex', marginBottom: 6 }}>
                          <Tag color="blue" style={{ flexShrink: 0, marginRight: 8 }}>{version1_name}</Tag>
                          <div style={{ fontFamily: "'Noto Serif SC', serif", fontSize: 16, lineHeight: 1.8, flex: 1 }}>
                            {record.has_diff && record.char_diff && record.char_diff.segments1
                              ? renderCharHighlight(record.char_diff.segments1)
                              : renderPlainText(record.sentence1)}
                          </div>
                        </div>

                        {/* 校本行 */}
                        <div style={{ display: 'flex' }}>
                          <Tag color="green" style={{ flexShrink: 0, marginRight: 8 }}>{version2_name}</Tag>
                          <div style={{ fontFamily: "'Noto Serif SC', serif", fontSize: 16, lineHeight: 1.8, flex: 1 }}>
                            {record.has_diff && record.char_diff && record.char_diff.segments2
                              ? renderCharHighlight(record.char_diff.segments2)
                              : renderPlainText(record.sentence2)}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              {displayMode === 'changes-only' && (
                /* 差异聚焦视图：只展示差异部分，紧凑卡片 */
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {currentPageData.filter(r => r.has_diff).length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '40px 0', color: '#999', background: '#fafafa', borderRadius: 8 }}>
                      当前页无差异记录
                    </div>
                  ) : (
                    currentPageData.filter(r => r.has_diff).map((record) => {
                      // 确定差异类型颜色
                      let borderColor = '#faad14' // 默认橙色
                      let diffTypeLabel = '文字差异'
                      const diffType = record.char_diff?.diff_type

                      if (diffType === 'punct_only') {
                        borderColor = '#1890ff'
                        diffTypeLabel = '标点差异'
                      } else if (diffType === 'text_only') {
                        borderColor = '#f5222d'
                        diffTypeLabel = '文字差异'
                      } else if (diffType === 'mixed') {
                        borderColor = '#722ed1'
                        diffTypeLabel = '混合差异'
                      }

                      return (
                        <div
                          key={record.id}
                          id={`aligned-row-${record.id}`}
                          style={{
                            border: `2px solid ${borderColor}`,
                            borderRadius: 8,
                            overflow: 'hidden',
                            background: '#fff',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                          }}
                        >
                          {/* 卡片头部 */}
                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '8px 16px',
                            background: `${borderColor}15`,
                            borderBottom: `1px solid ${borderColor}30`,
                          }}>
                            <Space>
                              <Tag color={borderColor}>#{record.id}</Tag>
                              <Tag color={borderColor}>{diffTypeLabel}</Tag>
                            </Space>
                          </div>

                          {/* 差异内容 */}
                          <div style={{ padding: '16px' }}>
                            {/* 底本 */}
                            <div style={{ marginBottom: 12 }}>
                              <div style={{ fontSize: 12, color: '#1890ff', fontWeight: 600, marginBottom: 4 }}>
                                底本 · {version1_name}
                              </div>
                              <div style={{
                                fontFamily: "'Noto Serif SC', serif",
                                fontSize: 18,
                                lineHeight: 2,
                                padding: '8px 12px',
                                background: '#f0f5ff',
                                borderRadius: 4,
                                borderLeft: '3px solid #1890ff',
                              }}>
                                {record.char_diff && record.char_diff.segments1
                                  ? renderCharHighlight(record.char_diff.segments1)
                                  : renderPlainText(record.sentence1)}
                              </div>
                            </div>

                            {/* 校本 */}
                            <div>
                              <div style={{ fontSize: 12, color: '#52c41a', fontWeight: 600, marginBottom: 4 }}>
                                校本 · {version2_name}
                              </div>
                              <div style={{
                                fontFamily: "'Noto Serif SC', serif",
                                fontSize: 18,
                                lineHeight: 2,
                                padding: '8px 12px',
                                background: '#f6ffed',
                                borderRadius: 4,
                                borderLeft: '3px solid #52c41a',
                              }}>
                                {record.char_diff && record.char_diff.segments2
                                  ? renderCharHighlight(record.char_diff.segments2)
                                  : renderPlainText(record.sentence2)}
                              </div>
                            </div>
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>
              )}

              {/* 分页控件 */}
              <div style={{ marginTop: 16, textAlign: 'center' }}>
                <Pagination
                  current={currentPage}
                  pageSize={pageSize}
                  total={filteredData.length}
                  onChange={(page, newPageSize) => {
                    if (newPageSize !== pageSize) {
                      // 切换每页数量时，跳转到第1页
                      setPageSize(newPageSize)
                      setCurrentPage(1)
                    } else {
                      // 只是翻页
                      setCurrentPage(page)
                    }
                  }}
                  showSizeChanger
                  showQuickJumper
                  showTotal={(total) =>
                    categoryFilter !== 'all'
                      ? `筛选后 ${total} 条（总计 ${aligned_sentences?.length || 0} 条）`
                      : `共 ${total} 条对齐记录`
                  }
                  pageSizeOptions={['20', '50', '100', '200']}
                />
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
              暂无对齐数据
            </div>
          )}
        </Card>
      </Space>

      {/* 校勘记预览模态框 */}
      <Modal
        title={
          <Space>
            <EyeOutlined />
            <span>校勘记预览</span>
            <Tag color="blue">{previewFormat === 'txt' ? '陈垣体例' : 'TEI-XML'}</Tag>
          </Space>
        }
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        width={900}
        footer={[
          <Button key="close" onClick={() => setPreviewModalVisible(false)}>
            关闭
          </Button>,
          <Button
            key="download"
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => {
              exportCollationNotes(previewFormat)
              setPreviewModalVisible(false)
            }}
          >
            下载此格式
          </Button>,
        ]}
      >
        {previewLoading ? (
          <div style={{ textAlign: 'center', padding: 60 }}>
            <Spin size="large" />
            <div style={{ marginTop: 16, color: '#666' }}>正在生成校勘记...</div>
          </div>
        ) : (
          <div>
            {/* 格式切换 */}
            <div style={{ marginBottom: 16 }}>
              <Radio.Group
                value={previewFormat}
                onChange={e => previewCollationNotes(e.target.value)}
                optionType="button"
                buttonStyle="solid"
              >
                <Radio.Button value="txt">TXT 格式（陈垣体例）</Radio.Button>
                <Radio.Button value="tei-xml">TEI-XML 格式</Radio.Button>
              </Radio.Group>
            </div>

            {/* 预览内容 */}
            <div
              style={{
                background: previewFormat === 'tei-xml' ? '#1e1e1e' : '#fafafa',
                color: previewFormat === 'tei-xml' ? '#d4d4d4' : '#333',
                padding: 20,
                borderRadius: 8,
                fontFamily: previewFormat === 'tei-xml' ? "'Fira Code', 'Consolas', monospace" : "'Noto Serif SC', serif",
                fontSize: previewFormat === 'tei-xml' ? 13 : 15,
                lineHeight: previewFormat === 'tei-xml' ? 1.6 : 2,
                maxHeight: 500,
                overflow: 'auto',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                border: '1px solid #d9d9d9',
              }}
            >
              {previewContent || '暂无内容'}
            </div>

            {/* 统计信息 */}
            <div style={{ marginTop: 12, color: '#999', fontSize: 12 }}>
              共 {previewContent.split('\n').length} 行，约 {previewContent.length.toLocaleString()} 字符
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
