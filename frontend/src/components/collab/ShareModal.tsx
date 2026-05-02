/**
 * 项目共享设置弹窗
 */
import React, { useState, useEffect } from 'react'
import {
  Modal,
  Form,
  Input,
  Select,
  Button,
  Table,
  Space,
  Tag,
  message,
  Popconfirm,
  Avatar,
  Typography,
  Divider,
  Radio,
} from 'antd'
import {
  UserAddOutlined,
  DeleteOutlined,
  GlobalOutlined,
  LockOutlined,
  TeamOutlined,
  CrownOutlined,
  EditOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import api from '../../services/api'

const { Text } = Typography

interface Member {
  id: number
  user_id: number
  username: string
  full_name?: string
  avatar_url?: string
  role: string
  created_at?: string
}

interface ShareModalProps {
  visible: boolean
  onClose: () => void
  projectId: string
  projectTitle: string
  currentVisibility: string
  isOwner: boolean
  onVisibilityChange?: (visibility: string) => void
}

const roleOptions = [
  { value: 'viewer', label: '只读', icon: <EyeOutlined />, description: '可查看项目内容和导出' },
  { value: 'editor', label: '编辑', icon: <EditOutlined />, description: '可编辑项目数据和判取' },
  { value: 'admin', label: '管理员', icon: <CrownOutlined />, description: '可管理成员和项目设置' },
]

const visibilityOptions = [
  { value: 'private', label: '私有', icon: <LockOutlined />, description: '仅所有者和被共享成员可见' },
  { value: 'shared', label: '团队可见', icon: <TeamOutlined />, description: '所有登录用户可以只读访问' },
  { value: 'public', label: '公开', icon: <GlobalOutlined />, description: '无需登录即可查看' },
]

const ShareModal: React.FC<ShareModalProps> = ({
  visible,
  onClose,
  projectId,
  projectTitle,
  currentVisibility,
  isOwner,
  onVisibilityChange,
}) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [members, setMembers] = useState<Member[]>([])
  const [visibility, setVisibility] = useState(currentVisibility)
  const [addingMember, setAddingMember] = useState(false)

  // 获取成员列表
  const fetchMembers = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/api/v1/collab/projects/${projectId}/members`)
      if (response.data.success) {
        setMembers(response.data.members || [])
      }
    } catch (error: any) {
      message.error(error.message || '获取成员列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (visible) {
      fetchMembers()
      setVisibility(currentVisibility)
    }
  }, [visible, projectId, currentVisibility])

  // 添加成员
  const handleAddMember = async (values: { username: string; role: string }) => {
    setAddingMember(true)
    try {
      const response = await api.post(`/api/v1/collab/projects/${projectId}/share`, {
        username: values.username,
        role: values.role,
      })
      if (response.data.success) {
        message.success(response.data.message || '添加成功')
        form.resetFields()
        fetchMembers()
      }
    } catch (error: any) {
      message.error(error.message || '添加失败')
    } finally {
      setAddingMember(false)
    }
  }

  // 更新成员角色
  const handleUpdateRole = async (userId: number, newRole: string) => {
    try {
      const response = await api.put(`/api/v1/collab/projects/${projectId}/share/${userId}`, {
        role: newRole,
      })
      if (response.data.success) {
        message.success('角色已更新')
        fetchMembers()
      }
    } catch (error: any) {
      message.error(error.message || '更新失败')
    }
  }

  // 移除成员
  const handleRemoveMember = async (userId: number) => {
    try {
      const response = await api.delete(`/api/v1/collab/projects/${projectId}/share/${userId}`)
      if (response.data.success) {
        message.success('已移除成员')
        fetchMembers()
      }
    } catch (error: any) {
      message.error(error.message || '移除失败')
    }
  }

  // 更新可见性
  const handleVisibilityChange = async (newVisibility: string) => {
    try {
      const response = await api.put(
        `/api/v1/collab/projects/${projectId}/visibility`,
        null,
        { params: { visibility: newVisibility } }
      )
      if (response.data.success) {
        setVisibility(newVisibility)
        message.success('可见性已更新')
        onVisibilityChange?.(newVisibility)
      }
    } catch (error: any) {
      message.error(error.message || '更新失败')
    }
  }

  // 表格列
  const columns: ColumnsType<Member> = [
    {
      title: '成员',
      dataIndex: 'username',
      render: (_, record) => (
        <Space>
          <Avatar size="small" src={record.avatar_url}>
            {record.username?.[0]?.toUpperCase()}
          </Avatar>
          <div>
            <div>{record.full_name || record.username}</div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              @{record.username}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '角色',
      dataIndex: 'role',
      width: 140,
      render: (role, record) => {
        if (role === 'owner') {
          return <Tag color="gold" icon={<CrownOutlined />}>所有者</Tag>
        }

        if (!isOwner) {
          return (
            <Tag color={role === 'admin' ? 'blue' : role === 'editor' ? 'green' : 'default'}>
              {roleOptions.find((r) => r.value === role)?.label || role}
            </Tag>
          )
        }

        return (
          <Select
            size="small"
            value={role}
            style={{ width: 100 }}
            onChange={(value) => handleUpdateRole(record.user_id, value)}
          >
            {roleOptions.map((opt) => (
              <Select.Option key={opt.value} value={opt.value}>
                {opt.label}
              </Select.Option>
            ))}
          </Select>
        )
      },
    },
    {
      title: '操作',
      width: 80,
      render: (_, record) => {
        if (record.role === 'owner') return null
        if (!isOwner) return null

        return (
          <Popconfirm
            title="确定移除该成员？"
            onConfirm={() => handleRemoveMember(record.user_id)}
          >
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>
              移除
            </Button>
          </Popconfirm>
        )
      },
    },
  ]

  return (
    <Modal
      title={`共享设置 - ${projectTitle}`}
      open={visible}
      onCancel={onClose}
      footer={null}
      width={600}
    >
      {/* 可见性设置 */}
      {isOwner && (
        <>
          <div style={{ marginBottom: 16 }}>
            <Text strong>项目可见性</Text>
            <Radio.Group
              value={visibility}
              onChange={(e) => handleVisibilityChange(e.target.value)}
              style={{ display: 'block', marginTop: 8 }}
            >
              <Space direction="vertical">
                {visibilityOptions.map((opt) => (
                  <Radio key={opt.value} value={opt.value}>
                    <Space>
                      {opt.icon}
                      <span>{opt.label}</span>
                      <Text type="secondary">- {opt.description}</Text>
                    </Space>
                  </Radio>
                ))}
              </Space>
            </Radio.Group>
          </div>
          <Divider />
        </>
      )}

      {/* 添加成员 */}
      {isOwner && (
        <>
          <Form form={form} layout="inline" onFinish={handleAddMember} style={{ marginBottom: 16 }}>
            <Form.Item
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="输入用户名或邮箱" />
            </Form.Item>
            <Form.Item name="role" initialValue="viewer">
              <Select style={{ width: 100 }}>
                {roleOptions.map((opt) => (
                  <Select.Option key={opt.value} value={opt.value}>
                    {opt.label}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                icon={<UserAddOutlined />}
                loading={addingMember}
              >
                添加
              </Button>
            </Form.Item>
          </Form>
        </>
      )}

      {/* 成员列表 */}
      <div style={{ marginBottom: 8 }}>
        <Text strong>成员列表</Text>
      </div>
      <Table
        columns={columns}
        dataSource={members}
        rowKey="user_id"
        loading={loading}
        pagination={false}
        size="small"
      />
    </Modal>
  )
}

export default ShareModal
