/**
 * 标点迁移 API 服务
 */
import { apiFetchJson } from '../../utils/apiFetch'
import type {
  TransferRequest,
  TransferResponse,
  RemovePunctuationRequest,
  RemovePunctuationResponse,
  ExampleResponse,
} from './types'

const API_BASE = '/api/v1/punctuation-transfer'

/**
 * 执行标点迁移
 */
export async function transferPunctuation(
  request: TransferRequest
): Promise<TransferResponse> {
  return apiFetchJson<TransferResponse>(`${API_BASE}/transfer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })
}

/**
 * 清除文本标点
 */
export async function removePunctuation(
  request: RemovePunctuationRequest
): Promise<RemovePunctuationResponse> {
  return apiFetchJson<RemovePunctuationResponse>(`${API_BASE}/remove-punctuation`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })
}

/**
 * 获取示例文本
 */
export async function getExample(): Promise<ExampleResponse> {
  return apiFetchJson<ExampleResponse>(`${API_BASE}/example`)
}
