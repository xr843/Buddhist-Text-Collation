/**
 * 流式处理服务
 * 支持 Server-Sent Events (SSE)
 */

export interface StreamProgress {
  progress: number
  chunk_index: number
  processed_chars: number
}

export interface StreamChunk {
  chunk_index: number
  result: string
  duration: number
  model_used: string
}

export interface StreamComplete {
  total_chunks: number
  final_text: string
  total_duration: number
  average_speed: number
}

export interface StreamError {
  error: string
  message: string
}

export interface StreamCallbacks {
  onStart?: (data: any) => void
  onProgress?: (data: StreamProgress) => void
  onChunk?: (data: StreamChunk) => void
  onComplete?: (data: StreamComplete) => void
  onError?: (error: StreamError) => void
}

/**
 * 流式标点处理
 *
 * @param text 待标点文本
 * @param chunkSize 分块大小
 * @param callbacks 事件回调
 * @returns 取消函数
 */
export async function punctuateWithStream(
  text: string,
  chunkSize: number = 500,
  callbacks: StreamCallbacks
): Promise<() => void> {
  const API_URL = import.meta.env.VITE_API_URL || ''
  const url = `${API_URL}/api/v1/streaming/punctuate-stream`

  // 使用 fetch 发起 POST 请求（SSE 不支持 EventSource）
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
      chunk_size: chunkSize,
    }),
  })

  if (!response.ok) {
    const error = await response.json()
    callbacks.onError?.({
      error: 'request_failed',
      message: error.detail || '请求失败',
    })
    return () => {}
  }

  // 读取流式响应
  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  let buffer = ''
  let cancelled = false

  // 异步读取流
  ;(async () => {
    try {
      while (!cancelled) {
        const { value, done } = await reader!.read()

        if (done) {
          break
        }

        // 解码数据
        buffer += decoder.decode(value, { stream: true })

        // 处理完整的事件
        const events = buffer.split('\n\n')
        buffer = events.pop() || ''

        for (const eventText of events) {
          if (!eventText.trim()) continue

          // 解析事件
          const lines = eventText.split('\n')
          let eventType = 'message'
          let eventData = ''

          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventType = line.slice(6).trim()
            } else if (line.startsWith('data:')) {
              eventData = line.slice(5).trim()
            }
          }

          // 解析 JSON 数据
          try {
            const data = JSON.parse(eventData)

            // 分发事件
            switch (eventType) {
              case 'start':
                callbacks.onStart?.(data)
                break
              case 'progress':
                callbacks.onProgress?.(data)
                break
              case 'chunk':
                callbacks.onChunk?.(data)
                break
              case 'complete':
                callbacks.onComplete?.(data)
                break
              case 'error':
                callbacks.onError?.(data)
                break
            }
          } catch (error) {
            console.error('解析事件数据失败:', error)
          }
        }
      }
    } catch (error) {
      if (!cancelled) {
        callbacks.onError?.({
          error: 'stream_error',
          message: error instanceof Error ? error.message : '流式处理错误',
        })
      }
    }
  })()

  // 返回取消函数
  return () => {
    cancelled = true
    reader?.cancel()
  }
}

/**
 * 使用示例：
 *
 * ```typescript
 * import { punctuateWithStream } from '@/services/streaming'
 *
 * const cancel = await punctuateWithStream(
 *   '诸一切种诸冥灭拔众生出生死泥',
 *   500,
 *   {
 *     onStart: (data) => {
 *       console.log('开始处理:', data)
 *     },
 *     onProgress: (data) => {
 *       console.log(`进度: ${data.progress}%`)
 *       setProgress(data.progress)
 *     },
 *     onChunk: (data) => {
 *       console.log(`分块 ${data.chunk_index}:`, data.result)
 *       appendResult(data.result)
 *     },
 *     onComplete: (data) => {
 *       console.log('完成:', data.final_text)
 *       setFinalText(data.final_text)
 *     },
 *     onError: (error) => {
 *       console.error('错误:', error.message)
 *       showError(error.message)
 *     }
 *   }
 * )
 *
 * // 取消处理
 * // cancel()
 * ```
 */
