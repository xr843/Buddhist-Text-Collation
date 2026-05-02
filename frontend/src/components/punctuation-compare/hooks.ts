/**
 * 标点对比视图 Hooks
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import type { PunctuationDifference, SplitLine, ScrollTarget } from './types'
import { findLineIndexForDiff } from './utils'
import { PAGE_SIZE, DIFF_ONLY_PAGE_SIZE } from './constants'

/**
 * 分页与视图模式 Hook
 */
export function usePagination(splitLines: SplitLine[], diffOnlyMode: boolean) {
  const [currentPage, setCurrentPage] = useState(1)

  // 仅差异模式：过滤出包含差异的行
  const filteredLines = useMemo(() => {
    if (!diffOnlyMode) {
      return splitLines
    }
    return splitLines.filter(line => line.hasDiff)
  }, [splitLines, diffOnlyMode])

  // 分页数据
  const pageSize = diffOnlyMode ? DIFF_ONLY_PAGE_SIZE : PAGE_SIZE
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize
    const endIndex = startIndex + pageSize
    return filteredLines.slice(startIndex, endIndex)
  }, [filteredLines, currentPage, pageSize])

  // 模式切换时重置页码
  useEffect(() => {
    setCurrentPage(1)
  }, [diffOnlyMode])

  return {
    currentPage,
    setCurrentPage,
    filteredLines,
    paginatedData,
    pageSize,
  }
}

/**
 * 滚动到差异 Hook
 */
export function useScrollToDiff(
  scrollToDiffId: number | null | undefined,
  filteredLines: SplitLine[],
  differences: PunctuationDifference[],
  diffOnlyMode: boolean,
  currentPage: number,
  setCurrentPage: (page: number) => void,
  scrollContainerRef: React.RefObject<HTMLDivElement>
) {
  const scrollTargetRef = useRef<ScrollTarget | null>(null)
  const currentPageRef = useRef(currentPage)

  useEffect(() => {
    currentPageRef.current = currentPage
  }, [currentPage])

  // 执行滚动
  const scrollToLine = useCallback((lineId: string) => {
    setTimeout(() => {
      const rowElement = document.querySelector(`[data-line-id="${lineId}"]`) as HTMLElement
      const container = scrollContainerRef.current

      if (rowElement && container) {
        const containerRect = container.getBoundingClientRect()
        const rowRect = rowElement.getBoundingClientRect()
        const scrollTop = rowElement.offsetTop - container.offsetTop - (containerRect.height / 2) + (rowRect.height / 2)

        container.scrollTo({
          top: Math.max(0, scrollTop),
          behavior: 'smooth'
        })

        // 添加高亮效果
        rowElement.style.transition = 'background-color 0.3s'
        rowElement.style.backgroundColor = '#fff7e6'
        setTimeout(() => {
          rowElement.style.backgroundColor = ''
        }, 1500)
      }
    }, 100)
  }, [scrollContainerRef])

  // 监听 scrollToDiffId 变化
  useEffect(() => {
    if (scrollToDiffId) {
      const targetDiff = differences.find(d => d.id === scrollToDiffId)
      if (!targetDiff) return

      const lineIndex = findLineIndexForDiff(filteredLines, targetDiff)

      if (lineIndex !== -1) {
        const pageSize = diffOnlyMode ? DIFF_ONLY_PAGE_SIZE : PAGE_SIZE
        const targetPage = Math.floor(lineIndex / pageSize) + 1
        const targetLineId = filteredLines[lineIndex]?.id

        if (targetPage === currentPageRef.current) {
          scrollToLine(targetLineId)
        } else {
          scrollTargetRef.current = { lineId: targetLineId, page: targetPage }
          setCurrentPage(targetPage)
        }
      }
    }
  }, [scrollToDiffId, filteredLines, differences, diffOnlyMode, setCurrentPage, scrollToLine])

  // 页面变化后执行滚动
  useEffect(() => {
    if (scrollTargetRef.current && scrollTargetRef.current.page === currentPage) {
      const { lineId } = scrollTargetRef.current
      scrollToLine(lineId)
      scrollTargetRef.current = null
    }
  }, [currentPage, scrollToLine])

  return { scrollToLine }
}

/**
 * 视图模式 Hook
 */
export function useViewMode() {
  const [diffOnlyMode, setDiffOnlyMode] = useState(false)
  const [charsPerLine, setCharsPerLine] = useState(60)

  return {
    diffOnlyMode,
    setDiffOnlyMode,
    charsPerLine,
    setCharsPerLine,
  }
}
