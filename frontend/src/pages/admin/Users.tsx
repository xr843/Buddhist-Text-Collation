/**
 * 管理员 - 用户管理页面
 */
import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Typography,
  Space,
  Tag,
  Button,
  Input,
  message,
  Popconfirm,
  Avatar,
} from 'antd'
import {
  UserOutlined,
  SearchOutlined,
  ReloadOutlined,
  CrownOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useAuthStore } from '../../store/authStore'
import api from '../../services/api'

const { Title, Text } = Typography

interface UserItem {
  id: number
  username: string
  email: string
  full_name?: string
  role: string
  is_active: boolean
  institution?: string
  created_at: string
  last_login?: string
}

const AdminUsers: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [users, setUsers] = useState<UserItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [searchText, setSearchText] = useState('')
  const { user: currentUser } = useAuthStore()

  // 获取用户列表
  const fetchUsers = async () => {
    setLoading(true)
    try {
      const response = await api.get('/api/v1/admin/users', {
        params: {
          limit: pageSize,
          offset: (page - 1) * pageSize,
          search: searchText || undefined,
        },
      })
      if (response.data.success) {
        setUsers(response.data.items || [])
        setTotal(response.data.total || 0)
      }
    } catch (error: any) {
      message.error(error.message || '获取用户列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [page, pageSize])

  // 搜索
  const handleSearch = () => {
    setPage(1)
    fetchUsers()
  }

  // 格式化日期
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  // 表格列定义
  const columns: ColumnsType<UserItem> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
    },
    {
      title: '用户',
      dataIndex: 'username',
      render: (_, record) => (
        <Space>
          <Avatar
            size="small"
            icon={<UserOutlined />}
            style={{ backgroundColor: record.role === 'admin' ? '#faad14' : '#1890ff' }}
          />
          <div>
            <div style={{ fontWeight: 500 }}>{record.username}</div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.email}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '姓名',
      dataIndex: 'full_name',
      render: (text) => text || '-',
    },
    {
      title: '机构',
      dataIndex: 'institution',
      render: (text) => text || '-',
    },
    {
      title: '角色',
      dataIndex: 'role',
      width: 100,
      render: (role) => (
        <Tag color={role === 'admin' ? 'gold' : 'blue'} icon={role === 'admin' ? <CrownOutlined /> : null}>
          {role === 'admin' ? '管理员' : '普通用户'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 80,
      render: (active) => (
        <Tag color={active ? 'green' : 'default'}>
          {active ? '正常' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '注册时间',
      dataIndex: 'created_at',
      width: 160,
      render: formatDate,
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      width: 160,
      render: formatDate,
    },
    {
      title: '操作',
      width: 120,
      render: (_, record) => (
        <Space>
          {record.id !== currentUser?.id && (
            <>
              <Button type="link" size="small">
                编辑
              </Button>
              <Popconfirm
                title={record.is_active ? '确定禁用该用户？' : '确定启用该用户？'}
                onConfirm={() => message.info('功能开发中')}
              >
                <Button type="link" size="small" danger={record.is_active}>
                  {record.is_active ? '禁用' : '启用'}
                </Button>
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>
        <CrownOutlined /> 用户管理
      </Title>

      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
          <Space>
            <Input
              placeholder="搜索用户名或邮箱"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={handleSearch}
              style={{ width: 240 }}
            />
            <Button onClick={handleSearch}>搜索</Button>
          </Space>
          <Button icon={<ReloadOutlined />} onClick={fetchUsers}>
            刷新
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 位用户`,
            onChange: (p, ps) => {
              setPage(p)
              setPageSize(ps)
            },
          }}
          size="middle"
        />
      </Card>
    </div>
  )
}

export default AdminUsers
