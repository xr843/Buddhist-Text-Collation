/**
 * 经论注疏对读页面
 *
 * 功能：
 * - 横排三栏布局：经论（底本）+ 两部注疏
 * - 支持《瑜伽师地论》与《瑜伽论记》《略纂》对读
 * - 基于 DILA 科判实现文本对齐标记
 * - 整卷显示，三栏独立滚动
 */

import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  Card,
  Row,
  Col,
  Select,
  Button,
  Spin,
  Empty,
  Typography,
  Space,
  message,
  Tag,
  Input,
  Slider,
  Dropdown,
  Tooltip,
  Divider,
} from 'antd'
import {
  SyncOutlined,
  ReadOutlined,
  SearchOutlined,
  FontSizeOutlined,
  BgColorsOutlined,
  ColumnHeightOutlined,
} from '@ant-design/icons'
import { apiFetchJson } from '../../utils/apiFetch'
import styles from './index.module.css'

const { Title, Text, Paragraph } = Typography
const { Option } = Select

// 类型定义
interface TextSegment {
  id: string
  text: string
  page: string
  line_start: string
  line_end: string
  div_type: string
  div_title: string
  refs: string[]
  base_ref?: string  // 注疏段落对应的底本节点ID
}

interface JuanContent {
  sutra_id: string
  juan_num: number
  title: string
  segments: TextSegment[]
}

interface ParallelReadingData {
  base: JuanContent | null
  commentaries: JuanContent[]
  total_segments: number
  current_index: number
  page_size: number
}

interface SutraInfo {
  id: string
  title: string
  author: string
  total_juans: number
  description: string
}

interface ReadingPreset {
  id: string
  name: string
  description: string
  base_id: string
  commentary_ids: string[]
  available_juans: number[]
}

// 护眼色配置
const eyeProtectionColors = [
  { label: '默认白', value: '#ffffff', textColor: '#333333' },
  { label: '护眼绿', value: '#C7EDCC', textColor: '#333333' },
  { label: '羊皮纸', value: '#FAF9DE', textColor: '#333333' },
  { label: '淡黄', value: '#FFF2E2', textColor: '#333333' },
  { label: '浅灰', value: '#EAEAEA', textColor: '#333333' },
]

