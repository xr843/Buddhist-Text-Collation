/**
 * 把图片按「相对比例选区」裁剪成一个新的 JPEG File（客户端 canvas 实现）。
 * 用于框选区域 OCR：只把选区送给后端识别，绕开引擎"只认主文本块"的版面裁切。
 *
 * 用 JPEG 而非 PNG：实测上传体积是识别耗时的主因——同一张图 PNG(≈1.9MB) 要 33s，
 * JPEG q0.92(≈0.4MB) 只要 ~10s，且识别字数基本不变（427↔428，精度不损）。
 *
 * 关键：向选区外扩一圈「牺牲边距」（取真实图像周边像素，越界则截到图边）再裁。
 * 因为 gj.cool 引擎对收到的每张图都会做版面检测、裁掉一圈边距；若紧贴选区裁，
 * 框边缘的列（含被框线压住的半列）会被引擎当边距裁掉而漏识别。外扩后引擎裁掉的
 * 是这圈边距而非用户要的列。实测：外扩可把贴边/半截的列完整救回。
 * （试过用纯色边框补边——会干扰版面检测、反而丢列，不可取。）
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

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v))

export async function cropToFile(file: File, region: Region, name: string): Promise<File> {
  const url = URL.createObjectURL(file)
  try {
    const img = await loadImage(url)
    const W = img.naturalWidth
    const H = img.naturalHeight

    const sx = Math.round(region.fx * W)
    const sy = Math.round(region.fy * H)
    const sw = Math.max(1, Math.round(region.fw * W))
    const sh = Math.max(1, Math.round(region.fh * H))

    // 牺牲边距：按选区尺寸成比例（8%），下限 12px、上限 120px。
    // 关键是比例而非固定下限：窄选区（如单列）→ 极小边距，不会带进相邻列；
    // 宽选区（框边可能切穿外缘列）→ 大边距，把被切的边列补全。
    // 实测：窄单列 pad12 → 仅识别该列无邻列；宽框 pad120 → 完整救回被切的最左列。
    const padX = clamp(Math.round(sw * 0.08), 12, 120)
    const padY = clamp(Math.round(sh * 0.08), 12, 120)
    const x0 = clamp(sx - padX, 0, W)
    const y0 = clamp(sy - padY, 0, H)
    const x1 = clamp(sx + sw + padX, 0, W)
    const y1 = clamp(sy + sh + padY, 0, H)
    const cw = Math.max(1, x1 - x0)
    const ch = Math.max(1, y1 - y0)

    const canvas = document.createElement('canvas')
    canvas.width = cw
    canvas.height = ch
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('无法获取 canvas 2D 上下文')
    ctx.drawImage(img, x0, y0, cw, ch, 0, 0, cw, ch)

    const blob: Blob = await new Promise((resolve, reject) =>
      canvas.toBlob(
        (b) => (b ? resolve(b) : reject(new Error('图片裁剪失败'))),
        'image/jpeg',
        0.92
      )
    )
    return new File([blob], `${name}-region.jpg`, { type: 'image/jpeg' })
  } finally {
    URL.revokeObjectURL(url)
  }
}
