/**
 * 版本对勘 API 服务
 */

import { message } from 'antd'
import { apiFetchJson } from '../../utils/apiFetch'
import type {
  MultiCollationResponse,
  ProjectSummary,
  FullProject,
  CollationDecision,
} from './types'
import { API_BASE } from './constants'

/**
 * 加载项目列表
 */
export async function fetchProjectList(limit: number = 50): Promise<{
  items: ProjectSummary[]
  total: number
}> {
  const data = await apiFetchJson<{ items?: any[]; total?: number }>(
    `/api/v1/multi-collation/projects?limit=${limit}`,
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
export async function fetchProject(projectId: string): Promise<FullProject> {
  const data = await apiFetchJson<{ project: FullProject }>(
    `/api/v1/multi-collation/projects/${projectId}`,
    { retries: 2 }
  )
  return data.project
}

/**
 * 删除项目
 */
export async function deleteProject(projectId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/multi-collation/projects/${projectId}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || '删除失败')
  }
}

/**
 * 更新项目标题
 */
export async function updateProjectTitle(projectId: string, newTitle: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/multi-collation/projects/${projectId}`, {
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
export async function fetchDecisions(projectId: string): Promise<Record<number, CollationDecision>> {
  const response = await fetch(
    `${API_BASE}/api/v1/multi-collation/projects/${projectId}/decisions`
  )

  if (!response.ok) {
    throw new Error('加载判取结果失败')
  }

  const data = await response.json()
  const loadedDecisions: Record<number, CollationDecision> = {}

  if (data.decisions) {
    for (const [pos, decision] of Object.entries(data.decisions)) {
      loadedDecisions[parseInt(pos)] = decision as CollationDecision
    }
  }

  return loadedDecisions
}

/**
 * 保存判取结果
 */
export async function saveDecisions(
  projectId: string,
  decisions: Record<number, CollationDecision>
): Promise<{ total_decisions: number }> {
  const response = await fetch(
    `${API_BASE}/api/v1/multi-collation/projects/${projectId}/decisions`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decisions }),
    }
  )

  if (!response.ok) {
    throw new Error('保存失败')
  }

  return response.json()
}

/**
 * 删除单个判取
 */
export async function deleteDecision(projectId: string, position: number): Promise<void> {
  const response = await fetch(
    `${API_BASE}/api/v1/multi-collation/projects/${projectId}/decisions/${position}`,
    { method: 'DELETE' }
  )

  if (!response.ok) {
    throw new Error('删除失败')
  }
}

/**
 * 生成定本
 */
export async function generateDefinitiveText(
  projectId: string,
  includeUncertain: boolean = false
): Promise<{
  definitive_text: string
  collation_notes: string
  statistics: {
    total_decisions: number
    certain_decisions: number
    uncertain_decisions: number
    remaining_variants: number
  }
}> {
  const response = await fetch(
    `${API_BASE}/api/v1/multi-collation/projects/${projectId}/generate-definitive-text`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ include_uncertain: includeUncertain }),
    }
  )

  if (!response.ok) {
    throw new Error('生成定本失败')
  }

  return response.json()
}

/**
 * 追加校本
 */
export async function addCollations(
  projectId: string,
  files: File[]
): Promise<MultiCollationResponse> {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('collation_files', file)
  })

  const response = await fetch(
    `${API_BASE}/api/v1/multi-collation/projects/${projectId}/add-collations`,
    { method: 'POST', body: formData }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '追加失败')
  }

  return response.json()
}

/**
 * 移除校本
 */
export async function removeCollations(
  projectId: string,
  indices: number[]
): Promise<MultiCollationResponse & {
  removed_collations: string[]
  removed_decisions: number
}> {
  const response = await fetch(
    `${API_BASE}/api/v1/multi-collation/projects/${projectId}/remove-collations`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ indices }),
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '移除失败')
  }

  return response.json()
}

/**
 * 执行多版本校勘
 */
export async function performCollation(
  baseFile: File,
  collationFiles: File[],
  sutraName?: string
): Promise<MultiCollationResponse> {
  const formData = new FormData()
  formData.append('base_file', baseFile)
  collationFiles.forEach((file) => {
    formData.append('collation_files', file)
  })
  if (sutraName) {
    formData.append('sutra_name', sutraName)
  }

  const response = await fetch(`${API_BASE}/api/v1/multi-collation/collate`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || '校勘失败')
  }

  return response.json()
}
