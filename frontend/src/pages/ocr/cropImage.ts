/**
 * 把图片按「相对比例选区」裁剪成一个新的 PNG File（客户端 canvas 实现）。
 * 用于框选区域 OCR：只把选区送给后端识别，绕开引擎"只认主文本块"的版面裁切。
 */
import type { Region } from './RegionSelectImage'

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('图片加载失败'))
    img.src = url
  })
}

export async function cropToFile(file: File, region: Region, name: string): Promise<File> {
  const url = URL.createObjectURL(file)
  try {
    const img = await loadImage(url)
    const sx = Math.round(region.fx * img.naturalWidth)
    const sy = Math.round(region.fy * img.naturalHeight)
    const sw = Math.max(1, Math.round(region.fw * img.naturalWidth))
    const sh = Math.max(1, Math.round(region.fh * img.naturalHeight))

    const canvas = document.createElement('canvas')
    canvas.width = sw
    canvas.height = sh
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('无法获取 canvas 2D 上下文')
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh)

    const blob: Blob = await new Promise((resolve, reject) =>
      canvas.toBlob(
        (b) => (b ? resolve(b) : reject(new Error('图片裁剪失败'))),
        'image/png'
      )
    )
    return new File([blob], `${name}-region.png`, { type: 'image/png' })
  } finally {
    URL.revokeObjectURL(url)
  }
}
