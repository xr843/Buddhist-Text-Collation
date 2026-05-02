/**
 * 颜色提示组件
 */

import { Typography } from 'antd'
import { PUNCT_COLORS } from './constants'

const { Text } = Typography

export default function ColorHint() {
  return (
    <div
      style={{
        padding: '8px 16px',
        background: '#f7f7f7',
        borderTop: '1px solid #d9d9d9',
        fontSize: 12,
        color: '#666',
      }}
    >
      <Text type="secondary">
        提示：
        <span
          style={{
            backgroundColor: PUNCT_COLORS.sentenceEnd,
            color: '#fff',
            padding: '0 4px',
            margin: '0 4px',
            borderRadius: 2,
          }}
        >
          红色
        </span>
        句末点号（。？！）；
        <span
          style={{
            backgroundColor: PUNCT_COLORS.sentenceInner,
            color: '#fff',
            padding: '0 4px',
            margin: '0 4px',
            borderRadius: 2,
          }}
        >
          蓝色
        </span>
        句内点号（，、；：）；
        <span
          style={{
            backgroundColor: PUNCT_COLORS.mark,
            color: '#fff',
            padding: '0 4px',
            margin: '0 4px',
            borderRadius: 2,
          }}
        >
          紫色
        </span>
        标号（引号、括号等）。点击可查看详情。
      </Text>
    </div>
  )
}
