/**
 * 控制栏组件
 */

import { Typography, Switch, Space, Tooltip, InputNumber } from 'antd'
import { EyeOutlined, CompressOutlined, ColumnWidthOutlined } from '@ant-design/icons'

const { Text } = Typography

interface ControlBarProps {
  diffOnlyMode: boolean
  charsPerLine: number
  filteredLinesCount: number
  totalLinesCount: number
  onDiffOnlyModeChange: (value: boolean) => void
  onCharsPerLineChange: (value: number) => void
}

export default function ControlBar({
  diffOnlyMode,
  charsPerLine,
  filteredLinesCount,
  totalLinesCount,
  onDiffOnlyModeChange,
  onCharsPerLineChange,
}: ControlBarProps) {
  return (
    <div
      style={{
        padding: '8px 16px',
        background: '#fafafa',
        borderBottom: '1px solid #e8e8e8',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 12,
      }}
    >
      <Space size="middle">
        <Tooltip title="仅显示有差异的行，方便快速对比分析">
          <Space>
            <Switch
              checked={diffOnlyMode}
              onChange={onDiffOnlyModeChange}
              size="small"
            />
            <Text
              style={{ fontSize: 13, cursor: 'pointer' }}
              onClick={() => onDiffOnlyModeChange(!diffOnlyMode)}
            >
              {diffOnlyMode ? (
                <>
                  <CompressOutlined /> 仅差异
                </>
              ) : (
                <>
                  <EyeOutlined /> 全文
                </>
              )}
            </Text>
          </Space>
        </Tooltip>

        <Tooltip title="调整每行显示的字符数">
          <Space size="small">
            <ColumnWidthOutlined style={{ color: '#666' }} />
            <Text type="secondary" style={{ fontSize: 12 }}>
              每行:
            </Text>
            <InputNumber
              min={30}
              max={120}
              value={charsPerLine}
              onChange={(v) => v && onCharsPerLineChange(v)}
              size="small"
              style={{ width: 65 }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              字
            </Text>
          </Space>
        </Tooltip>
      </Space>

      <Text type="secondary" style={{ fontSize: 12 }}>
        {diffOnlyMode ? (
          <>
            共{' '}
            <Text strong style={{ color: '#1890ff' }}>
              {filteredLinesCount}
            </Text>{' '}
            行差异（全文 {totalLinesCount} 行）
          </>
        ) : (
          <>共 {totalLinesCount} 行</>
        )}
      </Text>
    </div>
  )
}
