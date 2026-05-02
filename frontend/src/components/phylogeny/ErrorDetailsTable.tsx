/**
 * 异文详情表格组件
 */
import { Card, Table, Tag, Typography, Empty, Tooltip } from 'antd'
import { CATEGORY_COLOR_MAP } from './constants'
import { createVersionNameSimplifier, getTypeName } from './utils'
import type { SharedErrorDetail, VariantType } from './types'

const { Text } = Typography

interface ErrorDetailsTableProps {
  selectedPair: string | null
  details: SharedErrorDetail[] | null
  variantType: VariantType
}

export default function ErrorDetailsTable({
  selectedPair,
  details,
  variantType,
}: ErrorDetailsTableProps) {
  const columns = [
    {
      title: '位置',
      dataIndex: 'position',
      key: 'position',
      width: 70,
      align: 'center' as const,
      render: (pos: number | string) => {
        if (typeof pos === 'string' && pos.startsWith('ins_')) {
          return <Text type="secondary">衍入</Text>
        }
        return pos
      }
    },
    {
      title: '底本',
      dataIndex: 'base_char',
      key: 'base_char',
      width: 50,
      align: 'center' as const,
      render: (c: string) => (
        <Text strong style={{ color: c === '(无)' ? '#999' : '#1890ff', fontSize: 14 }}>
          {c || '-'}
        </Text>
      )
    },
    {
      title: '异文',
      dataIndex: 'shared_char',
      key: 'shared_char',
      width: 50,
      align: 'center' as const,
      render: (c: string, record: any) => {
        const char = c || record.shared_error_char
        const category = record.category
        const color = CATEGORY_COLOR_MAP[category] || '#1890ff'
        return <Text strong style={{ color, fontSize: 14 }}>{char || '-'}</Text>
      }
    },
    {
      title: '类型',
      dataIndex: 'category',
      key: 'category',
      width: 60,
      align: 'center' as const,
      render: (cat: string) => {
        const colorMap: Record<string, string> = {
          error: 'red',
          variant: 'green',
          tuowen: 'orange',
          yanwen: 'orange',
        }
        return (
          <Tag color={colorMap[cat] || 'default'} style={{ fontSize: 10, margin: 0 }}>
            {getTypeName(cat)}
          </Tag>
        )
      }
    },
  ]

  return (
    <Card
      title={
        selectedPair
          ? `${getTypeName(variantType)}详情: ${selectedPair.replace('|', ' vs ')}`
          : `${getTypeName(variantType)}详情`
      }
      size="small"
      bodyStyle={{ padding: '12px' }}
    >
      {details ? (
        <Table
          columns={columns}
          dataSource={details.map((d, i) => ({ ...d, key: i }))}
          pagination={{ pageSize: 8, size: 'small', showSizeChanger: false }}
          bordered
          size="small"
          scroll={{ y: 280 }}
        />
      ) : (
        <Empty
          description="点击热力图中的单元格查看详情"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          style={{ margin: '40px 0' }}
        />
      )}
    </Card>
  )
}

interface VersionTotalTableProps {
  totalByVersion: Record<string, number>
  variantType: VariantType
}

export function VersionTotalTable({ totalByVersion, variantType }: VersionTotalTableProps) {
  if (Object.keys(totalByVersion).length === 0) return null

  const getShortName = createVersionNameSimplifier(12)

  return (
    <Card
      title={`各版本${getTypeName(variantType)}总数`}
      size="small"
      style={{ marginTop: 16 }}
      bodyStyle={{ padding: '8px 12px' }}
    >
      <Table
        columns={[
          {
            title: '版本',
            dataIndex: 'name',
            key: 'name',
            ellipsis: true,
            render: (name: string) => (
              <Tooltip title={name}>
                <Text style={{ fontSize: 12 }}>{getShortName(name)}</Text>
              </Tooltip>
            )
          },
          {
            title: '数量',
            dataIndex: 'count',
            key: 'count',
            width: 70,
            align: 'right' as const,
            sorter: (a: any, b: any) => a.count - b.count,
            defaultSortOrder: 'descend' as const,
            render: (count: number) => (
              <Text strong style={{ color: count > 1000 ? '#f5222d' : count > 500 ? '#fa8c16' : '#1890ff' }}>
                {count.toLocaleString()}
              </Text>
            )
          },
        ]}
        dataSource={Object.entries(totalByVersion).map(([name, count], i) => ({
          key: i,
          name,
          count: count as number
        }))}
        pagination={false}
        size="small"
        scroll={{ y: 150 }}
        showHeader={true}
      />
    </Card>
  )
}
