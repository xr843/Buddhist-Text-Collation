/**
 * 相似度热力图组件
 */
import { useMemo } from 'react'
import { Card, Tag, Space, Typography } from 'antd'
import ReactECharts from 'echarts-for-react'
import { SIMILARITY_COLOR_SCHEME } from './constants'
import { createVersionNameSimplifier, wrapTextByChars } from './utils'
import type { SimilarityMatrix } from './types'

const { Paragraph } = Typography

interface SimilarityHeatmapProps {
  similarityMatrix: SimilarityMatrix
}

export default function SimilarityHeatmap({ similarityMatrix }: SimilarityHeatmapProps) {
  const heatmapOption = useMemo(() => {
    const names = similarityMatrix.names
    const matrix = similarityMatrix.matrix
    const n = names.length

    // 根据版本数量动态调整参数
    const isLarge = n > 10
    const isHuge = n > 15
    const isMassive = n > 20

    // 计算非对角线数据的最小值和最大值
    let minVal = 1, maxVal = 0
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        if (i !== j) {
          minVal = Math.min(minVal, matrix[i][j])
          maxVal = Math.max(maxVal, matrix[i][j])
        }
      }
    }
    const rangeMin = Math.max(0, Math.floor(minVal * 100 - 2) / 100)
    const rangeMax = Math.min(1, Math.ceil(maxVal * 100 + 1) / 100)

    // 构建热力图数据
    const heatmapData: any[] = []
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        if (i === j) {
          heatmapData.push({
            value: [j, i, 1],
            itemStyle: { color: '#e8e8e8' }
          })
        } else {
          heatmapData.push([j, i, matrix[i][j]])
        }
      }
    }

    // 智能简化版本名称
    const maxNameLen = isMassive ? 10 : isHuge ? 12 : isLarge ? 14 : 16
    const getShortName = createVersionNameSimplifier(maxNameLen)
    const shortNames = names.map(getShortName)

    // 动态计算布局参数
    const cellSize = isMassive ? 28 : isHuge ? 32 : isLarge ? 38 : 45
    const labelFontSize = isMassive ? 7 : isHuge ? 8 : isLarge ? 9 : 10
    const leftMargin = isMassive ? 130 : isHuge ? 140 : isLarge ? 150 : 160
    const showLabels = n <= 12

    const axisLabelWrap = isMassive ? 2 : isHuge ? 3 : isLarge ? 4 : 0
    const xAxisRotate = isLarge ? 0 : 45
    const axisLabelColor = '#1a1a1a'
    const axisLabelLineHeight = isMassive ? 12 : isHuge ? 13 : 14
    const maxAxisLabelLines = axisLabelWrap
      ? Math.max(...shortNames.map(name => Math.ceil(name.length / axisLabelWrap)))
      : 1
    const maxLabelLength = Math.max(...shortNames.map(s => s.length))
    const rotateExtraSpace = xAxisRotate ? Math.max(60, maxLabelLength * 6) : 0
    const bottomMargin = Math.max(90, maxAxisLabelLines * axisLabelLineHeight + 50 + rotateExtraSpace)

    const chartHeight = Math.max(450, cellSize * n + bottomMargin + 60)

    return {
      tooltip: {
        position: 'top',
        formatter: (params: any) => {
          const data = params.data.value || params.data
          const i = data[1]
          const j = data[0]
          const value = data[2]
          if (i === j) return `${names[i]}：自身`
          return `<strong>${names[i]}</strong><br/>vs<br/><strong>${names[j]}</strong><br/><br/>相似度: <span style="color:#1890ff;font-weight:bold">${(value * 100).toFixed(1)}%</span>`
        },
        backgroundColor: 'rgba(255,255,255,0.95)',
        borderColor: '#ddd',
        textStyle: { color: '#333' },
        extraCssText: 'box-shadow: 0 2px 8px rgba(0,0,0,0.15);',
      },
      grid: {
        left: leftMargin,
        right: 20,
        top: 20,
        bottom: bottomMargin,
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: shortNames,
        splitArea: { show: true },
        axisLabel: {
          rotate: xAxisRotate,
          interval: 0,
          fontSize: isMassive ? 10 : isHuge ? 11 : 12,
          fontWeight: 700,
          color: axisLabelColor,
          lineHeight: isMassive ? 12 : isHuge ? 13 : 14,
          align: xAxisRotate ? 'right' : 'center',
          verticalAlign: xAxisRotate ? 'top' : 'middle',
          margin: xAxisRotate ? 15 : 12,
          hideOverlap: false,
          textShadowColor: 'rgba(255,255,255,0.9)',
          textShadowBlur: 2,
          formatter: (value: string) => wrapTextByChars(value, axisLabelWrap),
        },
        position: 'bottom',
      },
      yAxis: {
        type: 'category',
        data: shortNames,
        splitArea: { show: true },
        axisLabel: {
          interval: 0,
          fontSize: isMassive ? 10 : isHuge ? 11 : 12,
          fontWeight: 700,
          color: axisLabelColor,
          textShadowColor: 'rgba(255,255,255,0.9)',
          textShadowBlur: 2,
          margin: 8,
        },
      },
      visualMap: {
        show: false,
        min: rangeMin,
        max: rangeMax,
        calculable: false,
        inRange: {
          color: SIMILARITY_COLOR_SCHEME,
        },
        outOfRange: {
          color: '#f0f0f0',
        },
      },
      series: [{
        name: '相似度',
        type: 'heatmap',
        data: heatmapData,
        label: {
          show: showLabels,
          formatter: (params: any) => {
            const data = params.data.value || params.data
            const x = data[0]
            const y = data[1]
            const value = data[2]
            if (x === y) return '-'
            if (value == null || value < 0) return '?'
            return isLarge ? `${Math.round(value * 100)}` : `${(value * 100).toFixed(1)}%`
          },
          fontSize: labelFontSize,
          fontWeight: 'bold',
          color: '#000',
          textShadowColor: 'rgba(255,255,255,0.8)',
          textShadowBlur: 2,
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: isMassive ? 0.5 : 1,
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      }],
      _chartHeight: chartHeight,
      _gridLeft: leftMargin,
      _gridRight: 20,
      _rangeMin: rangeMin,
      _rangeMax: rangeMax,
    }
  }, [similarityMatrix])

  return (
    <Card
      title={
        <Space>
          <span>版本相似度热力图</span>
          {similarityMatrix.names.length > 12 && (
            <Tag color="blue">鼠标悬停查看数值</Tag>
          )}
        </Space>
      }
      size="small"
    >
      <ReactECharts
        option={heatmapOption}
        style={{ height: (heatmapOption as any)._chartHeight || 450 }}
        opts={{ renderer: 'canvas' }}
      />
      <div
        style={{
          marginTop: 8,
          marginLeft: (heatmapOption as any)._gridLeft || 0,
          marginRight: (heatmapOption as any)._gridRight || 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Paragraph type="secondary" style={{ fontSize: 12, minWidth: 44, textAlign: 'right', margin: 0 }}>
            {`${Math.round(((heatmapOption as any)._rangeMin ?? 0) * 100)}%`}
          </Paragraph>
          <div
            style={{
              width: 240,
              height: 10,
              background: `linear-gradient(90deg, ${SIMILARITY_COLOR_SCHEME.join(',')})`,
              borderRadius: 4,
              border: '1px solid #d9d9d9',
            }}
          />
          <Paragraph type="secondary" style={{ fontSize: 12, minWidth: 44, margin: 0 }}>
            {`${Math.round(((heatmapOption as any)._rangeMax ?? 1) * 100)}%`}
          </Paragraph>
        </div>
        <Paragraph type="secondary" style={{ fontSize: 12, marginTop: 8, marginBottom: 0, textAlign: 'center' }}>
          热力图展示所有版本两两之间的真实相似度（基于文本直接对比计算）
        </Paragraph>
      </div>
    </Card>
  )
}
