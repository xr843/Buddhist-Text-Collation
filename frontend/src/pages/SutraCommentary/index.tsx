/**
 * 经论-注疏关联页面
 *
 * 独立于版本对勘的模块，专门用于：
 * 1. 上传经论原文和注疏文本
 * 2. 自动提取注疏中的引文
 * 3. 建立引文与经论原文的双向关联
 */
import { useState, useCallback, useEffect } from 'react'
import {
  Card,
  Button,
  Typography,
  Space,
  message,
  Drawer,
  Modal,
  Input,
  Form,
  Empty,
  Spin,
} from 'antd'
import {
  PlusOutlined,
  FolderOpenOutlined,
  BookOutlined,
} from '@ant-design/icons'
import { apiFetchJson } from '../../utils/apiFetch'
import ProjectList from './ProjectList'
import ProjectEditor from './ProjectEditor'

const { Title, Text } = Typography

// 项目类型定义
export interface SutraCommentaryProject {
  id: string
  title: string
  description: string
  created_at: string
  updated_at: string
  status: string
  metadata: {
    sutra_title?: string
    commentary_count: number
    citation_count: number
  }
  data: {
    sutra?: {
      title: string
      content: string
      source: string
      char_count: number
    }
    commentaries: Array<{
      id: string
      title: string
      citations_count: number
      matched_count: number
      upload_time: string
    }>
    matches: Array<{
      citation_id: string
      sutra_positions: Array<{
        start: number
        end: number
        similarity: number
        matched_text: string
      }>
    }>
  }
}

export default function SutraCommentaryPage() {
  // 状态
  const [projects, setProjects] = useState<SutraCommentaryProject[]>([])
  const [currentProject, setCurrentProject] = useState<SutraCommentaryProject | null>(null)
  const [loading, setLoading] = useState(false)
  const [projectListOpen, setProjectListOpen] = useState(false)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [form] = Form.useForm()

  // 加载项目列表
  const loadProjects = useCallback(async () => {
    setLoading(true)
    try {
      const res = await apiFetchJson('/api/v1/sutra-commentary/projects') as { items: SutraCommentaryProject[] }
      setProjects(res.items || [])
    } catch (err: any) {
      message.error(`加载项目列表失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }, [])

  // 加载项目详情
  const loadProject = useCallback(async (projectId: string) => {
    setLoading(true)
    try {
      const project = await apiFetchJson(`/api/v1/sutra-commentary/projects/${projectId}`) as SutraCommentaryProject
      setCurrentProject(project)
      setProjectListOpen(false)
    } catch (err: any) {
      message.error(`加载项目失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }, [])

  // 创建新项目
  const handleCreateProject = async (values: { name: string; description?: string }) => {
    try {
      const res = await apiFetchJson('/api/v1/sutra-commentary/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      }) as { id: string }
      message.success('项目创建成功')
      setCreateModalOpen(false)
      form.resetFields()
      await loadProject(res.id)
      loadProjects()
    } catch (err: any) {
      message.error(`创建项目失败: ${err.message}`)
    }
  }

  // 删除项目
  const handleDeleteProject = async (projectId: string) => {
    try {
      await apiFetchJson(`/api/v1/sutra-commentary/projects/${projectId}`, {
        method: 'DELETE',
      })
      message.success('项目已删除')
      if (currentProject?.id === projectId) {
        setCurrentProject(null)
      }
      loadProjects()
    } catch (err: any) {
      message.error(`删除失败: ${err.message}`)
    }
  }

  // 初始化加载项目列表
  useEffect(() => {
    loadProjects()
  }, [loadProjects])

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 页面头部 */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <Space>
          <BookOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          <Title level={4} style={{ margin: 0 }}>
            经论-注疏关联
          </Title>
          {currentProject && (
            <Text type="secondary" style={{ marginLeft: 16 }}>
              当前项目: {currentProject.title}
            </Text>
          )}
        </Space>

        <Space>
          <Button icon={<FolderOpenOutlined />} onClick={() => setProjectListOpen(true)}>
            项目列表
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
            新建项目
          </Button>
        </Space>
      </div>

      {/* 主内容区 */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {loading && !currentProject ? (
          <Card style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Spin size="large" tip="加载中..." />
          </Card>
        ) : currentProject ? (
          <ProjectEditor
            project={currentProject}
            onProjectUpdate={loadProject}
          />
        ) : (
          <Card style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <span>
                  暂无打开的项目
                  <br />
                  <Text type="secondary">请从项目列表选择或创建新项目</Text>
                </span>
              }
            >
              <Space>
                <Button onClick={() => setProjectListOpen(true)}>打开项目</Button>
                <Button type="primary" onClick={() => setCreateModalOpen(true)}>
                  新建项目
                </Button>
              </Space>
            </Empty>
          </Card>
        )}
      </div>

      {/* 项目列表抽屉 */}
      <Drawer
        title="项目列表"
        placement="right"
        width={400}
        open={projectListOpen}
        onClose={() => setProjectListOpen(false)}
      >
        <ProjectList
          projects={projects}
          loading={loading}
          onSelect={loadProject}
          onDelete={handleDeleteProject}
          onRefresh={loadProjects}
        />
      </Drawer>

      {/* 创建项目弹窗 */}
      <Modal
        title="新建经论-注疏关联项目"
        open={createModalOpen}
        onCancel={() => {
          setCreateModalOpen(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        okText="创建"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" onFinish={handleCreateProject}>
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="如：顺正理论与述文记关联研究" />
          </Form.Item>
          <Form.Item name="description" label="项目描述">
            <Input.TextArea
              rows={3}
              placeholder="可选，描述本项目的研究内容"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