export default function SutraParallelReader() {
  // 状态
  const [loading, setLoading] = useState(false)
  const [presets, setPresets] = useState<ReadingPreset[]>([])
  const [selectedPreset, setSelectedPreset] = useState<string>('')
  const [currentJuan, setCurrentJuan] = useState(1)
  const [parallelData, setParallelData] = useState<ParallelReadingData | null>(null)
  const [availableSutras, setAvailableSutras] = useState<SutraInfo[]>([])
  const [searchKeyword, setSearchKeyword] = useState<string>('')
  const [activeBaseNodeId, setActiveBaseNodeId] = useState<string | null>(null)  // 当前选中的底本节点

  // 阅读设置
  const [fontSize, setFontSize] = useState(16)
  const [lineHeight, setLineHeight] = useState(1.8)
  const [bgColorIndex, setBgColorIndex] = useState(0)

  // 注疏栏的ref，用于滚动定位
  const commentaryRefs = useRef<{ [key: string]: HTMLDivElement | null }>({})

  const bgColor = eyeProtectionColors[bgColorIndex]

  // 加载预设和可用经论
  useEffect(() => {
    loadPresets()
    loadAvailableSutras()
  }, [])

  const loadPresets = async () => {
    try {
      const data = await apiFetchJson<ReadingPreset[]>('/api/v1/sutra-reading/presets')
      setPresets(data)
      if (data.length > 0) {
        setSelectedPreset(data[0].id)
      }
    } catch (error) {
      console.error('加载预设失败:', error)
    }
  }

  const loadAvailableSutras = async () => {
    try {
      const data = await apiFetchJson<SutraInfo[]>('/api/v1/sutra-reading/sutras')
      setAvailableSutras(data)
    } catch (error) {
      console.error('加载经论列表失败:', error)
    }
  }

  // 加载整卷对读数据
  const loadParallelData = useCallback(async () => {
    const preset = presets.find((p) => p.id === selectedPreset)
    if (!preset) return

    setLoading(true)
    try {
      const commentaryIds = preset.commentary_ids.join(',')
      // 请求整卷数据，page_size 设为很大的数
      const url = `/api/v1/sutra-reading/parallel?base_id=${preset.base_id}&commentary_ids=${commentaryIds}&juan_num=${currentJuan}&segment_index=0&page_size=9999`

      const data = await apiFetchJson<ParallelReadingData>(url)
      setParallelData(data)
    } catch (error) {
      console.error('加载对读数据失败:', error)
      message.error('加载对读数据失败')
    } finally {
      setLoading(false)
    }
  }, [selectedPreset, currentJuan, presets])

  // 当选择变化时加载数据
  useEffect(() => {
    if (selectedPreset && currentJuan) {
      loadParallelData()
    }
  }, [selectedPreset, currentJuan, loadParallelData])

  // 获取经论信息
  const getSutraInfo = (sutraId: string): SutraInfo | undefined => {
    return availableSutras.find((s) => s.id === sutraId)
  }

  // 高亮文本中的搜索关键词
  const highlightText = (text: string, keyword: string) => {
    if (!keyword || !text) return text
    // 转义正则特殊字符，防止用户输入 ( [ * 等导致崩溃
    const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const parts = text.split(new RegExp(`(${escaped})`, 'gi'))
    return parts.map((part, index) =>
      part.toLowerCase() === keyword.toLowerCase() ? (
        <mark key={index} className={styles.highlight}>{part}</mark>
      ) : (
        part
      )
    )
  }

  // 计算哪些底本段落有注疏对应
  const baseNodeWithCommentary = React.useMemo(() => {
    const result = new Set<string>()
    if (parallelData) {
      for (const comm of parallelData.commentaries) {
        for (const seg of comm.segments) {
          if (seg.base_ref) {
            result.add(seg.base_ref)
          }
        }
      }
    }
    return result
  }, [parallelData])

  // 点击底本段落，滚动注疏到对应位置
  const handleBaseSegmentClick = (baseNodeId: string) => {
    // 只有有对应关系的才响应点击
    if (!baseNodeWithCommentary.has(baseNodeId)) {
      return
    }

    setActiveBaseNodeId(baseNodeId)

    // 找到所有引用此底本节点的注疏段落，并滚动到第一个
    if (parallelData) {
      for (const comm of parallelData.commentaries) {
        for (const seg of comm.segments) {
          if (seg.base_ref === baseNodeId) {
            const refKey = `${comm.sutra_id}_${seg.id}`
            const element = commentaryRefs.current[refKey]
            if (element) {
              element.scrollIntoView({ behavior: 'smooth', block: 'start' })
            }
            return
          }
        }
      }
    }
  }

  // 渲染文本栏
  const renderTextColumn = (
    title: string,
    author: string,
    segments: TextSegment[],
    isBase: boolean,
    colorTag: string,
    sutraId?: string  // 注疏的sutra_id，用于构建ref key
  ) => {
    return (
      <div className={styles.textColumn} style={{ backgroundColor: bgColor.value }}>
        <div className={styles.columnHeader}>
          <Tag color={colorTag}>{isBase ? '经论' : '注疏'}</Tag>
          <Text strong>{title}</Text>
          <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
            {author}
          </Text>
        </div>
        <div className={styles.columnContent} style={{ backgroundColor: bgColor.value }}>
          {segments.map((seg) => {
            // 判断是否高亮（注疏段落对应当前选中的底本段落）
            const isHighlighted = !isBase && activeBaseNodeId && seg.base_ref === activeBaseNodeId
            // 构建ref key
            const refKey = sutraId ? `${sutraId}_${seg.id}` : seg.id
            // 底本段落是否有注疏对应
            const hasCommentary = isBase && baseNodeWithCommentary.has(seg.id)

            return (
              <div
                key={seg.id}
                ref={!isBase ? (el) => { commentaryRefs.current[refKey] = el } : undefined}
                className={`${styles.textSegment} ${isHighlighted ? styles.highlightedSegment : ''} ${isBase && hasCommentary ? styles.hasCommentary : ''} ${isBase && !hasCommentary ? styles.noCommentary : ''}`}
                onClick={isBase && hasCommentary ? () => handleBaseSegmentClick(seg.id) : undefined}
                style={isBase && hasCommentary ? { cursor: 'pointer' } : undefined}
              >
                {seg.div_title && (
                  <div className={isBase ? styles.divTitle : styles.divTitleComm}>
                    {highlightText(seg.div_title, searchKeyword)}
                    {isBase && hasCommentary && (
                      <Tag color="green" style={{ marginLeft: 8, fontSize: 10 }}>有注疏</Tag>
                    )}
                  </div>
                )}
                <Paragraph
                  className={styles.segmentText}
                  style={{
                    fontSize: fontSize,
                    lineHeight: lineHeight,
                    color: bgColor.textColor,
                  }}
                >
                  {highlightText(seg.text, searchKeyword)}
                  {seg.page && (
                    <Text type="secondary" className={styles.pageRef}>
                      （{seg.page}）
                    </Text>
                  )}
                </Paragraph>
              </div>
            )
          })}
        </div>
        <div className={styles.columnFooter}>
          <Text type="secondary">共 {segments.length} 段</Text>
        </div>
      </div>
    )
  }

  const currentPreset = presets.find((p) => p.id === selectedPreset)

  return (
    <div className={styles.container}>
      {/* 页面标题 */}
      <div className={styles.header}>
        <Space>
          <ReadOutlined style={{ fontSize: 24 }} />
          <Title level={3} style={{ margin: 0 }}>
            经论注疏对读
          </Title>
        </Space>
      </div>

      {/* 控制栏 */}
      <Card className={styles.controlBar}>
        <Row gutter={16} align="middle">
          <Col>
            <Space>
              <Text>选择对读组合：</Text>
              <Select
                value={selectedPreset}
                onChange={setSelectedPreset}
                style={{ width: 280 }}
                placeholder="请选择"
              >
                {presets.map((preset) => (
                  <Option key={preset.id} value={preset.id}>
                    {preset.name}
                  </Option>
                ))}
              </Select>
            </Space>
          </Col>

          <Col>
            <Space>
              <Text>卷数：</Text>
              <Select
                value={currentJuan}
                onChange={(val) => setCurrentJuan(val)}
                style={{ width: 100 }}
              >
                {currentPreset?.available_juans.map((juan) => (
                  <Option key={juan} value={juan}>
                    卷{juan}
                  </Option>
                ))}
              </Select>
              <Text type="secondary">
                （共{currentPreset?.available_juans.length || 0}卷）
              </Text>
            </Space>
          </Col>

          <Col flex="auto">
            <Input.Search
              placeholder="输入关键词搜索..."
              allowClear
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onSearch={setSearchKeyword}
              style={{ maxWidth: 300 }}
              prefix={<SearchOutlined />}
            />
          </Col>

          <Col>
            <Button icon={<SyncOutlined />} onClick={loadParallelData}>
              刷新
            </Button>
          </Col>
        </Row>

        {/* 阅读设置栏 */}
        <Divider style={{ margin: '12px 0' }} />
        <Row gutter={16} align="middle">
          <Col>
            <Space>
              <Tooltip title="字体大小">
                <FontSizeOutlined />
              </Tooltip>
              <Slider
                min={14}
                max={24}
                value={fontSize}
                onChange={setFontSize}
                style={{ width: 80 }}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>{fontSize}px</Text>
            </Space>
          </Col>

          <Col>
            <Space>
              <Tooltip title="行高">
                <ColumnHeightOutlined />
              </Tooltip>
              <Slider
                min={1.5}
                max={2.5}
                step={0.1}
                value={lineHeight}
                onChange={setLineHeight}
                style={{ width: 60 }}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>{lineHeight}</Text>
            </Space>
          </Col>

          <Col>
            <Dropdown
              menu={{
                items: eyeProtectionColors.map((color, index) => ({
                  key: index.toString(),
                  label: (
                    <Space>
                      <div
                        style={{
                          width: 16,
                          height: 16,
                          backgroundColor: color.value,
                          border: '1px solid #d9d9d9',
                          borderRadius: 2,
                        }}
                      />
                      {color.label}
                    </Space>
                  ),
                  onClick: () => setBgColorIndex(index),
                })),
              }}
              trigger={['click']}
            >
              <Button icon={<BgColorsOutlined />} size="small">
                {bgColor.label}
              </Button>
            </Dropdown>
          </Col>
        </Row>
      </Card>

      {/* 对读内容区 - 三栏布局 */}
      <Spin spinning={loading} tip="加载中...">
        {parallelData?.base ? (
          <div className={styles.threeColumnLayout}>
            {/* 底本栏 */}
            {renderTextColumn(
              getSutraInfo(currentPreset?.base_id || '')?.title || '经论',
              getSutraInfo(currentPreset?.base_id || '')?.author || '',
              parallelData.base.segments,
              true,
              'blue'
            )}

            {/* 注疏栏 */}
            {parallelData.commentaries.map((comm) => (
              <React.Fragment key={comm.sutra_id}>
                {renderTextColumn(
                  comm.title || getSutraInfo(comm.sutra_id)?.title || '注疏',
                  getSutraInfo(comm.sutra_id)?.author || '',
                  comm.segments,
                  false,
                  'green',
                  comm.sutra_id  // 传入sutra_id用于构建ref
                )}
              </React.Fragment>
            ))}

            {/* 如果注疏不足两列，补空列 */}
            {parallelData.commentaries.length < 2 && (
              <div className={styles.textColumn}>
                <div className={styles.columnHeader}>
                  <Tag color="default">注疏</Tag>
                  <Text type="secondary">暂无更多注疏</Text>
                </div>
                <div className={styles.columnContent}>
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" />
                </div>
              </div>
            )}
          </div>
        ) : (
          <Card>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <span>
                  请选择对读组合和卷数
                  <br />
                  <Text type="secondary">
                    目前支持《瑜伽师地论》与《瑜伽论记》《略纂》对读
                  </Text>
                </span>
              }
            >
              {presets.length === 0 && (
                <Button type="primary" onClick={loadPresets}>
                  加载预设
                </Button>
              )}
            </Empty>
          </Card>
        )}
      </Spin>

      {/* 数据来源 */}
      <div className={styles.helpText}>
        <Text type="secondary">
          数据来源：
          <a
            href="https://ybh.dila.edu.tw"
            target="_blank"
            rel="noopener noreferrer"
          >
            DILA 瑜伽师地论数据库
          </a>
          ，完整显示注疏全文
        </Text>
      </div>
    </div>
  )
}
