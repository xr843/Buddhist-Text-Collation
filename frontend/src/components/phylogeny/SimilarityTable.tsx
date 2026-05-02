/**
 * 相似度矩阵表格组件
 */
import { useMemo } from 'react'
import { Card, Table, Tag, Tooltip, Space, Typography } from 'antd'
import { SYSTEM_COLORS } from './constants'
import { createVersionNameSimplifier } from './utils'
import type { SimilarityMatrix } from './types'

const { Text } = Typography

interface SimilarityTableProps {
  similarityMatrix: SimilarityMatrix
  chartHeight?: number
}

export default function SimilarityTable({ similarityMatrix, chartHeight = 400 }: SimilarityTableProps) {
  const columns = useMemo(() => {
    const names = similarityMatrix.names
    const systems = similarityMatrix.systems || {}
    const n = names.length
    const isLarge = n > 10
    const isHuge = n > 15

    const maxLen = isHuge ? 10 : isLarge ? 12 : 14
    const getShortName = createVersionNameSimplifier(maxLen)

    return [
      {
        title: '',
        dataIndex: 'name',
        key: 'name',
        fixed: 'left' as const,
        width: isHuge ? 80 : isLarge ? 100 : 120,
        render: (name: string) => {
          const system = systems[name]
          const shortName = getShortName(name)
          return (
            <Tooltip title={name}>
              <Space direction="vertical" size={0}>
                <Text strong style={{ fontSize: isHuge ? 10 : 12 }}>{shortName}</Text>
                {!isLarge && system && system !== '未知' && (
                  <Tag
                    color={SYSTEM_COLORS[system] || SYSTEM_COLORS['未知']}
                    style={{ fontSize: 9 }}
                  >
                    {system}
                  </Tag>
                )}
              </Space>
            </Tooltip>
          )
        },
      },
      ...names.map((name, idx) => ({
        title: (
          <Tooltip title={name}>
            <span style={{ fontSize: isHuge ? 9 : 10 }}>{getShortName(name)}</span>
          </Tooltip>
        ),
        dataIndex: `col_${idx}`,
        key: `col_${idx}`,
        width: isHuge ? 50 : isLarge ? 60 : 70,
        align: 'center' as const,
        render: (val: number, _record: any, rowIdx: number) => {
          if (rowIdx === idx) return <Text type="secondary">-</Text>
          const color = val > 0.95 ? '#52c41a' : val > 0.9 ? '#1890ff' : val > 0.8 ? '#fa8c16' : '#f5222d'
          return (
            <Text style={{ color, fontWeight: val > 0.9 ? 'bold' : 'normal', fontSize: isHuge ? 10 : 12 }}>
              {isHuge ? `${Math.round(val * 100)}` : `${(val * 100).toFixed(1)}%`}
            </Text>
          )
        },
      })),
    ]
  }, [similarityMatrix])

  const dataSource = useMemo(() => {
    return similarityMatrix.names.map((name, i) => ({
      key: i,
      name,
      ...similarityMatrix.names.reduce((acc, _, j) => ({
        ...acc,
        [`col_${j}`]: similarityMatrix.matrix[i][j],
      }), {}),
    }))
  }, [similarityMatrix])

  return (
    <Card title="相似度数值表" size="small">
      <Table
        columns={columns}
        dataSource={dataSource}
        pagination={similarityMatrix.names.length > 15 ? { pageSize: 10, size: 'small' } : false}
        bordered
        size="small"
        scroll={{ x: 'max-content', y: chartHeight - 100 }}
      />
    </Card>
  )
}
