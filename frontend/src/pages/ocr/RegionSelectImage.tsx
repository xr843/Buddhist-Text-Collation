/**
 * 图片框选组件：在图片上拖拽画矩形选区。
 *
 * 选区以「相对比例」(0~1) 表达，与渲染尺寸/分辨率无关，便于在裁剪时换算回原图像素。
 * 不框选（或框得过小视为点击）→ 选区清空（识别整图）。
 *
 * 性能：拖拽全程
 *  - 只在 mousedown 时取一次 getBoundingClientRect（拖拽中图片不动，避免每次 move 强制 reflow）；
 *  - mousemove 用 requestAnimationFrame 合并，每帧最多一次 setState（避免高频重渲染卡顿）；
 *  - 监听挂在 window 上，光标移出图片也能跟手。
 */
import { useRef, useState, useCallback, useEffect } from 'react'

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
  const rectRef = useRef<DOMRect | null>(null)
  const startRef = useRef<{ fx: number; fy: number } | null>(null)
  const draftRef = useRef<Region | null>(null)
  const pendingRef = useRef<{ fx: number; fy: number } | null>(null)
  const rafRef = useRef<number | null>(null)
  const [draft, setDraft] = useState<Region | null>(null)

  const fracFromEvent = (clientX: number, clientY: number) => {
    const r = rectRef.current
    if (!r || r.width === 0 || r.height === 0) return { fx: 0, fy: 0 }
    return {
      fx: Math.min(1, Math.max(0, (clientX - r.left) / r.width)),
      fy: Math.min(1, Math.max(0, (clientY - r.top) / r.height)),
    }
  }

  // 把 pending 坐标合并成一次 setDraft（每帧一次）
  const flush = useCallback(() => {
    rafRef.current = null
    const s = startRef.current
    const p = pendingRef.current
    if (!s || !p) return
    const d: Region = {
      fx: Math.min(s.fx, p.fx),
      fy: Math.min(s.fy, p.fy),
      fw: Math.abs(p.fx - s.fx),
      fh: Math.abs(p.fy - s.fy),
    }
    draftRef.current = d
    setDraft(d)
  }, [])

  const onWindowMove = useCallback(
    (e: MouseEvent) => {
      if (!startRef.current) return
      pendingRef.current = fracFromEvent(e.clientX, e.clientY)
      if (rafRef.current == null) {
        rafRef.current = requestAnimationFrame(flush)
      }
    },
    [flush]
  )

  const endDrag = useCallback(() => {
    if (!startRef.current) return
    startRef.current = null
    if (rafRef.current != null) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
    window.removeEventListener('mousemove', onWindowMove)
    window.removeEventListener('mouseup', endDrag)
    const d = draftRef.current
    draftRef.current = null
    setDraft(null)
    if (d && d.fw >= MIN_FRACTION && d.fh >= MIN_FRACTION) {
      onRegionChange(d)
    } else {
      onRegionChange(null)
    }
  }, [onWindowMove, onRegionChange])

  const onMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault()
      const el = wrapRef.current
      if (!el) return
      rectRef.current = el.getBoundingClientRect() // 每次拖拽缓存一次
      const p = fracFromEvent(e.clientX, e.clientY)
      startRef.current = p
      pendingRef.current = p
      draftRef.current = { fx: p.fx, fy: p.fy, fw: 0, fh: 0 }
      setDraft(draftRef.current)
      onRegionChange(null)
      window.addEventListener('mousemove', onWindowMove)
      window.addEventListener('mouseup', endDrag)
    },
    [onWindowMove, endDrag, onRegionChange]
  )

  // 卸载时清理（防止拖拽中组件被卸载导致监听泄漏）
  useEffect(
    () => () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current)
      window.removeEventListener('mousemove', onWindowMove)
      window.removeEventListener('mouseup', endDrag)
    },
    [onWindowMove, endDrag]
  )

  const box = draft ?? region

  return (
    <div
      ref={wrapRef}
      onMouseDown={onMouseDown}
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
