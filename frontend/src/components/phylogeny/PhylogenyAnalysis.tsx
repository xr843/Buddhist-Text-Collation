/**
 * 版本谱系分析组件 - 专业级展示
 * 包含：热力图、谱系树、共同讹误分析、版本系统标注
 */
import { useState, useMemo } from 'react'
import { Row, Col, Tabs, Alert, Badge, Empty } from 'antd'
import {
  ApartmentOutlined,
  HeatMapOutlined,
  WarningOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import VariantMap from '../VariantMap'

import SimilarityHeatmap from './SimilarityHeatmap'
import SimilarityTable from './SimilarityTable'
import SharedErrorHeatmap from './SharedErrorHeatmap'
import PhylogenyTree, { SystemInfoCard } from './PhylogenyTree'
import ErrorDetailsTable, { VersionTotalTable } from './ErrorDetailsTable'
import { mergeVariantDetails, getTotalByVersionForType } from './utils'
import type { PhylogenyAnalysisProps, VariantType } from './types'

export default function PhylogenyAnalysis({ data, baseName, projectId }: PhylogenyAnalysisProps) {
  const [activeTab, setActiveTab] = useState('heatmap')
  const [selectedErrorPair, setSelectedErrorPair] = useState<string | null>(null)
  const [variantType, setVariantType] = useState<VariantType>('combined')

  const { similarity_matrix, shared_errors, tree, conclusions } = data

  // 处理共同异文热力图点击
  const handleSharedErrorClick = (params: any) => {
    if (!shared_errors) return
    const i = params.data[1]
    const j = params.data[0]
    if (i === j || params.data[2] === 0) return

    const names = shared_errors.names
    const key = `${names[i]}|${names[j]}`
    const altKey = `${names[j]}|${names[i]}`

    const details = mergeVariantDetails(shared_errors, variantType)
    if (details?.[key]) {
      setSelectedErrorPair(key)
    } else if (details?.[altKey]) {
      setSelectedErrorPair(altKey)
    }
  }

  // 获取选中的共同异文详情
  const selectedErrorDetails = useMemo(() => {
    if (!selectedErrorPair || !shared_errors) return null
    const details = mergeVariantDetails(shared_errors, variantType)
    return details?.[selectedErrorPair] || null
  }, [selectedErrorPair, shared_errors, variantType])

  // 获取当前类型的总数统计
  const currentTotalByVersion = useMemo(() => {
    if (!shared_errors) return {}
    return getTotalByVersionForType(shared_errors, variantType)
  }, [shared_errors, variantType])

  return (
    <div>
      {conclusions && conclusions.length > 0 && (
        <Alert
          type="info"
          icon={<BulbOutlined />}
          message="版本谱系分析结论"
          description={
            <ul style={{ margin: '8px 0 0 0', paddingLeft: 20 }}>
              {conclusions.map((c, i) => (
                <li key={i} style={{ marginBottom: 4 }}>{c}</li>
              ))}
            </ul>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'heatmap',
            label: (
              <span>
                <HeatMapOutlined /> 相似度矩阵
              </span>
            ),
            children: (
              <Row gutter={16}>
                <Col xs={24} lg={similarity_matrix.names.length > 10 ? 16 : 14}>
                  <SimilarityHeatmap similarityMatrix={similarity_matrix} />
                </Col>
                <Col xs={24} lg={similarity_matrix.names.length > 10 ? 8 : 10}>
                  <SimilarityTable similarityMatrix={similarity_matrix} />
                </Col>
              </Row>
            ),
          },
          {
            key: 'tree',
            label: (
              <span>
                <ApartmentOutlined /> 谱系树
              </span>
            ),
            children: (
              <Row gutter={16}>
                <Col span={12}>
                  <PhylogenyTree tree={tree} systems={similarity_matrix.systems} />
                </Col>
                <Col span={12}>
                  <SystemInfoCard systems={similarity_matrix.systems} />
                </Col>
              </Row>
            ),
          },
          {
            key: 'shared_errors',
            label: (
              <span>
                <WarningOutlined /> 共同异文
                {shared_errors && (
                  <Badge
                    count={
                      Object.keys(shared_errors.details || {}).length +
                      Object.keys(shared_errors.variant_details || {}).length +
                      Object.keys(shared_errors.yantuo_details || {}).length
                    }
                    style={{ marginLeft: 8 }}
                    size="small"
                  />
                )}
              </span>
            ),
            children: shared_errors ? (
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={14}>
                  <SharedErrorHeatmap
                    sharedErrors={shared_errors}
                    variantType={variantType}
                    onVariantTypeChange={(type) => {
                      setVariantType(type)
                      setSelectedErrorPair(null)
                    }}
                    onCellClick={handleSharedErrorClick}
                  />
                </Col>
                <Col xs={24} lg={10}>
                  <ErrorDetailsTable
                    selectedPair={selectedErrorPair}
                    details={selectedErrorDetails}
                    variantType={variantType}
                  />
                  <VersionTotalTable
                    totalByVersion={currentTotalByVersion}
                    variantType={variantType}
                  />
                </Col>
              </Row>
            ) : (
              <Empty description="暂无共同异文数据" />
            ),
          },
          {
            key: 'geo_map',
            label: (
              <span>
                <HeatMapOutlined /> 地理分布图
              </span>
            ),
            children: (
              <VariantMap
                phylogenyData={data}
                baseName={(baseName && similarity_matrix.names.includes(baseName)) ? baseName : similarity_matrix.names[0]}
                projectId={projectId}
              />
            ),
          },
        ]}
      />
    </div>
  )
}
