import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, theme, Button, Tooltip, Space, Dropdown } from 'antd'
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
  GlobalOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useTranslation } from 'react-i18next'
import { useSettingsStore } from '../../store/settingsStore'
import { supportedLanguages } from '../../i18n'
import UserMenu from '../auth/UserMenu'

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

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { t, i18n } = useTranslation()
  const [collapsed, setCollapsed] = useState(false)
  const {
    token: { colorBgContainer, borderRadiusLG, colorPrimary },
  } = theme.useToken()

  // 专注模式状态
  const { settings, toggleZenMode } = useSettingsStore()
  const { zenMode } = settings.ui

  const menuItems: MenuItem[] = [
    getItem(t('menu.workspace'), '/workspace', <AppstoreOutlined />),
    getItem(t('menu.cbetaImport'), '/cbeta-import', <DatabaseOutlined />),
    getItem(t('menu.multiCollation'), '/multi-collation', <BookOutlined />),
    getItem(t('menu.punctuationCompare'), '/punctuation-compare', <DiffOutlined />),
    getItem(t('menu.punctuationTransfer'), '/punctuation-transfer', <SwapOutlined />),
    getItem(t('menu.sutraParallelReader'), '/sutra-parallel-reader', <ReadOutlined />),
    getItem(t('menu.settings'), '/settings', <SettingOutlined />),
  ]

  const handleMenuClick: MenuProps['onClick'] = (e) => {
    navigate(e.key)
  }

  const languageMenuItems: MenuProps['items'] = supportedLanguages.map((lng) => ({
    key: lng.code,
    label: lng.label,
    onClick: () => i18n.changeLanguage(lng.code),
  }))

  // 专注模式下显示浮动工具条
  if (zenMode) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        {/* 浮动工具条 */}
        <div className="zen-mode-toolbar">
          <Tooltip title={t('actions.exitZenMode')}>
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
            {t('app.title')}
          </h1>
        </div>

        {/* 右侧工具栏 */}
        <Space size="small">
          {/* 语言切换 */}
          <Dropdown menu={{ items: languageMenuItems, selectable: true, selectedKeys: [i18n.language] }} placement="bottomRight">
            <Tooltip title={t('actions.switchLanguage')}>
              <Button type="text" icon={<GlobalOutlined />} />
            </Tooltip>
          </Dropdown>

          {/* 专注模式按钮 */}
          <Tooltip title={t('actions.zenMode')}>
            <Button
              type="text"
              icon={<ExpandOutlined />}
              onClick={toggleZenMode}
            />
          </Tooltip>

          <UserMenu />
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
