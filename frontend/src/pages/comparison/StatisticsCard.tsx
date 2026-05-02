/**
 * 差异统计筛选卡片
 */

import { Card, Button, Space, Typography, Tag, Progress } from 'antd'
import { FilterOutlined, DownloadOutlined } from '@ant-design/icons'
import { PUNCTUATION_CATEGORIES, CATEGORY_DISPLAY } from './constants'
import type { PunctuationComparisonResponse } from './types'

const { Text } = Typography

interface StatisticsCardProps {
  result: PunctuationComparisonResponse
  selectedCategories: string[]
  filteredDifferencesCount: number
  reviewedCount: number
  reviewProgress: number
  onToggleCategory: (category: string) => void
  onSelectAllCategories: () => void
  onClearCategories: () => void
  onExportReport: () => void
}

export default function StatisticsCard({
  result,
  selectedCategories,
  filteredDifferencesCount,
  reviewedCount,
  reviewProgress,
  onToggleCategory,
  onSelectAllCategories,
  onClearCategories,
  onExportReport,
}: StatisticsCardProps) {
  return (
    <Card
      title={
        <>
          <FilterOutlined /> 差异统计与筛选
        </>
      }
      size="small"
      bodyStyle={{ padding: '12px 16px' }}
      extra={
        <Button type="primary" size="small" icon={<DownloadOutlined />} onClick={onExportReport}>
          导出报告
        </Button>
      }
    >
      <div>
        {/* 总差异数 + 审核进度 */}
        <div
          style={{
            marginBottom: 12,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Text strong style={{ fontSize: 15, color: '#1890ff' }}>
            总差异 {result.punctuation_analysis?.research_stats?.total_count || 0} 处
          </Text>
          <Space>
            <Text type="secondary" style={{ fontSize: 13 }}>
              已审核 {reviewedCount}/{filteredDifferencesCount}
            </Text>
            <Tag color={reviewProgress === 100 ? 'success' : 'processing'}>{reviewProgress}%</Tag>
          </Space>
        </div>

        {/* 审核进度条 */}
        {filteredDifferencesCount > 0 && (
          <div style={{ marginBottom: 12 }}>
            <Progress
              percent={reviewProgress}
              showInfo={false}
              strokeColor={{ '0%': '#67C23A', '100%': '#85CE61' }}
              size="small"
            />
          </div>
        )}

        {/* 分类筛选按钮 */}
        <div style={{ borderTop: '1px solid #e8e8e8', paddingTop: 8 }}>
          <div
            style={{
              marginBottom: 6,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Text type="secondary" style={{ fontSize: 12 }}>
              分类筛选
            </Text>
            <Space size={4}>
              {selectedCategories.length < 3 && (
                <Button
                  type="link"
                  size="small"
                  onClick={onSelectAllCategories}
                  style={{ padding: 0, height: 'auto', fontSize: 12 }}
                >
                  全选
                </Button>
              )}
              {selectedCategories.length > 0 && (
                <Button
                  type="link"
                  size="small"
                  onClick={onClearCategories}
                  style={{ padding: 0, height: 'auto', fontSize: 12 }}
                >
                  清除
                </Button>
              )}
            </Space>
          </div>
          <Space wrap>
            {PUNCTUATION_CATEGORIES.map((category) => (
              <Tag
                key={category}
                color={selectedCategories.includes(category) ? 'blue' : 'default'}
                style={{ cursor: 'pointer' }}
                onClick={() => onToggleCategory(category)}
              >
                {selectedCategories.includes(category) && '✓ '}
                {category} {CATEGORY_DISPLAY[category] || ''}
              </Tag>
            ))}
          </Space>
        </div>
      </div>
    </Card>
  )
}
