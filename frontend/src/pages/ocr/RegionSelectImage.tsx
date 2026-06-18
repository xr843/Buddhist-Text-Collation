/**
 * 图片框选组件：在图片上拖拽画矩形选区。
 *
 * 选区以「相对比例」(0~1) 表达，与渲染尺寸/分辨率无关，便于在裁剪时换算回原图像素。
 * 不框选（或框得过小视为点击）→ 选区清空（识别整图）。
 */
import { useRef, useState, useCallback } from 'react'

export interface Region {
  fx: number
  fy: number
  fw: number
  fh: number
}

interface Props {
  src: string
  region: Region | null
  onRegionChange: (r: Region | null) => void
  maxHeight?: number
}

// 小于该比例的框视为误触（点击），不当作选区
const MIN_FRACTION = 0.02

export default function RegionSelectImage({
  src,
  region,
  onRegionChange,
  maxHeight = 420,
}: Props) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const startRef = useRef<{ fx: number; fy: number } | null>(null)
  const draftRef = useRef<Region | null>(null)
  const [draft, setDraft] = useState<Region | null>(null)

  const setDraftBoth = (r: Region | null) => {
    draftRef.current = r
    setDraft(r)
  }

  const toFrac = useCallback((clientX: number, clientY: number) => {
    const el = wrapRef.current
    if (!el) return { fx: 0, fy: 0 }
    const r = el.getBoundingClientRect()
    return {
      fx: Math.min(1, Math.max(0, (clientX - r.left) / r.width)),
      fy: Math.min(1, Math.max(0, (clientY - r.top) / r.height)),
    }
  }, [])

  const onMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault()
      const p = toFrac(e.clientX, e.clientY)
      startRef.current = p
      setDraftBoth({ fx: p.fx, fy: p.fy, fw: 0, fh: 0 })
      onRegionChange(null)
    },
    [toFrac, onRegionChange]
  )

  const onMouseMove = useCallback(
    (e: React.MouseEvent) => {
      const s = startRef.current
      if (!s) return
      const p = toFrac(e.clientX, e.clientY)
      setDraftBoth({
        fx: Math.min(s.fx, p.fx),
        fy: Math.min(s.fy, p.fy),
        fw: Math.abs(p.fx - s.fx),
        fh: Math.abs(p.fy - s.fy),
      })
    },
    [toFrac]
  )

  const finish = useCallback(() => {
    if (!startRef.current) return
    startRef.current = null
    const d = draftRef.current
    setDraftBoth(null)
    if (d && d.fw >= MIN_FRACTION && d.fh >= MIN_FRACTION) {
      onRegionChange(d)
    } else {
      onRegionChange(null)
    }
  }, [onRegionChange])

  const box = draft ?? region

  return (
    <div
      ref={wrapRef}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={finish}
      onMouseLeave={finish}
      style={{
        position: 'relative',
        display: 'inline-block',
        maxWidth: '100%',
        cursor: 'crosshair',
        userSelect: 'none',
        lineHeight: 0,
      }}
    >
      <img
        src={src}
        alt="preview"
        draggable={false}
        style={{ maxWidth: '100%', maxHeight, objectFit: 'contain', display: 'block' }}
      />
      {box && box.fw > 0 && box.fh > 0 && (
        <div
          style={{
            position: 'absolute',
            left: `${box.fx * 100}%`,
            top: `${box.fy * 100}%`,
            width: `${box.fw * 100}%`,
            height: `${box.fh * 100}%`,
            border: '2px solid #1677ff',
            background: 'rgba(22,119,255,0.15)',
            pointerEvents: 'none',
          }}
        />
      )}
    </div>
  )
}
