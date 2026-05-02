/**
 * CBETA数据导入组件
 * 从CBETA平台搜索和导入经文
 */
import { useState } from 'react'
import {
  Card,
  Input,
  Button,
  List,
  Space,
  Tag,
  message,
  Typography,
  Empty,
  Spin,
  Alert,
  Modal,
} from 'antd'
import {
  SearchOutlined,
  ImportOutlined,
  BookOutlined,
  ReadOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Text, Paragraph } = Typography
const { Search } = Input

interface CBETASutra {
  id: string
  title: string
  full_title?: string
  dynasty: string
  translator: string
  author?: string
  byline?: string
  juan?: number
  category?: string
}

interface CBETAImporterProps {
  onImport?: (sutraData: any) => void
}

export default function CBETAImporter({ onImport }: CBETAImporterProps) {
  const navigate = useNavigate()

  const [searchKeyword, setSearchKeyword] = useState('')
  const [searchResults, setSearchResults] = useState<CBETASutra[]>([])
  const [loading, setLoading] = useState(false)
  const [importing, setImporting] = useState(false)
  const [selectedSutra, setSelectedSutra] = useState<CBETASutra | null>(null)
  const [importModalOpen, setImportModalOpen] = useState(false)
  const [importedResult, setImportedResult] = useState<{
    sutra: CBETASutra
    sutraData: any
  } | null>(null)

  const closeImportModal = () => {
    setImportModalOpen(false)
    setImportedResult(null)
  }

  const formatNameForCollation = (sutra: CBETASutra) => {
    const title = (sutra.title || '').trim()
    const part = (sutra.id.match(/_(\d{3})$/) || [])[1] || ''
    if (title) {
      return part ? `CBETA_《${title}》_${part}` : `CBETA_《${title}》`
    }
    return `CBETA ${sutra.id}`
  }

  const buildExportUrl = (sutraId: string, variant: 'punct_notes' | 'punct' | 'plain') =>
    `/api/v1/cbeta/export/txt/${encodeURIComponent(sutraId)}?variant=${variant}`

  // 搜索经文
  const handleSearch = async (keyword: string) => {
    if (!keyword.trim()) {
      message.warning('请输入搜索关键词')
      return
    }

    setLoading(true)
    try {
      // 调用后端API搜索
      const response = await fetch(`/api/v1/cbeta/search?keyword=${encodeURIComponent(keyword)}`)
      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        message.error(data?.detail || '搜索失败')
        return
      }

      if (data.success) {
        setSearchResults(data.results)
        if (data.results.length === 0) {
          message.info('未找到相关经文')
        }
        return
      }

      message.error(data?.detail || data?.message || '搜索失败')
    } catch (error) {
      message.error(`搜索失败: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  // 导入经文
  const handleImport = async (sutra: CBETASutra) => {
    setImporting(true)
    setSelectedSutra(sutra)

    try {
      // 调用后端API获取经文详情
      const response = await fetch(`/api/v1/cbeta/fetch/${sutra.id}`)
      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        message.error(data?.detail || '导入失败')
        return
      }

      if (data.success) {
        const sutraData = data.sutra

        message.success(`成功导入《${sutra.title}》`)
        setImportedResult({ sutra, sutraData })
        setImportModalOpen(true)

        // 如果有回调函数，也调用它
        if (onImport) {
          onImport(sutraData)
        }
        return
      }

      message.error(data?.detail || data?.message || '导入失败')
    } catch (error) {
      message.error(`导入失败: ${error}`)
    } finally {
      setImporting(false)
      setSelectedSutra(null)
    }
  }

  return (
    <Card
      title={
        <Space>
          <BookOutlined />
          <span>从CBETA导入经文</span>
        </Space>
      }
      extra={
        null
      }
    >
      <Alert
        type="info"
        message="CBETA数据源"
        description={
          <div>
            <p>中华电子佛典协会（CBETA）提供高质量的佛典电子文本。</p>
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              <li>支持搜索大正藏、卍续藏等主要藏经</li>
              <li>导入的文本已包含CBETA的校勘记</li>
              <li>可作为底本或校本进入对勘流程</li>
              <li>点击经名可在线阅读经文</li>
            </ul>
          </div>
        }
        style={{ marginBottom: 16 }}
        showIcon
      />

      <Search
        placeholder="输入经名或经号，如：阿毘達磨俱舍論、瑜伽師地論卷第一、T1579_001"
        enterButton={<SearchOutlined />}
        size="large"
        loading={loading}
        onSearch={handleSearch}
        onChange={(e) => setSearchKeyword(e.target.value)}
        style={{ marginBottom: 16 }}
      />

      <Modal
        open={importModalOpen}
        onCancel={closeImportModal}
        title="导入成功"
        footer={null}
        width={640}
        destroyOnClose
      >
        {importedResult && (
          <Space direction="vertical" style={{ width: '100%' }} size={12}>
            <div>
              已成功从 CBETA 导入《{importedResult.sutra.title}》，共{' '}
              {importedResult.sutraData?.text?.length || 0} 字。
            </div>

            <Space wrap>
              <Button
                type="primary"
                onClick={() => {
                  const { sutra, sutraData } = importedResult
                  navigate('/multi-collation', {
                    state: {
                      fromCBETA: true,
                      baseText: sutraData.text,
                      baseName: formatNameForCollation(sutra),
                      cbetaCollations: sutraData.collations,
                      source: 'cbeta',
                    },
                  })
                  closeImportModal()
                }}
              >
                作为底本进入版本对勘
              </Button>

              <Button
                style={{
                  background: '#722ed1',
                  borderColor: '#722ed1',
                  color: '#fff',
                }}
                onClick={() => {
                  const { sutra, sutraData } = importedResult
                  navigate('/multi-collation', {
                    state: {
                      fromCBETA: true,
                      collationText: sutraData.text,
                      collationName: formatNameForCollation(sutra),
                      cbetaCollations: sutraData.collations,
                      source: 'cbeta',
                    },
                  })
                  closeImportModal()
                }}
              >
                作为校本进入版本对勘
              </Button>
            </Space>

            <div style={{ marginTop: 8 }}>
              <Text type="secondary">导出TXT：</Text>
            </div>

            <Space wrap>
              <a
                href={buildExportUrl(importedResult.sutra.id, 'punct_notes')}
                download
                target="_blank"
                rel="noreferrer"
              >
                <Button>含标点、校勘记（校注）</Button>
              </a>
              <a
                href={buildExportUrl(importedResult.sutra.id, 'punct')}
                download
                target="_blank"
                rel="noreferrer"
              >
                <Button>含标点</Button>
              </a>
              <a
                href={buildExportUrl(importedResult.sutra.id, 'plain')}
                download
                target="_blank"
                rel="noreferrer"
              >
                <Button>纯文本</Button>
              </a>
            </Space>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button onClick={closeImportModal}>关闭</Button>
            </div>
          </Space>
        )}
      </Modal>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size="large" tip="搜索中..." />
        </div>
      ) : searchResults.length > 0 ? (
        <List
          dataSource={searchResults}
          renderItem={(sutra) => (
            <List.Item
              actions={[
                <Button
                  icon={<ReadOutlined />}
                  onClick={() => navigate(`/cbeta/read/${sutra.id}`)}
                >
                  阅读
                </Button>,
                <Button
                  type="primary"
                  icon={<ImportOutlined />}
                  onClick={() => handleImport(sutra)}
                  loading={importing && selectedSutra?.id === sutra.id}
                >
                  导入
                </Button>,
              ]}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <Text
                      strong
                      style={{
                        fontSize: 16,
                        cursor: 'pointer',
                        color: '#1890ff',
                      }}
                      onClick={() => navigate(`/cbeta/read/${sutra.id}`)}
                    >
                      {sutra.full_title || sutra.title}
                    </Text>
                    <Tag color="blue">{sutra.id}</Tag>
                  </Space>
                }
                description={
                  sutra.byline ? (
                    <Space split="|">
                      <Text type="secondary">{sutra.byline}</Text>
                      {sutra.juan && <Text type="secondary">{sutra.juan}卷</Text>}
                      {sutra.category && <Tag>{sutra.category}</Tag>}
                    </Space>
                  ) : (
                    <Space split="|">
                      <Text type="secondary">{sutra.dynasty}</Text>
                      {sutra.author && sutra.author !== '未知' && (
                        <Text type="secondary">{sutra.author}</Text>
                      )}
                      <Text type="secondary">{sutra.translator} 译</Text>
                      {sutra.juan && <Text type="secondary">{sutra.juan}卷</Text>}
                      {sutra.category && <Tag>{sutra.category}</Tag>}
                    </Space>
                  )
                }
              />
            </List.Item>
          )}
        />
      ) : searchKeyword ? (
        <Empty
          description="未找到相关经文"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <Empty
          description="请输入关键词开始搜索"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Paragraph type="secondary" style={{ marginTop: 16 }}>
            <strong>搜索示例：</strong>
            <ul style={{ textAlign: 'left', display: 'inline-block' }}>
              <li>经名：金刚经、心经、法华经</li>
              <li>经名+卷次：瑜伽師地論卷第一、阿毘達磨俱舍論卷二十</li>
              <li>经号：T0235、T0251、T0262、T1558_001</li>
            </ul>
          </Paragraph>
        </Empty>
      )}
    </Card>
  )
}
