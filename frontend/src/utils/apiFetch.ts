type JsonErrorPayload = {
  detail?: unknown
  message?: unknown
}

const normalizeBase = (base: string) => base.replace(/\/+$/, '')

const joinUrl = (base: string, path: string) => {
  if (!base) return path
  const normalized = normalizeBase(base)
  return path.startsWith('/') ? `${normalized}${path}` : `${normalized}/${path}`
}

const getCandidateApiBases = () => {
  const envBase = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').trim()
  const bases: string[] = []
  const seen = new Set<string>()

  const add = (b: string) => {
    const key = b.trim()
    if (seen.has(key)) return
    seen.add(key)
    bases.push(key)
  }

  if (envBase) add(envBase)
  // 允许使用 Vite 代理（相对路径）
  add('')

  // 开发环境兜底：即使代理/端口配置出错，也尽量能自动访问到后端默认端口
  if (import.meta.env.DEV && !envBase) {
    add('http://localhost:8000')
    add('http://127.0.0.1:8000')
    add('http://localhost:8001')
    add('http://127.0.0.1:8001')
  }

  return bases
}

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export async function apiFetchJson<T>(
  path: string,
  init?: RequestInit & { retries?: number; retryDelayMs?: number }
): Promise<T> {
  const retries = init?.retries ?? 2
  const retryDelayMs = init?.retryDelayMs ?? 250
  const { retries: _r, retryDelayMs: _d, ...requestInit } = init || {}

  const bases = getCandidateApiBases()
  let lastError: unknown = null

  for (const base of bases) {
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const url = joinUrl(base, path)
        const resp = await fetch(url, requestInit)
        if (!resp.ok) {
          let detail = ''
          try {
            const data = (await resp.json()) as JsonErrorPayload
            const raw = data?.detail ?? data?.message
            if (typeof raw === 'string') detail = raw
            else if (raw != null) detail = JSON.stringify(raw)
          } catch {
            // ignore
          }

          const statusText = resp.statusText || '请求失败'
          const msg = detail ? `${resp.status} ${detail}` : `${resp.status} ${statusText}`

          // 仅对“服务暂不可用/代理未就绪”等情况进行重试
          if (attempt < retries && [502, 503, 504].includes(resp.status)) {
            await delay(retryDelayMs * (attempt + 1))
            continue
          }
          throw new Error(msg)
        }
        return (await resp.json()) as T
      } catch (e) {
        lastError = e
        if (attempt < retries) {
          await delay(retryDelayMs * (attempt + 1))
          continue
        }
      }
    }
  }

  if (lastError instanceof Error) {
    throw lastError
  }
  throw new Error('网络连接失败，请检查后端服务是否启动')
}

