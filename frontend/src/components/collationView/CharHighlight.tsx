/**
 * 字符级高亮渲染组件
 * 从 CollationView.tsx 中提取
 */
import type { CharSegment } from '../../types/collationView'

interface CharHighlightProps {
  segments: CharSegment[] | undefined
}

/**
 * 渲染字符级高亮
 */
export default function CharHighlight({ segments }: CharHighlightProps) {
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

/**
 * 渲染普通文本
 */
export function renderPlainText(text: string | undefined, emptySymbol: string = '∅') {
  if (!text) return <span style={{ color: '#999' }}>{emptySymbol}</span>
  return text
}
