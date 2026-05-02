/**
 * 可拖拽分屏组件
 *
 * 基于 react-split 封装，提供：
 * - 水平/垂直分屏
 * - 可拖拽调整比例
 * - 记忆分屏比例
 * - 主题适配
 */
import { useCallback, useState } from 'react'
import Split from 'react-split'
import './SplitPane.css'

export interface SplitPaneProps {
  /** 分屏方向 */
  direction?: 'horizontal' | 'vertical'
  /** 初始比例 [左/上, 右/下] */
  sizes?: [number, number]
  /** 最小尺寸 (像素) */
  minSize?: number
  /** 拖拽条尺寸 */
  gutterSize?: number
  /** 是否允许折叠 */
  collapsible?: boolean
  /** 存储 key（用于记忆比例） */
  storageKey?: string
  /** 左/上面板内容 */
  left?: React.ReactNode
  /** 右/下面板内容 */
  right?: React.ReactNode
  /** 上面板内容（垂直模式） */
  top?: React.ReactNode
  /** 下面板内容（垂直模式） */
  bottom?: React.ReactNode
  /** 子元素（替代 left/right） */
  children?: React.ReactNode
  /** 尺寸变化回调 */
  onSizesChange?: (sizes: number[]) => void
  /** 自定义类名 */
  className?: string
  /** 自定义样式 */
  style?: React.CSSProperties
}

export default function SplitPane({
  direction = 'horizontal',
  sizes: initialSizes = [50, 50],
  minSize = 100,
  gutterSize = 8,
  collapsible = false,
  storageKey,
  left,
  right,
  top,
  bottom,
  children,
  onSizesChange,
  className = '',
  style,
}: SplitPaneProps) {
  // 从 localStorage 恢复比例
  const getSavedSizes = useCallback((): [number, number] => {
    if (!storageKey) return initialSizes
    try {
      const saved = localStorage.getItem(`splitPane:${storageKey}`)
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed) && parsed.length === 2) {
          return parsed as [number, number]
        }
      }
    } catch {
      // ignore
    }
    return initialSizes
  }, [storageKey, initialSizes])

  const [sizes, setSizes] = useState<[number, number]>(getSavedSizes)

  // 保存比例到 localStorage
  const saveSizes = useCallback(
    (newSizes: number[]) => {
      if (storageKey && newSizes.length === 2) {
        localStorage.setItem(`splitPane:${storageKey}`, JSON.stringify(newSizes))
      }
    },
    [storageKey]
  )

  // 处理拖拽结束
  const handleDragEnd = useCallback(
    (newSizes: number[]) => {
      setSizes(newSizes as [number, number])
      saveSizes(newSizes)
      onSizesChange?.(newSizes)
    },
    [saveSizes, onSizesChange]
  )

  // 双击折叠/展开
  const handleGutterDoubleClick = useCallback(() => {
    if (!collapsible) return

    // 如果左侧/上侧已折叠，展开；否则折叠
    const newSizes: [number, number] =
      sizes[0] < 10 ? [50, 50] : [0, 100]
    setSizes(newSizes)
    saveSizes(newSizes)
    onSizesChange?.(newSizes)
  }, [collapsible, sizes, saveSizes, onSizesChange])

  // 确定面板内容
  const panels = children
    ? (Array.isArray(children) ? children : [children])
    : direction === 'horizontal'
      ? [left, right]
      : [top, bottom]

  // 确保有两个面板
  if (panels.length < 2) {
    console.warn('SplitPane requires exactly 2 children')
    return <div className={className} style={style}>{panels[0]}</div>
  }

  return (
    <Split
      className={`split-pane split-pane-${direction} ${className}`}
      sizes={sizes}
      minSize={minSize}
      gutterSize={gutterSize}
      direction={direction}
      onDragEnd={handleDragEnd}
      gutter={(_index, gutterDirection) => {
        const gutter = document.createElement('div')
        gutter.className = `split-gutter split-gutter-${gutterDirection}`
        if (collapsible) {
          gutter.ondblclick = handleGutterDoubleClick
          gutter.title = '双击折叠/展开'
        }
        return gutter
      }}
      style={style}
    >
      <div className="split-pane-panel">{panels[0]}</div>
      <div className="split-pane-panel">{panels[1]}</div>
    </Split>
  )
}
