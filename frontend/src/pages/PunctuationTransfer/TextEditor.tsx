/**
 * 文本编辑器组件
 */
import React from 'react'
import { Input, Typography } from 'antd'

const { TextArea } = Input
const { Text } = Typography

interface TextEditorProps {
  title: string
  value: string
  onChange?: (value: string) => void
  placeholder?: string
  readOnly?: boolean
  showCharCount?: boolean
  style?: React.CSSProperties
}

export default function TextEditor({
  title,
  value,
  onChange,
  placeholder,
  readOnly = false,
  showCharCount = true,
  style,
}: TextEditorProps) {
  const charCount = value.length

  // 处理只读模式：允许选择和复制，但阻止修改
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (!readOnly) return

    // 允许的快捷键：Ctrl+C (复制), Ctrl+A (全选), 方向键, Home, End, PageUp, PageDown
    const allowedKeys = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Home', 'End', 'PageUp', 'PageDown']
    const isCtrlC = (e.ctrlKey || e.metaKey) && e.key === 'c'
    const isCtrlA = (e.ctrlKey || e.metaKey) && e.key === 'a'

    if (isCtrlC || isCtrlA || allowedKeys.includes(e.key)) {
      return // 允许这些操作
    }

    // 阻止其他所有键盘输入
    e.preventDefault()
  }

  // 阻止粘贴
  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    if (readOnly) {
      e.preventDefault()
    }
  }

  // 阻止剪切
  const handleCut = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    if (readOnly) {
      e.preventDefault()
    }
  }

  return (
    <div className="text-editor" style={style}>
      <div className="text-editor-header">
        <Text strong>{title}</Text>
        {showCharCount && (
          <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
            {charCount} 字
          </Text>
        )}
      </div>
      <TextArea
        value={value}
        onChange={onChange ? (e) => onChange(e.target.value) : undefined}
        placeholder={placeholder}
        onKeyDown={handleKeyDown}
        onPaste={handlePaste}
        onCut={handleCut}
        autoSize={{ minRows: 12, maxRows: 24 }}
        style={{
          fontFamily: 'var(--font-family-text, "Noto Serif SC", serif)',
          fontSize: 16,
          lineHeight: 1.8,
          // 只读时显示不同的背景色提示
          backgroundColor: readOnly ? '#fafafa' : undefined,
        }}
      />
    </div>
  )
}
