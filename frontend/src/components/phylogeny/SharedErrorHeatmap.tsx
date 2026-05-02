/**
 * 共同异文热力图组件
 */
import { useMemo } from 'react'
import { Card, Radio, Space } from 'antd'
import ReactECharts from 'echarts-for-react'
import { VARIANT_TYPE_CONFIG } from './constants'
import { createVersionNameSimplifier, wrapTextByChars, getMatrixByType } from './utils'
import type { SharedErrors, VariantType } from './types'

interface SharedErrorHeatmapProps {
  sharedErrors: SharedErrors
  variantType: VariantType
  onVariantTypeChange: (type: VariantType) => void
  onCellClick: (params: any) => void
}

export default function SharedErrorHeatmap({
  sharedErrors,
  variantType,
  onVariantTypeChange,
  onCellClick,
}: SharedErrorHeatmapProps) {
  const heatmapOption = useMemo(() => {
    const names = sharedErrors.names
    const n = names.length
    const isLarge = n > 10
    const isHuge = n > 15
    const maxLen = isHuge ? 10 : isLarge ? 12 : 14

    const getShortName = createVersionNameSimplifier(maxLen)
    const shortNames = names.map(getShortName)

    const config = VARIANT_TYPE_CONFIG[variantType]
    const matrix = getMatrixByType(sharedErrors, variantType)

    // 计算非对角线的最大值
    let maxValue = 0
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        if (i !== j && matrix[i][j] > maxValue) {
          maxValue = matrix[i][j]
        }
      }
    }

    // 构建热力图数据
    const heatmapData: [number, number, number][] = []
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        heatmapData.push([j, i, i === j ? -1 : matrix[i][j]])
      }
    }

    const cellSize = Math.max(40, Math.min(55, 400 / n))
    const chartHeight = Math.max(300, cellSize * n + 150)
    const leftMargin = isHuge ? 130 : isLarge ? 140 : 150
    const bottomMargin = isHuge ? 140 : isLarge ? 150 : 160

    return {
      tooltip: {
        position: 'top',
        formatter: (params: any) => {
          const i = params.data[1]
          const j = params.data[0]
          const value = params.data[2]
          if (i === j || value < 0) return `${names[i]}：自身`
          if (value === 0) return `<strong>${shortNames[i]}</strong> vs <strong>${shortNames[j]}</strong><br/>无${config.title}`
          return `<strong>${shortNames[i]}</strong> vs <strong>${shortNames[j]}</strong><br/>${config.title}: <span style="color:#1890ff;font-weight:bold">${value}</span> 处<br/><small style="color:#888">点击查看详情</small>`
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
          rotate: isLarge ? 0 : 45,
          interval: 0,
          fontSize: isHuge ? 11 : 12,
          fontWeight: 700,
          color: '#1a1a1a',
          lineHeight: isHuge ? 13 : 14,
          align: isLarge ? 'center' : 'right',
          verticalAlign: isLarge ? 'middle' : 'top',
          margin: isLarge ? 12 : 15,
          hideOverlap: false,
          textShadowColor: 'rgba(255,255,255,0.9)',
          textShadowBlur: 2,
          formatter: (value: string) => wrapTextByChars(value, isHuge ? 3 : isLarge ? 4 : 0),
        },
        position: 'bottom',
      },
      yAxis: {
        type: 'category',
        data: shortNames,
        splitArea: { show: true },
        axisLabel: {
          interval: 0,
          fontSize: isHuge ? 11 : 12,
          fontWeight: 700,
          color: '#1a1a1a',
          textShadowColor: 'rgba(255,255,255,0.9)',
          textShadowBlur: 2,
        },
      },
      visualMap: {
        min: 0,
        max: maxValue || 10,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: 5,
        itemWidth: 15,
        itemHeight: 100,
        inRange: {
          color: config.colorScheme,
        },
        outOfRange: {
          color: '#f5f5f5',
        },
        text: [`${maxValue}`, '0'],
        textStyle: { fontSize: 10 },
      },
      series: [{
        name: config.title,
        type: 'heatmap',
        data: heatmapData,
        label: {
          show: true,
          formatter: (params: any) => {
            const value = params.data[2]
            if (value < 0) return '-'
            if (value === 0) return ''
            if (value >= 1000) return `${(value / 1000).toFixed(1)}k`
            return String(value)
          },
          fontSize: 10,
          color: '#333',
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 1,
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      }],
      _chartHeight: chartHeight,
    }
  }, [sharedErrors, variantType])

  const config = VARIANT_TYPE_CONFIG[variantType]

  return (
    <Card
      title={
        <Space size="middle">
          <span>共同异文热力图</span>
          <Radio.Group
            value={variantType}
            onChange={(e) => onVariantTypeChange(e.target.value)}
            size="small"
            optionType="button"
            buttonStyle="solid"
          >
            <Radio.Button value="combined">全部</Radio.Button>
            <Radio.Button value="error">讹误</Radio.Button>
            <Radio.Button value="variant">异体字</Radio.Button>
            <Radio.Button value="yantuo">衍脱</Radio.Button>
          </Radio.Group>
        </Space>
      }
      size="small"
      bodyStyle={{ padding: '12px' }}
    >
      <div style={{
        padding: '8px 12px',
        marginBottom: 12,
        borderRadius: 4,
        fontSize: 12,
        background: config.background,
        border: `1px solid ${config.border}`,
      }}>
        {config.description}
      </div>
      <ReactECharts
        option={heatmapOption}
        style={{ height: (heatmapOption as any)._chartHeight || 350 }}
        opts={{ renderer: 'canvas' }}
        onEvents={{
          click: onCellClick,
        }}
      />
    </Card>
  )
}
