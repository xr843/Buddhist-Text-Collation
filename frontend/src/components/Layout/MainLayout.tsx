import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, theme, Button, Tooltip, Space } from 'antd'
import {
  FileTextOutlined,
  DiffOutlined,
  AppstoreOutlined,
  SettingOutlined,
  BookOutlined,
  DatabaseOutlined,
  ExpandOutlined,
  CompressOutlined,
  ReadOutlined,
  SwapOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useSettingsStore } from '../../store/settingsStore'

const { Header, Content, Sider } = Layout

type MenuItem = Required<MenuProps>['items'][number]

function getItem(
  label: React.ReactNode,
  key: React.Key,
  icon?: React.ReactNode,
  children?: MenuItem[]
): MenuItem {
  return {
    key,
    icon,
    children,
    label,
  } as MenuItem
}

const menuItems: MenuItem[] = [
  getItem('工作台', '/workspace', <AppstoreOutlined />),
  getItem('CBETA导入', '/cbeta-import', <DatabaseOutlined />),
  getItem('版本对勘', '/multi-collation', <BookOutlined />),
  getItem('标点版本对比', '/punctuation-compare', <DiffOutlined />),
  getItem('标点迁移', '/punctuation-transfer', <SwapOutlined />),
  getItem('经论注疏对读', '/sutra-parallel-reader', <ReadOutlined />),
  getItem('设置', '/settings', <SettingOutlined />),
]

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const {
    token: { colorBgContainer, borderRadiusLG, colorPrimary },
  } = theme.useToken()

  // 专注模式状态
  const { settings, toggleZenMode } = useSettingsStore()
  const { zenMode } = settings.ui

  const handleMenuClick: MenuProps['onClick'] = (e) => {
    navigate(e.key)
  }

  // 专注模式下显示浮动工具条
  if (zenMode) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        {/* 浮动工具条 */}
        <div className="zen-mode-toolbar">
          <Tooltip title="退出专注模式">
            <Button
              type="text"
              icon={<CompressOutlined />}
              onClick={toggleZenMode}
            />
          </Tooltip>
        </div>

        {/* 全屏内容区 */}
        <Content
          style={{
            padding: 24,
            margin: 0,
            minHeight: '100vh',
            background: colorBgContainer,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    )
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: colorBgContainer,
          boxShadow: '0 1px 4px rgba(0, 0, 0, 0.08)',
          padding: '0 24px',
          zIndex: 1,
        }}
      >
        {/* Logo 和标题 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <FileTextOutlined style={{ fontSize: '24px', color: colorPrimary }} />
          <h1
            style={{
              margin: 0,
              fontSize: '20px',
              fontWeight: 600,
              fontFamily: 'var(--font-family-heading)',
            }}
          >
            佛典标点与校勘研究平台
          </h1>
        </div>

        {/* 右侧工具栏 */}
        <Space size="small">
          {/* 专注模式按钮 */}
          <Tooltip title="专注模式">
            <Button
              type="text"
              icon={<ExpandOutlined />}
              onClick={toggleZenMode}
            />
          </Tooltip>
        </Space>
      </Header>

      <Layout>
        <Sider
          width={160}
          collapsedWidth={60}
          collapsible
          collapsed={collapsed}
          onCollapse={(value) => setCollapsed(value)}
          style={{
            background: colorBgContainer,
            borderRight: '1px solid var(--color-border)',
          }}
        >
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={handleMenuClick}
            style={{
              height: '100%',
              borderRight: 0,
              paddingTop: '16px',
            }}
          />
        </Sider>

        <Layout style={{ padding: '24px' }}>
          <Content
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}
