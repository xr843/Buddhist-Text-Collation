/**
 * 用户菜单组件
 * 显示在顶部导航栏，包含用户信息和操作菜单
 */
import React from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Dropdown, Avatar, Button, Space, message, Typography } from 'antd'
import type { MenuProps } from 'antd'
import {
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  CrownOutlined,
  LoginOutlined,
  UserAddOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../../store/authStore'

const { Text } = Typography

const UserMenu: React.FC = () => {
  const navigate = useNavigate()
  const { user, isAuthenticated, logout, isAdmin } = useAuthStore()

  const handleLogout = async () => {
    try {
      await logout()
      message.success('已退出登录')
      navigate('/login')
    } catch (error) {
      message.error('退出登录失败')
    }
  }

  // 已登录用户的菜单项
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'info',
      label: (
        <div style={{ padding: '4px 0' }}>
          <div style={{ fontWeight: 500 }}>{user?.full_name || user?.username}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {user?.email}
          </Text>
        </div>
      ),
      disabled: true,
    },
    { type: 'divider' },
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => navigate('/settings'),
    },
    ...(isAdmin() ? [{
      key: 'admin',
      icon: <CrownOutlined />,
      label: '管理后台',
      onClick: () => navigate('/admin/users'),
    }] : []),
    { type: 'divider' },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
      onClick: handleLogout,
    },
  ]

  // 已登录状态
  if (isAuthenticated && user) {
    return (
      <Dropdown
        menu={{ items: userMenuItems }}
        placement="bottomRight"
        trigger={['click']}
      >
        <Space style={{ cursor: 'pointer', padding: '0 8px' }}>
          <Avatar
            size="small"
            src={user.avatar_url}
            icon={!user.avatar_url && <UserOutlined />}
            style={{ backgroundColor: '#1890ff' }}
          />
          <span style={{ color: 'inherit', maxWidth: 100, overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {user.full_name || user.username}
          </span>
        </Space>
      </Dropdown>
    )
  }

  // 未登录状态
  return (
    <Space>
      <Link to="/login">
        <Button type="text" icon={<LoginOutlined />}>
          登录
        </Button>
      </Link>
      <Link to="/register">
        <Button type="primary" icon={<UserAddOutlined />}>
          注册
        </Button>
      </Link>
    </Space>
  )
}

export default UserMenu
