/**
 * 文字校勘视图自定义 Hooks
 */

import { useState, useMemo, useEffect, useCallback } from 'react'
import type {
  AlignedSentence,
  CategoryFilter,
  DisplayMode,
  HighlightedChar,
  DiffNavigation,
} from './types'
import {
  filterByCategory,
  findMatchedRecords,
  calculateTargetPage,
  scrollToRecord,
} from './utils'
import { DEFAULT_PAGE_SIZE } from './constants'

/**
 * 分页 Hook
 */
export function usePagination(
  filteredData: AlignedSentence[],
  defaultPageSize: number = DEFAULT_PAGE_SIZE
) {
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(defaultPageSize)

  const startIndex = (currentPage - 1) * pageSize
  const endIndex = startIndex + pageSize
  const currentPageData = filteredData.slice(startIndex, endIndex)

  // 当筛选数据变化时重置到第一页
  useEffect(() => {
    setCurrentPage(1)
  }, [filteredData.length])

  return {
    currentPage,
    setCurrentPage,
    pageSize,
    setPageSize,
    currentPageData,
    startIndex,
    endIndex,
  }
}

/**
 * 视图模式 Hook
 */
export function useViewMode() {
  const [displayMode, setDisplayMode] = useState<DisplayMode>('side-by-side')
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>('all')

  return {
    displayMode,
    setDisplayMode,
    categoryFilter,
    setCategoryFilter,
  }
}

/**
 * 差异导航 Hook
 */
export function useDiffNavigation(
  alignedSentences: AlignedSentence[] | undefined,
  filteredData: AlignedSentence[],
  pageSize: number,
  setCurrentPage: (page: number) => void
) {
  const [highlightedChar, setHighlightedChar] = useState<HighlightedChar | null>(null)
  const [diffNavigation, setDiffNavigation] = useState<DiffNavigation | null>(null)

  // 跳转到指定索引的匹配记录
  const navigateToMatch = useCallback((index: number) => {
    if (!diffNavigation || index < 0 || index >= diffNavigation.matchedRecords.length) {
      return
    }

    const targetRecord = diffNavigation.matchedRecords[index]
    setDiffNavigation(prev => prev ? { ...prev, currentIndex: index } : null)

    const targetIndexInFiltered = filteredData.findIndex(r => r.id === targetRecord.id)

    if (targetIndexInFiltered >= 0) {
      const targetPage = calculateTargetPage(targetIndexInFiltered, pageSize)
      setCurrentPage(targetPage)
      setHighlightedChar({
        type: diffNavigation.type,
        char: diffNavigation.char,
        from: diffNavigation.from,
        to: diffNavigation.to
      })

      scrollToRecord(targetRecord.id)

      // 3秒后清除高亮（但保留导航状态）
      setTimeout(() => {
        setHighlightedChar(null)
      }, 3000)
    }
  }, [diffNavigation, filteredData, pageSize, setCurrentPage])

  // 上一处
  const navigateToPrevMatch = useCallback(() => {
    if (diffNavigation && diffNavigation.currentIndex > 0) {
      navigateToMatch(diffNavigation.currentIndex - 1)
    }
  }, [diffNavigation, navigateToMatch])

  // 下一处
  const navigateToNextMatch = useCallback(() => {
    if (diffNavigation && diffNavigation.currentIndex < diffNavigation.matchedRecords.length - 1) {
      navigateToMatch(diffNavigation.currentIndex + 1)
    }
  }, [diffNavigation, navigateToMatch])

  // 关闭导航
  const closeDiffNavigation = useCallback(() => {
    setDiffNavigation(null)
    setHighlightedChar(null)
  }, [])

  // 跳转到包含指定差异字符的段落
  const jumpToCharDiff = useCallback((
    type: 'replace' | 'delete' | 'insert',
    char?: string,
    from?: string,
    to?: string
  ) => {
    if (!alignedSentences) return

    const matchedRecords = findMatchedRecords(alignedSentences, type, char, from, to)

    if (matchedRecords.length > 0) {
      setDiffNavigation({
        type,
        char,
        from,
        to,
        matchedRecords,
        currentIndex: 0
      })

      const targetRecord = matchedRecords[0]
      const targetIndexInFiltered = filteredData.findIndex(r => r.id === targetRecord.id)

      if (targetIndexInFiltered >= 0) {
        const targetPage = calculateTargetPage(targetIndexInFiltered, pageSize)
        setCurrentPage(targetPage)
        setHighlightedChar({ type, char, from, to })
        scrollToRecord(targetRecord.id)

        // 3秒后清除高亮
        setTimeout(() => {
          setHighlightedChar(null)
        }, 3000)
      }
    } else {
      setDiffNavigation(null)
    }
  }, [alignedSentences, filteredData, pageSize, setCurrentPage])

  return {
    highlightedChar,
    setHighlightedChar,
    diffNavigation,
    setDiffNavigation,
    navigateToMatch,
    navigateToPrevMatch,
    navigateToNextMatch,
    closeDiffNavigation,
    jumpToCharDiff,
  }
}

/**
 * 初始高亮定位 Hook
 */
export function useInitialHighlight(
  initialHighlight: { char: string; type?: 'replace' | 'delete' | 'insert' } | undefined,
  alignedSentences: AlignedSentence[] | undefined,
  pageSize: number,
  setCurrentPage: (page: number) => void,
  setHighlightedChar: (char: HighlightedChar | null) => void,
  setDiffNavigation: (nav: DiffNavigation | null) => void
) {
  useEffect(() => {
    if (initialHighlight && initialHighlight.char && alignedSentences && alignedSentences.length > 0) {
      // 延迟执行，确保组件渲染完成
      setTimeout(() => {
        const matchedRecords: AlignedSentence[] = []

        for (const record of alignedSentences) {
          if (!record.has_diff || !record.char_diff) continue

          const segments1 = record.char_diff.segments1 || []
          const segments2 = record.char_diff.segments2 || []

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

        if (matchedRecords.length > 0) {
          const targetRecord = matchedRecords[0]

          setDiffNavigation({
            type: initialHighlight.type || 'replace',
            char: initialHighlight.char,
            matchedRecords,
            currentIndex: 0
          })

          const targetIndex = alignedSentences.findIndex(r => r.id === targetRecord.id)
          if (targetIndex >= 0) {
            const targetPage = calculateTargetPage(targetIndex, pageSize)
            setCurrentPage(targetPage)

            setHighlightedChar({
              type: initialHighlight.type || 'replace',
              char: initialHighlight.char
            })

            setTimeout(() => {
              scrollToRecord(targetRecord.id)
            }, 200)

            // 3秒后清除高亮
            setTimeout(() => {
              setHighlightedChar(null)
            }, 3000)
          }
        }
      }, 300)
    }
  }, [initialHighlight, alignedSentences, pageSize, setCurrentPage, setHighlightedChar, setDiffNavigation])
}

/**
 * 数据过滤 Hook
 */
export function useFilteredData(
  alignedSentences: AlignedSentence[] | undefined,
  categoryFilter: CategoryFilter
) {
  const filteredData = useMemo(
    () => filterByCategory(alignedSentences, categoryFilter),
    [alignedSentences, categoryFilter]
  )

  return filteredData
}
