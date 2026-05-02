/**
 * 对比工作区组件
 */

import { Card, Button, Space, Tag, Tooltip, Empty, Typography } from 'antd'
import { SaveOutlined, FileTextOutlined, FormOutlined } from '@ant-design/icons'
import PunctuationCompareView from '../../components/PunctuationCompareView'
import type { PunctuationComparisonResponse, PunctuationDifference } from './types'

const { Text } = Typography

interface CompareWorkspaceProps {
  result: PunctuationComparisonResponse
  selectedDiff: PunctuationDifference | null
  filteredDifferences: PunctuationDifference[]
  decisionMode: boolean
  decisionCount: number
  currentProjectId: string | null
  savingDecisions: boolean
  generatingDefinitive: boolean
  reviewDrawerVisible: boolean
  onDecisionModeToggle: () => void
  onSaveDecisions: () => void
  onGenerateDefinitive: () => void
  onReviewDrawerToggle: () => void
  onDiffClick: (diff: PunctuationDifference, index: number) => void
}

export default function CompareWorkspace({
  result,
  selectedDiff,
  filteredDifferences,
  decisionMode,
  decisionCount,
  currentProjectId,
  savingDecisions,
  generatingDefinitive,
  reviewDrawerVisible,
  onDecisionModeToggle,
  onSaveDecisions,
  onGenerateDefinitive,
  onReviewDrawerToggle,
  onDiffClick,
}: CompareWorkspaceProps) {
  return (
    <Card
      bodyStyle={{ padding: 0, height: 800 }}
      extra={
        <Space>
          {/* 判取模式开关 */}
          <Tooltip title={decisionMode ? '关闭判取模式' : '开启判取模式'}>
            <Button type={decisionMode ? 'primary' : 'default'} onClick={onDecisionModeToggle}>
              {decisionMode ? '✓ 判取模式' : '判取模式'}
              {decisionCount > 0 && (
                <Tag color="green" style={{ marginLeft: 4 }}>
                  {decisionCount}
                </Tag>
              )}
            </Button>
          </Tooltip>

          {/* 保存判取 */}
          {decisionCount > 0 && currentProjectId && (
            <Tooltip title="保存判取结果">
              <Button icon={<SaveOutlined />} onClick={onSaveDecisions} loading={savingDecisions}>
                保存判取
              </Button>
            </Tooltip>
          )}

          {/* 生成定本按钮 */}
          {currentProjectId && decisionCount > 0 && (
            <Tooltip title="基于判取结果生成标点定本">
              <Button
                type="primary"
                icon={<FileTextOutlined />}
                onClick={onGenerateDefinitive}
                loading={generatingDefinitive}
              >
                生成定本
              </Button>
            </Tooltip>
          )}

          {/* 审核面板 */}
          <Tooltip title="打开审核面板">
            <Button
              type={reviewDrawerVisible ? 'primary' : 'default'}
              icon={<FormOutlined />}
              onClick={onReviewDrawerToggle}
            >
              审核面板
            </Button>
          </Tooltip>
        </Space>
      }
    >
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div
          style={{
            padding: '8px 16px',
            borderBottom: '1px solid var(--color-border, #e8e8e8)',
            background: 'var(--color-bg-container, #fff)',
            fontWeight: 500,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>标点对比视图</span>
          <Text type="secondary" style={{ fontSize: 12 }}>
            点击差异高亮处查看详情
          </Text>
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          {result.punctuation_analysis?.sentence_alignment ? (
            <PunctuationCompareView
              sentenceAlignment={result.punctuation_analysis.sentence_alignment}
              differences={result.punctuation_analysis.differences}
              version1Name={result.version1_name}
              version2Name={result.version2_name}
              scrollToDiffId={selectedDiff?.id}
              onDiffClick={(diff) => {
                const index = filteredDifferences.findIndex((d) => d.id === diff.id)
                if (index !== -1) {
                  onDiffClick(diff, index)
                }
              }}
            />
          ) : (
            <Empty description="暂无对比数据" style={{ paddingTop: 100 }} />
          )}
        </div>
      </div>
    </Card>
  )
}
