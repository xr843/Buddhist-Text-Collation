/**
 * 标点对比模块 API 服务
 */

import { apiFetchJson } from '../../utils/apiFetch'
import { API_BASE } from './constants'
import type {
  ProjectSummary,
  ProjectListResponse,
  ProjectDetailResponse,
  PunctuationDecision,
  PunctuationDefinitiveData,
} from './types'

/**
 * 加载项目列表
 */
export async function fetchProjectList(): Promise<{ items: ProjectSummary[]; total: number }> {
  const data = await apiFetchJson<ProjectListResponse>(
    '/api/v1/comparison/punctuation/projects?limit=50',
    { retries: 2 }
  )
  return {
    items: data.items || [],
    total: data.total || 0,
  }
}

/**
 * 加载项目详情
 */
export async function fetchProject(projectId: string): Promise<ProjectDetailResponse['project']> {
  const data = await apiFetchJson<ProjectDetailResponse>(
    `/api/v1/comparison/punctuation/projects/${projectId}`,
    { retries: 2 }
  )
  return data.project
}

/**
 * 删除项目
 */
export async function deleteProject(projectId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/comparison/punctuation/projects/${projectId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error('删除失败')
  }
}

/**
 * 更新项目标题
 */
export async function updateProjectTitle(projectId: string, newTitle: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/comparison/punctuation/projects/${projectId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: newTitle.trim() }),
  })
  if (!response.ok) {
    throw new Error('更新失败')
  }
}

/**
 * 加载判取结果
 */
export async function fetchDecisions(
  projectId: string
): Promise<Record<number, PunctuationDecision>> {
  try {
    const response = await fetch(
      `${API_BASE}/api/v1/comparison/punctuation/projects/${projectId}/decisions`
    )
    if (response.ok) {
      const data = await response.json()
      if (data.decisions && Object.keys(data.decisions).length > 0) {
        const loadedDecisions: Record<number, PunctuationDecision> = {}
        Object.entries(data.decisions).forEach(([diffId, decision]: [string, any]) => {
          loadedDecisions[parseInt(diffId)] = decision as PunctuationDecision
        })
        return loadedDecisions
      }
    }
    return {}
  } catch {
    return {}
  }
}

/**
 * 保存判取结果
 */
export async function saveDecisions(
  projectId: string,
  decisions: Record<number, PunctuationDecision>
): Promise<void> {
  const decisionsData: Record<string, any> = {}
  Object.entries(decisions).forEach(([diffId, decision]) => {
    decisionsData[diffId] = { ...decision }
  })

  const response = await fetch(
    `${API_BASE}/api/v1/comparison/punctuation/projects/${projectId}/decisions`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decisions: decisionsData }),
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '保存失败')
  }
}

/**
 * 生成定本
 */
export async function generateDefinitive(projectId: string): Promise<PunctuationDefinitiveData> {
  const response = await fetch(
    `${API_BASE}/api/v1/comparison/punctuation/projects/${projectId}/generate-definitive`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '生成失败')
  }

  return response.json()
}

/**
 * 文件上传对比
 */
export async function compareFiles(
  file1: File,
  file2: File,
  version1Name: string,
  version2Name: string
): Promise<any> {
  const formData = new FormData()
  formData.append('file1', file1)
  formData.append('file2', file2)
  formData.append('version1_name', version1Name)
  formData.append('version2_name', version2Name)
  formData.append('force_mode', 'punctuation')
  formData.append('auto_save', 'true')

  const res = await fetch(`${API_BASE}/api/v1/comparison/compare-files`, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail || '对比失败')
  }

  return res.json()
}
