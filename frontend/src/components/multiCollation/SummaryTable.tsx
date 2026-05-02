/**
 * 汇总统计表格组件
 * 从 MultiCollation.tsx 中提取
 */
import { Table, Tag, Tooltip } from 'antd'
import type { MultiCollationResponse } from '../../types/multiCollation'
import { parseVersionInfo } from '../../utils/versionParser'
import { SYSTEM_COLORS } from '../../constants/multiCollation'
import { getCollationDisplayOrder } from '../../utils/exportMultiCollation'

interface SummaryTableProps {
  result: MultiCollationResponse
}

/**
 * 渲染三层表头单元格
 */
function renderVersionHeader(fullName: string, isBase: boolean = false) {
  const info = parseVersionInfo(fullName)
  return (
    <Tooltip title={fullName}>
      <div style={{ textAlign: 'center', lineHeight: 1.3 }}>
        <div style={{
          fontSize: 11,
          color: SYSTEM_COLORS[info.system] || '#8c8c8c',
          fontWeight: 500,
        }}>
          {info.system}
        </div>
        <div style={{
          fontSize: 13,
          fontWeight: 'bold',
          color: isBase ? '#1890ff' : '#333',
        }}>
          {info.canon}
        </div>
        {info.sutra && (
          <div style={{ fontSize: 10, color: '#999' }}>
            {info.sutra}
          </div>
        )}
      </div>
    </Tooltip>
  )
}

export default function SummaryTable({ result }: SummaryTableProps) {
  const { summary } = result

  const collationDisplayOrder = getCollationDisplayOrder(summary.collation_names)

  const columns = [
    {
      title: '版本信息',
      dataIndex: 'type',
      key: 'type',
      fixed: 'left' as const,
      width: 100,
      render: (text: string, record: any) => {
        const colorMap: Record<string, string> = {
          variant: 'green',
          error: 'red',
          yanwen: 'orange',
          tuowen: 'purple',
          total: 'blue',
        }
        const isTotal = record.type_key === 'total'
        return (
          <Tag color={colorMap[record.type_key]} style={isTotal ? { fontWeight: 'bold' } : {}}>
            {text}
          </Tag>
        )
      },
    },
    ...collationDisplayOrder.map((origIdx) => ({
      title: renderVersionHeader(summary.collation_names[origIdx]),
      dataIndex: `col_${origIdx}`,
      key: `col_${origIdx}`,
      align: 'center' as const,
      render: (_: any, record: any) => record.values[origIdx],
    })),
    {
      title: '合计',
      dataIndex: 'total',
      key: 'total',
      align: 'center' as const,
      render: (total: number) => <strong>{total}</strong>,
    },
  ]

  const dataSource = summary.stats_table.rows.map((row, idx) => ({
    key: idx,
    ...row,
  }))

  // 计算总数行
  const totalRow = {
    key: 'total',
    type: '总数',
    type_key: 'total',
    values: summary.collation_names.map((_, colIdx) =>
      summary.stats_table.rows.reduce((sum, row) => sum + (row.values[colIdx] || 0), 0)
    ),
    total: summary.stats_table.rows.reduce((sum, row) => sum + (row.total || 0), 0),
  }

  return (
    <Table
      columns={columns}
      dataSource={[...dataSource, totalRow]}
      pagination={false}
      bordered
      size="middle"
      rowClassName={(record) => record.key === 'total' ? 'total-row' : ''}
    />
  )
}
