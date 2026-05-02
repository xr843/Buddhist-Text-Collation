/**
 * 版本源流图组件
 *
 * 使用 ECharts Graph 展示版本传承关系的有向无环图(DAG)
 * 视觉编码：
 * - 节点颜色：按系统（中系黄/南系绿/北系蓝）
 * - 节点大小：按版本重要性（祖本较大）
 * - 边粗细：按传承置信度
 * - 边样式：实线=高置信度，虚线=推测
 */
import { useMemo, useState } from 'react'
import { Card, Row, Col, Tag, Tooltip, Typography, Empty, Alert, Table, Divider, Space } from 'antd'
import { BulbOutlined, NodeIndexOutlined, InfoCircleOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { SYSTEM_COLORS } from './constants'
import { createVersionNameSimplifier } from './utils'
import type { LineageData, LineageNode, LineageEdge } from './types'

const { Text, Paragraph } = Typography

interface LineageGraphProps {
  lineageData?: LineageData
}

// 系统颜色配置（与 constants.ts 保持一致）
const getSystemColor = (system: string): string => {
  return SYSTEM_COLORS[system] || SYSTEM_COLORS['未知']
}

// 计算节点层级（基于年代）
const calculateYearLevels = (nodes: LineageNode[]): Map<string, number> => {
  const levels = new Map<string, number>()
  if (nodes.length === 0) return levels

  // 按年代排序（year 可能是 number 或 string，统一为 number 比较）
  const sortedYears = [...new Set(nodes.map(n => n.year))].sort(
    (a, b) => Number(a) - Number(b)
  )

  // 为每个独特的年代分配层级
  sortedYears.forEach((year, index) => {
    nodes.filter(n => n.year === year).forEach(n => {
      levels.set(n.id, index)
    })
  })

  return levels
}

export default function LineageGraph({ lineageData }: LineageGraphProps) {
  const [selectedEdge, setSelectedEdge] = useState<LineageEdge | null>(null)

  // 处理图表数据
  const chartOption = useMemo(() => {
    if (!lineageData || lineageData.nodes.length === 0) {
      return null
    }

    const { nodes, edges } = lineageData
    const yearLevels = calculateYearLevels(nodes)
    const maxLevel = Math.max(...Array.from(yearLevels.values()), 0)

    // 按系统分组节点以计算 x 位置
    const systemGroups = new Map<string, LineageNode[]>()
    nodes.forEach(node => {
      const system = node.system || '未知'
      if (!systemGroups.has(system)) {
        systemGroups.set(system, [])
      }
      systemGroups.get(system)!.push(node)
    })

    // 系统顺序：中系、南系、北系、其他
    const systemOrder = ['中系', '南系', '北系', '近现代藏经', '未知']
    const sortedSystems = [...systemGroups.keys()].sort((a, b) => {
      const idxA = systemOrder.indexOf(a)
      const idxB = systemOrder.indexOf(b)
      return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB)
    })

    // 为每个系统分配 x 区域
    const systemXBase = new Map<string, number>()
    const systemWidth = 100 / Math.max(sortedSystems.length, 1)
    sortedSystems.forEach((system, idx) => {
      systemXBase.set(system, idx * systemWidth + systemWidth / 2)
    })

    // 版本名称简化器
    const getShortName = createVersionNameSimplifier(12)

    // 构建 ECharts 节点数据
    const graphNodes = nodes.map((node) => {
      const system = node.system || '未知'
      const level = yearLevels.get(node.id) || 0
      const systemNodes = systemGroups.get(system) || []
      const nodeIndexInSystem = systemNodes.findIndex(n => n.id === node.id)
      const nodeCountInLevel = systemNodes.filter(n => yearLevels.get(n.id) === level).length

      // 计算位置
      const baseX = systemXBase.get(system) || 50
      const offsetX = nodeCountInLevel > 1
        ? (nodeIndexInSystem % nodeCountInLevel - (nodeCountInLevel - 1) / 2) * 15
        : 0
      const x = baseX + offsetX
      const y = maxLevel > 0 ? (level / maxLevel) * 80 + 10 : 50

      return {
        id: node.id,
        name: getShortName(node.name),
        fullName: node.name,
        x,
        y,
        symbolSize: node.is_ancestor ? 45 : 35,
        itemStyle: {
          color: getSystemColor(system),
          borderColor: '#fff',
          borderWidth: 2,
          shadowColor: 'rgba(0, 0, 0, 0.2)',
          shadowBlur: 5,
        },
        label: {
          show: true,
          position: 'bottom',
          distance: 8,
          fontSize: 11,
          fontWeight: 'bold',
          color: '#333',
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          padding: [2, 4],
          borderRadius: 2,
          formatter: () => `${getShortName(node.name)}\n(${node.year})`,
        },
        // 存储原始数据供 tooltip 使用
        _nodeData: node,
      }
    })

    // 构建 ECharts 边数据
    const graphLinks = edges.map(edge => {
      const confidence = edge.confidence || 0
      const lineWidth = Math.max(1, Math.min(5, confidence / 20))
      const lineType = confidence >= 70 ? 'solid' : 'dashed'

      return {
        source: edge.source,
        target: edge.target,
        lineStyle: {
          color: confidence >= 70 ? '#1890ff' : '#aaa',
          width: lineWidth,
          type: lineType,
          curveness: 0.1,
        },
        emphasis: {
          lineStyle: {
            width: lineWidth + 2,
            shadowColor: 'rgba(0, 0, 0, 0.3)',
            shadowBlur: 5,
          },
        },
        // 存储原始数据
        _edgeData: edge,
      }
    })

    return {
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255,255,255,0.95)',
        borderColor: '#ddd',
        textStyle: { color: '#333' },
        extraCssText: 'box-shadow: 0 2px 8px rgba(0,0,0,0.15); max-width: 300px;',
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            const node = params.data._nodeData as LineageNode
            return `
              <div style="font-weight:bold;margin-bottom:4px;">${node.name}</div>
              <div>年代: ${node.year}</div>
              <div>系统: <span style="color:${getSystemColor(node.system || '未知')}">${node.system || '未知'}</span></div>
              ${node.city ? `<div>刻印地: ${node.city}</div>` : ''}
              ${node.period ? `<div>时期: ${node.period}</div>` : ''}
              ${node.is_ancestor ? '<div style="color:#faad14;margin-top:4px;">祖本</div>' : ''}
            `
          } else if (params.dataType === 'edge') {
            const edge = params.data._edgeData as LineageEdge
            return `
              <div style="font-weight:bold;margin-bottom:4px;">传承关系</div>
              <div>${edge.source}</div>
              <div style="color:#999;">↓</div>
              <div>${edge.target}</div>
              <div style="margin-top:8px;border-top:1px solid #eee;padding-top:8px;">
                <div>置信度: ${edge.confidence}%</div>
                ${edge.similarity ? `<div>相似度: ${edge.similarity}%</div>` : ''}
                ${edge.shared_errors ? `<div>共同讹误: ${edge.shared_errors}处</div>` : ''}
                ${edge.evidence?.length ? `<div>证据: ${edge.evidence.join('、')}</div>` : ''}
              </div>
            `
          }
          return ''
        },
      },
      series: [{
        type: 'graph',
        layout: 'none',
        roam: true,
        zoom: 0.9,
        draggable: true,
        coordinateSystem: null,
        data: graphNodes,
        links: graphLinks,
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [0, 10],
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 4,
          },
        },
        lineStyle: {
          opacity: 0.9,
        },
      }],
    }
  }, [lineageData])

  // 处理边点击事件
  const handleChartClick = (params: any) => {
    if (params.dataType === 'edge' && params.data?._edgeData) {
      setSelectedEdge(params.data._edgeData)
    } else {
      setSelectedEdge(null)
    }
  }

  // 如果没有数据，显示空状态
  if (!lineageData) {
    return (
      <Card title="版本源流图" size="small">
        <Empty description="暂无版本源流数据（lineageData 为空）" />
      </Card>
    )
  }

  // 如果节点为空，显示调试信息
  if (lineageData.nodes.length === 0) {
    return (
      <Card title="版本源流图" size="small">
        <Empty description={`暂无版本源流数据（节点: ${lineageData.nodes?.length || 0}, 边: ${lineageData.edges?.length || 0}）`} />
      </Card>
    )
  }

  // 准备表格数据
  const edgeTableData = lineageData.edges.map((edge, idx) => ({
    key: idx,
    source: edge.source,
    target: edge.target,
    confidence: edge.confidence,
    similarity: edge.similarity,
    shared_errors: edge.shared_errors,
    evidence: edge.evidence?.join('、') || '-',
    is_known: edge.is_known,
  }))

  const edgeColumns = [
    {
      title: '源版本',
      dataIndex: 'source',
      key: 'source',
      width: 150,
      ellipsis: true,
    },
    {
      title: '目标版本',
      dataIndex: 'target',
      key: 'target',
      width: 150,
      ellipsis: true,
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 80,
      sorter: (a: any, b: any) => a.confidence - b.confidence,
      defaultSortOrder: 'descend' as const,
      render: (v: number) => (
        <Tag color={v >= 70 ? 'blue' : v >= 50 ? 'orange' : 'default'}>
          {v}%
        </Tag>
      ),
    },
    {
      title: '证据',
      dataIndex: 'evidence',
      key: 'evidence',
      ellipsis: true,
    },
  ]

  return (
    <Row gutter={[16, 16]}>
      {/* 左侧：源流图（占一半宽度） */}
      <Col xs={24} lg={12}>
        <Card
          title={
            <Space>
              <NodeIndexOutlined />
              <span>版本源流图</span>
              <Tooltip title="箭头表示传承方向（年代早→晚），实线表示高置信度关系，虚线表示推测关系">
                <InfoCircleOutlined style={{ color: '#999' }} />
              </Tooltip>
            </Space>
          }
          size="small"
          style={{ height: '100%' }}
          styles={{ body: { height: 'calc(100% - 40px)', display: 'flex', flexDirection: 'column' } }}
        >
          {chartOption && (
            <ReactECharts
              option={chartOption}
              style={{ flex: 1, minHeight: 450 }}
              onEvents={{ click: handleChartClick }}
              opts={{ renderer: 'canvas' }}
            />
          )}

          {/* 图例 */}
          <div style={{ marginTop: 12, display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'center' }}>
            {Object.entries(SYSTEM_COLORS).map(([system, color]) => (
              <Space key={system} size={4}>
                <div
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: color,
                    border: '1px solid #fff',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.2)',
                  }}
                />
                <Text type="secondary" style={{ fontSize: 12 }}>{system}</Text>
              </Space>
            ))}
          </div>

          <Divider style={{ margin: '8px 0' }} />

          <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
            <Space size={4}>
              <div style={{ width: 30, height: 2, backgroundColor: '#1890ff' }} />
              <Text type="secondary" style={{ fontSize: 12 }}>高置信度</Text>
            </Space>
            <Space size={4}>
              <div style={{ width: 30, height: 2, backgroundColor: '#aaa', borderStyle: 'dashed', borderWidth: '1px 0 0 0' }} />
              <Text type="secondary" style={{ fontSize: 12 }}>推测关系</Text>
            </Space>
          </div>
        </Card>
      </Col>

      {/* 右侧：上下两部分 */}
      <Col xs={24} lg={12}>
        <Row gutter={[0, 16]}>
          {/* 右上：分析结论 */}
          <Col span={24}>
            {lineageData.conclusions && lineageData.conclusions.length > 0 && (
              <Alert
                type="info"
                icon={<BulbOutlined />}
                message="版本源流分析结论"
                description={
                  <ul style={{ margin: '8px 0 0 0', paddingLeft: 20, maxHeight: 200, overflowY: 'auto' }}>
                    {lineageData.conclusions.map((c, i) => (
                      <li key={i} style={{ marginBottom: 4, whiteSpace: 'pre-wrap' }}>{c}</li>
                    ))}
                  </ul>
                }
              />
            )}
          </Col>

          {/* 右下：传承关系表 */}
          <Col span={24}>
            <Card title="传承关系列表" size="small">
              <Table
                dataSource={edgeTableData}
                columns={edgeColumns}
                size="small"
                pagination={{ pageSize: 8, size: 'small' }}
                scroll={{ x: 'max-content', y: 280 }}
              />
            </Card>
          </Col>

          {/* 选中的边详情 */}
          {selectedEdge && (
            <Col span={24}>
              <Card title="选中的传承关系" size="small">
                <Paragraph style={{ marginBottom: 4 }}>
                  <Text strong>{selectedEdge.source}</Text>
                  <Text type="secondary"> → </Text>
                  <Text strong>{selectedEdge.target}</Text>
                </Paragraph>
                <Space wrap>
                  <span>
                    <Text type="secondary">置信度: </Text>
                    <Tag color={selectedEdge.confidence >= 70 ? 'blue' : 'orange'}>
                      {selectedEdge.confidence}%
                    </Tag>
                  </span>
                  {selectedEdge.similarity && (
                    <span><Text type="secondary">相似度: </Text><Text>{selectedEdge.similarity}%</Text></span>
                  )}
                  {selectedEdge.shared_errors && (
                    <span><Text type="secondary">共同讹误: </Text><Text>{selectedEdge.shared_errors}处</Text></span>
                  )}
                  {selectedEdge.is_known && <Tag color="green">已知传承</Tag>}
                </Space>
                {selectedEdge.evidence && selectedEdge.evidence.length > 0 && (
                  <Paragraph style={{ marginTop: 4, marginBottom: 0 }}>
                    <Text type="secondary">证据: </Text>
                    <Text>{selectedEdge.evidence.join('、')}</Text>
                  </Paragraph>
                )}
              </Card>
            </Col>
          )}
        </Row>
      </Col>
    </Row>
  )
}
