/**
 * 工作台 Dashboard - 项目概览与快速入口
 */
import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Row,
  Col,
  Typography,
  List,
  Tag,
  Button,
  Space,
  Spin,
  Empty,
  message,
  Badge,
} from 'antd'
import {
  DiffOutlined,
  BookOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  RightOutlined,
  PlusOutlined,
  DatabaseOutlined,
} from '@ant-design/icons'
import { apiFetchJson } from '../utils/apiFetch'

const { Title, Text, Paragraph } = Typography

// 项目摘要类型
interface ProjectSummary {
  id: string
  title: string
  status: string
  created_at: string
  updated_at: string
  metadata: {
    version1_name?: string
    version2_name?: string
    total_differences?: number
  }
}

// 统计数据类型
interface DashboardStats {
  punctuationProjects: number
  collationProjects: number
  totalDifferences: number
}

export default function Workspace() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<DashboardStats>({
    punctuationProjects: 0,
    collationProjects: 0,
    totalDifferences: 0,
  })
  const [recentPunctuationProjects, setRecentPunctuationProjects] = useState<ProjectSummary[]>([])
  const [recentCollationProjects, setRecentCollationProjects] = useState<any[]>([])

  // 加载仪表板数据
  const loadDashboardData = useCallback(async () => {
    setLoading(true)
    try {
      // 并行加载数据
      const [punctuationData, collationData] = await Promise.allSettled([
        apiFetchJson<{ items: ProjectSummary[]; total: number }>(
          '/api/v1/comparison/punctuation/projects?limit=5'
        ),
        apiFetchJson<{ items: any[]; total: number }>(
          '/api/v1/multi-collation/projects?limit=5'
        ),
      ])

      // 处理标点对比项目数据
      if (punctuationData.status === 'fulfilled') {
        setRecentPunctuationProjects(punctuationData.value.items || [])
        const totalDiffs = (punctuationData.value.items || []).reduce(
          (sum, p) => sum + (p.metadata?.total_differences || 0),
          0
        )
        setStats(prev => ({
          ...prev,
          punctuationProjects: punctuationData.value.total || 0,
          totalDifferences: totalDiffs,
        }))
      }

      // 处理版本对勘项目数据
      if (collationData.status === 'fulfilled') {
        setRecentCollationProjects(collationData.value.items || [])
        setStats(prev => ({
          ...prev,
          collationProjects: collationData.value.total || 0,
        }))
      }
    } catch (error: any) {
      console.error('加载仪表板数据失败:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDashboardData()
  }, [loadDashboardData])

  // 快捷入口卡片（含统计数字）
  const quickActions = [
    {
      title: 'CBETA 导入',
      description: '从 CBETA 数据库导入佛典文本',
      icon: <DatabaseOutlined style={{ fontSize: 32, color: '#fa8c16' }} />,
      path: '/cbeta-import',
      color: '#fa8c16',
      count: 0,
    },
    {
      title: '版本对勘',
      description: '多个版本文本的综合校勘分析',
      icon: <BookOutlined style={{ fontSize: 32, color: '#722ed1' }} />,
      path: '/multi-collation',
      color: '#722ed1',
      count: stats.collationProjects,
    },
    {
      title: '标点版本对比',
      description: '上传两个带标点文本，分析标点差异',
      icon: <DiffOutlined style={{ fontSize: 32, color: '#384E77' }} />,
      path: '/punctuation-compare',
      color: '#384E77',
      count: stats.punctuationProjects,
    },
  ]

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string; icon: React.ReactNode }> = {
      completed: { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
      processing: { color: 'processing', text: '处理中', icon: <SyncOutlined spin /> },
      pending: { color: 'default', text: '待处理', icon: <ClockCircleOutlined /> },
      active: { color: 'success', text: '进行中', icon: <SyncOutlined /> },
    }
    const config = statusMap[status] || statusMap.pending
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    )
  }

  // 格式化时间
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 60) return `${minutes} 分钟前`
    if (hours < 24) return `${hours} 小时前`
    if (days < 7) return `${days} 天前`
    return date.toLocaleDateString('zh-CN')
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
        <p style={{ marginTop: 16, color: '#666' }}>加载仪表板数据...</p>
      </div>
    )
  }

  return (
    <div style={{ padding: '0' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ marginBottom: 8 }}>
          工作台
        </Title>
        <Paragraph type="secondary">
          佛典标点与校勘研究平台 - 项目概览与快速入口
        </Paragraph>
      </div>

      {/* 快捷入口 */}
      <Card
        title="快捷入口"
        style={{ marginBottom: 24 }}
        bodyStyle={{ padding: '12px 24px' }}
      >
        <Row gutter={[16, 16]}>
          {quickActions.map((action) => (
            <Col xs={24} sm={12} md={6} key={action.path}>
              <Badge
                count={action.count}
                offset={[-10, 10]}
                style={{ backgroundColor: action.color }}
              >
                <Card
                  hoverable
                  onClick={() => navigate(action.path)}
                  style={{ textAlign: 'center', height: '100%', width: '100%' }}
                  bodyStyle={{ padding: '24px 16px' }}
                >
                  <div style={{ marginBottom: 12 }}>{action.icon}</div>
                  <Title level={5} style={{ marginBottom: 8 }}>
                    {action.title}
                  </Title>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {action.description}
                  </Text>
                </Card>
              </Badge>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 最近项目列表 */}
      <Row gutter={[16, 16]}>
        {/* 最近标点对比项目 */}
        <Col xs={24} lg={8}>
          <Card
            style={{ height: '100%', minHeight: 180 }}
            title={
              <Space>
                <DiffOutlined />
                <span>最近标点对比项目</span>
              </Space>
            }
            extra={
              <Button
                type="link"
                icon={<PlusOutlined />}
                onClick={() => navigate('/punctuation-compare')}
              >
                新建
              </Button>
            }
          >
            {recentPunctuationProjects.length > 0 ? (
              <List
                dataSource={recentPunctuationProjects}
                renderItem={(item) => (
                  <List.Item
                    style={{ cursor: 'pointer', padding: '12px 0' }}
                    onClick={() => {
                      navigate('/punctuation-compare')
                      message.info(`请在标点对比页面打开项目: ${item.title}`)
                    }}
                    actions={[
                      <Button type="text" size="small" icon={<RightOutlined />} />,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <Text strong style={{ maxWidth: 200 }} ellipsis>
                            {item.title}
                          </Text>
                          {getStatusTag(item.status)}
                        </Space>
                      }
                      description={
                        <Space direction="vertical" size={0}>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {item.metadata?.version1_name || '版本A'} vs{' '}
                            {item.metadata?.version2_name || '版本B'}
                          </Text>
                          <Space size={16}>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              差异: {item.metadata?.total_differences || 0} 处
                            </Text>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {formatTime(item.updated_at)}
                            </Text>
                          </Space>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Empty
                description="暂无标点对比项目"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => navigate('/punctuation-compare')}
                >
                  创建第一个项目
                </Button>
              </Empty>
            )}
          </Card>
        </Col>

        {/* 最近版本对勘项目 */}
        <Col xs={24} lg={8}>
          <Card
            style={{ height: '100%', minHeight: 180 }}
            title={
              <Space>
                <BookOutlined />
                <span>最近版本对勘项目</span>
              </Space>
            }
            extra={
              <Button
                type="link"
                icon={<PlusOutlined />}
                onClick={() => navigate('/multi-collation')}
              >
                新建
              </Button>
            }
          >
            {recentCollationProjects.length > 0 ? (
              <List
                dataSource={recentCollationProjects}
                renderItem={(item) => (
                  <List.Item
                    style={{ cursor: 'pointer', padding: '12px 0' }}
                    onClick={() => navigate('/multi-collation')}
                    actions={[
                      <Button type="text" size="small" icon={<RightOutlined />} />,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <Text strong style={{ maxWidth: 150 }} ellipsis>
                            {item.title}
                          </Text>
                          {getStatusTag(item.status)}
                        </Space>
                      }
                      description={
                        <Space direction="vertical" size={0}>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            底本：{item.metadata?.base_name || '未知'}
                          </Text>
                          <Space size={16}>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {item.metadata?.collation_count || 0} 个校本
                            </Text>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {formatTime(item.updated_at)}
                            </Text>
                          </Space>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Empty
                description="暂无版本对勘项目"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => navigate('/multi-collation')}
                >
                  创建第一个项目
                </Button>
              </Empty>
            )}
          </Card>
        </Col>
      </Row>

    </div>
  )
}
