/**
 * API服务层
 */
import axios from 'axios'
import type {
  ComparisonRequest,
  ComparisonResponse,
  PunctuationComparisonResponse,
} from '../types'

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const message = error.response.data?.detail || error.message
      console.error('API错误:', message)
      throw new Error(message)
    } else if (error.request) {
      console.error('网络错误:', error.message)
      throw new Error('网络连接失败，请检查后端服务是否启动')
    } else {
      console.error('请求错误:', error.message)
      throw error
    }
  }
)

/**
 * 文本对比API
 */
export const comparisonApi = {
  /**
   * 对比两个文本
   */
  async compare(data: ComparisonRequest): Promise<ComparisonResponse> {
    const response = await api.post<ComparisonResponse>('/api/v1/comparison/compare', data)
    return response.data
  },

  /**
   * 标点版本对比
   */
  async comparePunctuation(data: ComparisonRequest): Promise<PunctuationComparisonResponse> {
    const response = await api.post<PunctuationComparisonResponse>(
      '/api/v1/comparison/compare-punctuation',
      data,
      { timeout: 300000 }
    )
    return response.data
  },

  /**
   * 文件上传对比
   */
  async compareFiles(
    file1: File,
    file2: File,
    version1Name?: string,
    version2Name?: string,
    forceMode?: 'punctuation' | 'collation'
  ): Promise<any> {
    const formData = new FormData()
    formData.append('file1', file1)
    formData.append('file2', file2)
    if (version1Name) formData.append('version1_name', version1Name)
    if (version2Name) formData.append('version2_name', version2Name)
    if (forceMode) formData.append('force_mode', forceMode)

    const response = await api.post(
      '/api/v1/comparison/compare-files',
      formData,
      {
        timeout: 300000,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  /**
   * 健康检查
   */
  async health(): Promise<any> {
    const response = await api.get('/api/v1/comparison/health')
    return response.data
  },

  /**
   * 导出校勘记
   */
  async exportCollationNotes(data: {
    text1: string
    text2: string
    version1_name?: string
    version2_name?: string
    format?: 'txt' | 'tei-xml' | 'json' | 'csv'
    include_context?: boolean
    title?: string
  }): Promise<{
    success: boolean
    content: string
    format: string
    content_type: string
    filename: string
    note_count: number
    statistics: any
  }> {
    const response = await api.post(
      '/api/v1/comparison/export-collation-notes',
      {
        text1: data.text1,
        text2: data.text2,
        version1_name: data.version1_name || '底本',
        version2_name: data.version2_name || '校本',
        format: data.format || 'txt',
        include_context: data.include_context ?? true,
        title: data.title || '校勘记'
      },
      { timeout: 60000 }
    )
    return response.data
  },
}

export default api
