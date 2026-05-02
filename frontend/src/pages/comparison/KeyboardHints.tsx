/**
 * 快捷键提示组件
 */

interface KeyboardHintsProps {
  visible: boolean
}

export default function KeyboardHints({ visible }: KeyboardHintsProps) {
  if (!visible) return null

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 20,
        left: '50%',
        transform: 'translateX(-50%)',
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: '12px 24px',
        borderRadius: 8,
        fontSize: 13,
        zIndex: 1000,
        display: 'flex',
        gap: 16,
      }}
    >
      <span>
        <kbd
          style={{
            background: 'rgba(255,255,255,0.2)',
            padding: '4px 8px',
            borderRadius: 4,
            margin: '0 4px',
          }}
        >
          ←
        </kbd>
        上一个
      </span>
      <span>
        <kbd
          style={{
            background: 'rgba(255,255,255,0.2)',
            padding: '4px 8px',
            borderRadius: 4,
            margin: '0 4px',
          }}
        >
          →
        </kbd>
        下一个
      </span>
      <span>
        <kbd
          style={{
            background: 'rgba(255,255,255,0.2)',
            padding: '4px 8px',
            borderRadius: 4,
            margin: '0 4px',
          }}
        >
          Enter
        </kbd>
        标记已审核
      </span>
    </div>
  )
}
