/**
 * Studio工具面板 - Workspace右栏
 */
import { Card, Typography, Button, List, Space, Tag, Divider } from 'antd'
import {
  FileTextOutlined,
  DiffOutlined,
  SoundOutlined,
  ApartmentOutlined,
  BookOutlined,
  RightOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useWorkspaceStore } from '../../store'
import type { StudioTool } from '../../types/studio'

const { Text } = Typography

// Studio工具定义
const studioTools: StudioTool[] = [
  {
    id: 'punctuation',
    name: '智能标点',
    description: '为选中文档添加标点',
    icon: 'FileTextOutlined',
    category: 'core',
    enabled: true,
  },
  {
    id: 'comparison',
    name: '版本对比',
    description: '对比多个版本的差异',
    icon: 'DiffOutlined',
    category: 'core',
    enabled: true,
  },
  {
    id: 'audio',
    name: '音频概览',
    description: '生成文档语音朗读',
    icon: 'SoundOutlined',
    category: 'general',
    enabled: false,
  },
  {
    id: 'mindmap',
    name: '思维导图',
    description: '提取核心概念结构',
    icon: 'ApartmentOutlined',
    category: 'general',
    enabled: false,
  },
  {
    id: 'study-guide',
    name: '学习指南',
    description: '生成学习大纲',
    icon: 'BookOutlined',
    category: 'general',
    enabled: false,
  },
]

// 图标映射
const iconMap: Record<string, React.ReactNode> = {
  FileTextOutlined: <FileTextOutlined />,
  DiffOutlined: <DiffOutlined />,
  SoundOutlined: <SoundOutlined />,
  ApartmentOutlined: <ApartmentOutlined />,
  BookOutlined: <BookOutlined />,
}

export default function StudioPanel() {
  const navigate = useNavigate()
  const { getRecentOutputs } = useWorkspaceStore()

  const recentOutputs = getRecentOutputs(3)

  const handleToolClick = (tool: StudioTool) => {
    if (!tool.enabled) return

    // 跳转到对应的专业页面
    if (tool.id === 'punctuation') {
      navigate('/punctuation')
    } else if (tool.id === 'comparison') {
      navigate('/comparison')
    }
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: 16, overflow: 'auto' }}>
      {/* 标题 */}
      <div style={{ marginBottom: 16 }}>
        <Text strong style={{ fontSize: 16 }}>
          🎨 Studio
        </Text>
      </div>

      {/* 工具列表 */}
      <div style={{ marginBottom: 24 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          🛠️ 创建工具
        </Text>
        <div style={{ marginTop: 12 }}>
          {studioTools.map((tool) => (
            <Card
              key={tool.id}
              size="small"
              hoverable={tool.enabled}
              style={{
                marginBottom: 8,
                cursor: tool.enabled ? 'pointer' : 'not-allowed',
                opacity: tool.enabled ? 1 : 0.5,
              }}
              onClick={() => handleToolClick(tool)}
            >
              <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                <Space>
                  <div style={{ fontSize: 20 }}>{iconMap[tool.icon]}</div>
                  <div>
                    <div>
                      <Text strong style={{ fontSize: 13 }}>
                        {tool.name}
                      </Text>
                      {tool.category === 'core' && (
                        <Tag color="blue" style={{ marginLeft: 4, fontSize: 10 }}>
                          核心
                        </Tag>
                      )}
                    </div>
                    <div>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {tool.description}
                      </Text>
                    </div>
                  </div>
                </Space>
                {tool.enabled && <RightOutlined style={{ fontSize: 12, color: '#999' }} />}
              </Space>
            </Card>
          ))}
        </div>
      </div>

      <Divider style={{ margin: '16px 0' }} />

      {/* 最近输出 */}
      <div>
        <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 12 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            📌 最近输出
          </Text>
          {recentOutputs.length > 0 && (
            <Button type="link" size="small" style={{ padding: 0, height: 'auto' }}>
              查看全部
            </Button>
          )}
        </Space>

        {recentOutputs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 24, color: '#999' }}>
            <div style={{ fontSize: 36, marginBottom: 8 }}>📋</div>
            <div style={{ fontSize: 12 }}>暂无输出</div>
            <div style={{ fontSize: 11 }}>使用工具后结果会显示在这里</div>
          </div>
        ) : (
          <List
            dataSource={recentOutputs}
            renderItem={(output) => (
              <Card size="small" style={{ marginBottom: 8 }}>
                <div>
                  <Text strong style={{ fontSize: 12 }}>
                    {output.name}
                  </Text>
                </div>
                <div style={{ marginTop: 4 }}>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {new Date(output.createdAt).toLocaleString()}
                  </Text>
                </div>
                <div style={{ marginTop: 8 }}>
                  <Space size="small">
                    <Button size="small" type="link" style={{ padding: 0, height: 'auto' }}>
                      预览
                    </Button>
                    <Button size="small" type="link" style={{ padding: 0, height: 'auto' }}>
                      下载
                    </Button>
                    <Button size="small" type="link" style={{ padding: 0, height: 'auto' }}>
                      添加
                    </Button>
                  </Space>
                </div>
              </Card>
            )}
          />
        )}
      </div>

      {/* 输出统计 */}
      {recentOutputs.length > 0 && (
        <div style={{ marginTop: 'auto', paddingTop: 16 }}>
          <Divider style={{ margin: '0 0 12px 0' }} />
          <Text type="secondary" style={{ fontSize: 11 }}>
            📊 本周生成: {recentOutputs.length} 个
          </Text>
        </div>
      )}
    </div>
  )
}
