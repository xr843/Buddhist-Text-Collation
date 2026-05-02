/**
 * 方案B - 混合对比视图组件（主视图+浮动审核面板）
 *
 * 功能：
 * 1. 左侧并排对比视图
 * 2. 右侧固定审核面板
 * 3. 智能高亮和滚动
 * 4. 批量操作支持
 * 5. 快捷键支持
 */

import { useState, useEffect, useCallback } from 'react'
import { Button, Space, message, Statistic, Tag } from 'antd'
import type { PunctuationComparisonResponse } from '../types'
import SideBySideView from './SideBySideView'
import ReviewPanel from './ReviewPanel'
import './HybridComparisonView.css'

interface HybridComparisonViewProps {
  result: PunctuationComparisonResponse
  version1Name: string
  version2Name: string
}

export default function HybridComparisonView({
  result,
  version1Name,
  version2Name
}: HybridComparisonViewProps) {
  // 状态管理
  const [currentIndex, setCurrentIndex] = useState(0)
  const [reviewStatus, setReviewStatus] = useState<boolean[]>(
    new Array(result.punctuation_analysis.differences.length).fill(false)
  )
  const [notes, setNotes] = useState<string[]>(
    new Array(result.punctuation_analysis.differences.length).fill('')
  )
  const [selectedDiffs, setSelectedDiffs] = useState<Set<number>>(new Set())
  const [panelVisible, setPanelVisible] = useState(true)

  const differences = result.punctuation_analysis.differences

  // 统计信息
  const reviewedCount = reviewStatus.filter(r => r).length
  const progress = Math.round((reviewedCount / differences.length) * 100)

  // 滚动到指定差异
  const scrollToDiff = useCallback((index: number) => {
    const element = document.getElementById(`diff-${index}-a`)
    if (element) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      })
    }
  }, [])

  // 切换到指定差异
  const handleDiffClick = useCallback((index: number) => {
    if (currentIndex !== index) {
      setCurrentIndex(index)
      scrollToDiff(index)
    }
  }, [currentIndex, scrollToDiff])

  // 标记当前差异为已审核
  const markCurrentAsReviewed = useCallback(() => {
    setReviewStatus(prev => {
      const newStatus = [...prev]
      newStatus[currentIndex] = true
      return newStatus
    })
    message.success('已标记为已审核')

    // 自动跳到下一个
    setTimeout(() => {
      if (currentIndex < differences.length - 1) {
        setCurrentIndex(currentIndex + 1)
        scrollToDiff(currentIndex + 1)
      }
    }, 300)
  }, [currentIndex, differences.length, scrollToDiff])

  // 上一个差异
  const gotoPrevious = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
      scrollToDiff(currentIndex - 1)
    }
  }, [currentIndex, scrollToDiff])

  // 下一个差异
  const gotoNext = useCallback(() => {
    if (currentIndex < differences.length - 1) {
      setCurrentIndex(currentIndex + 1)
      scrollToDiff(currentIndex + 1)
    }
  }, [currentIndex, differences.length, scrollToDiff])

  // 保存备注
  const saveNote = useCallback((note: string) => {
    setNotes(prev => {
      const newNotes = [...prev]
      newNotes[currentIndex] = note
      return newNotes
    })
  }, [currentIndex])

  // 复选框变化
  const handleCheckboxChange = useCallback((index: number, checked: boolean) => {
    setSelectedDiffs(prev => {
      const newSet = new Set(prev)
      if (checked) {
        newSet.add(index)
      } else {
        newSet.delete(index)
      }
      return newSet
    })
  }, [])

  // 批量标记已审核
  const batchReview = useCallback(() => {
    setReviewStatus(prev => {
      const newStatus = [...prev]
      selectedDiffs.forEach(index => {
        newStatus[index] = true
      })
      return newStatus
    })
    message.success(`已批量标记 ${selectedDiffs.size} 个差异为已审核`)
    setSelectedDiffs(new Set())
  }, [selectedDiffs])

  // 取消选择
  const cancelSelection = useCallback(() => {
    setSelectedDiffs(new Set())
  }, [])

  // 全部标记为已审核
  const markAllAsReviewed = useCallback(() => {
    setReviewStatus(new Array(differences.length).fill(true))
    message.success('已将所有差异标记为已审核')
  }, [differences.length])

  // 切换面板显示
  const togglePanel = useCallback(() => {
    setPanelVisible(prev => !prev)
  }, [])

  // 快捷键支持
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // 如果焦点在输入框，不响应快捷键
      if ((e.target as HTMLElement).tagName === 'TEXTAREA') return

      switch(e.key) {
        case 'ArrowLeft':
          e.preventDefault()
          gotoPrevious()
          break
        case 'ArrowRight':
          e.preventDefault()
          gotoNext()
          break
        case 'Enter':
          e.preventDefault()
          markCurrentAsReviewed()
          break
        case ' ':
          e.preventDefault()
          gotoNext()
          break
        case 'Escape':
          e.preventDefault()
          if (panelVisible) {
            togglePanel()
          }
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [gotoPrevious, gotoNext, markCurrentAsReviewed, panelVisible, togglePanel])

  return (
    <div className="hybrid-comparison-view">
      {/* 统计栏 */}
      <div className="stats-bar">
        <Space size="large">
          <Statistic title="总差异数" value={differences.length} />
          <Statistic
            title="已审核"
            value={reviewedCount}
            valueStyle={{ color: '#409EFF' }}
          />
          <Statistic title="标点差异" value={result.punctuation_analysis.research_stats.total_count} />
          <div style={{ fontSize: 14, color: '#67C23A', fontWeight: 500 }}>
            进度: {progress}%
          </div>
        </Space>

        <Space>
          {selectedDiffs.size > 0 && (
            <>
              <Tag color="blue">已选中 {selectedDiffs.size} 个</Tag>
              <Button size="small" type="primary" onClick={batchReview}>
                批量标记已审核
              </Button>
              <Button size="small" onClick={cancelSelection}>
                取消选择
              </Button>
            </>
          )}
          <Button type="primary" ghost onClick={markAllAsReviewed}>
            全部标记为已审核
          </Button>
          <Button type="primary" onClick={togglePanel}>
            {panelVisible ? '隐藏' : '显示'}审核面板
          </Button>
        </Space>
      </div>

      {/* 主内容区 */}
      <div className="content-wrapper">
        {/* 并排对比视图 */}
        <SideBySideView
          differences={differences}
          version1Name={version1Name}
          version2Name={version2Name}
          text1={result.text1}
          text2={result.text2}
          currentIndex={currentIndex}
          reviewStatus={reviewStatus}
          selectedDiffs={selectedDiffs}
          onDiffClick={handleDiffClick}
          onCheckboxChange={handleCheckboxChange}
        />

        {/* 审核面板 */}
        {panelVisible && (
          <ReviewPanel
            difference={differences[currentIndex]}
            allDifferences={differences}
            currentIndex={currentIndex}
            totalCount={differences.length}
            reviewedCount={reviewedCount}
            progress={progress}
            isReviewed={reviewStatus[currentIndex]}
            note={notes[currentIndex]}
            version1Name={version1Name}
            version2Name={version2Name}
            canGoPrev={currentIndex > 0}
            canGoNext={currentIndex < differences.length - 1}
            reviewStatus={reviewStatus}
            onReview={markCurrentAsReviewed}
            onPrevious={gotoPrevious}
            onNext={gotoNext}
            onSkip={gotoNext}
            onNoteChange={saveNote}
            onDifferenceSelect={(index) => setCurrentIndex(index)}
            onClose={togglePanel}
          />
        )}
      </div>

      {/* 快捷键提示 */}
      <div className="shortcut-hint">
        <Space>
          <span><kbd>←</kbd> <kbd>→</kbd> 切换差异</span>
          <span><kbd>Enter</kbd> 标记已审核</span>
          <span><kbd>Space</kbd> 跳过</span>
          <span><kbd>Esc</kbd> 关闭面板</span>
        </Space>
      </div>
    </div>
  )
}
