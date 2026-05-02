/**
 * 异文地图可视化组件
 * 在中国地图上展示版本地理分布与相似度关系
 */
import { useEffect, useMemo, useState } from 'react'
import { Card, Alert, Tag, Space, Typography, Divider, Button, Drawer, Table, Input, InputNumber, Select, message } from 'antd'
import ReactECharts from 'echarts-for-react'
import * as echarts from 'echarts'
import chinaOutline from '../data/china-outline.json'

const { Text } = Typography

interface CanonLocation {
  lat: number
  lng: number
  city: string
  province?: string
  system: string
  period?: string
  year?: number
  description?: string
}

interface VariantMapProps {
  phylogenyData: {
    similarity_matrix: {
      names: string[]
      matrix: number[][]
      systems?: Record<string, string>
    }
    canon_locations?: Record<string, CanonLocation>
  }
  baseName?: string
  projectId?: string | null
}

// 离线环境下提供简化的中国轮廓（用于承载散点分布，不依赖外网地图数据）
echarts.registerMap('china-outline', chinaOutline as any)

const SYSTEM_COLORS: Record<string, string> = {
  '中系': '#faad14',
  '南系': '#52c41a',
  '北系': '#1890ff',
  '近现代藏经': '#722ed1',
  '未知': '#8c8c8c',
}

const SYSTEM_OPTIONS = Object.keys(SYSTEM_COLORS).map((k) => ({ value: k, label: k }))
const API_BASE = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').trim()

type CanonLocationDraft = Partial<CanonLocation> & { system?: string }

export default function VariantMap({ phylogenyData, baseName, projectId }: VariantMapProps) {
  const { similarity_matrix, canon_locations } = phylogenyData
  const names = similarity_matrix.names

  const [canonLocationsLocal, setCanonLocationsLocal] = useState<Record<string, CanonLocation>>(
    () => canon_locations || {}
  )
  const [editorOpen, setEditorOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [draftLocations, setDraftLocations] = useState<Record<string, CanonLocationDraft>>({})

  useEffect(() => {
    setCanonLocationsLocal(canon_locations || {})
  }, [canon_locations])

  useEffect(() => {
    if (editorOpen) return
    setDraftLocations(canonLocationsLocal)
  }, [canonLocationsLocal, editorOpen])

  const updateDraft = (name: string, patch: CanonLocationDraft) => {
    setDraftLocations((prev) => ({
      ...prev,
      [name]: { ...(prev[name] || {}), ...patch },
    }))
  }

  const inferredSystemFor = (name: string) => similarity_matrix.systems?.[name] || '未知'

  const knownCount = Object.keys(canonLocationsLocal || {}).length
  const missingCount = Math.max(0, (names?.length || 0) - knownCount)

  // 找出缺失地理位置的版本
  const missingVersions = useMemo(() => {
    if (!names || !canonLocationsLocal) return []
    return names.filter(name => !canonLocationsLocal[name])
  }, [names, canonLocationsLocal])

  // 准备地图数据
  const mapOption = useMemo(() => {
    if (!canonLocationsLocal || Object.keys(canonLocationsLocal).length === 0) {
      return null
    }

    const matrix = similarity_matrix.matrix
    const base = (baseName && names.includes(baseName)) ? baseName : names[0]

    // 找到底本的索引
    const baseIndex = names.indexOf(base)
    if (baseIndex === -1) return null

    // 获取底本位置
    const baseLocation = canonLocationsLocal[base]

    // 调试输出
    if (!baseLocation) {
      console.warn('底本没有地理位置数据:', base)
    }

    // 准备散点数据（校本）
    const scatterData = names
      .map((name, idx) => {
        if (idx === baseIndex) return null // 跳过底本，底本会单独显示

        const location = canonLocationsLocal[name]
        if (!location) return null

        // 计算与底本的相似度
        const similarity = matrix[idx][baseIndex]

        return {
          name: name,
          value: [location.lng, location.lat, similarity],
          system: location.system,
          city: location.city,
          province: location.province,
          period: location.period,
          year: location.year,
        }
      })
      .filter(Boolean)

    // 计算相似度范围
    const similarities = scatterData.map((d: any) => d.value[2]).filter((v: any) => typeof v === 'number')
    const hasScatter = similarities.length > 0
    const minSim = hasScatter ? Math.min(...similarities) : 0
    const maxSim = hasScatter ? Math.max(...similarities) : 1

    // 简化底本名称显示
    const getShortBaseName = (name: string): string => {
      // 提取【】或《》内的核心名称
      const match = name.match(/【([^】]+)】|《([^》]+)》/)
      if (match) {
        return match[1] || match[2]
      }
      // 去掉括号等内容
      return name.replace(/[（(][^）)]*[）)]/g, '').trim()
    }

    return {
      title: {
        text: '版本地理分布图',
        subtext: base ? `以《${getShortBaseName(base)}》为参照` : '版本地理分布',
        left: 'center',
        textStyle: {
          fontSize: 18,
          fontWeight: 'bold',
        },
        subtextStyle: {
          fontSize: 13,
          color: '#666',
        },
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (params.componentSubType === 'scatter') {
            const data = params.data
            return `
              <div style="padding: 8px;">
                <strong style="font-size: 14px;">${data.name}</strong><br/>
                <div style="margin-top: 6px;">
                  <span style="color: #666;">刻印地：</span>${data.city || '未知'}<br/>
                  ${data.province && data.province !== '海外' ? `<span style="color: #666;">省份：</span>${data.province}<br/>` : ''}
                  ${data.period ? `<span style="color: #666;">朝代：</span>${data.period}<br/>` : ''}
                  ${data.year ? `<span style="color: #666;">年代：</span>${data.year}年<br/>` : ''}
                  <span style="color: #666;">版本系统：</span>
                  <span style="color: ${SYSTEM_COLORS[data.system] || '#000'}; font-weight: bold;">${data.system}</span><br/>
                  <span style="color: #666;">相似度：</span>
                  <span style="color: #1890ff; font-weight: bold; font-size: 16px;">${(data.value[2] * 100).toFixed(1)}%</span>
                </div>
              </div>
            `
          }
          return params.name
        },
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#ddd',
        borderWidth: 1,
        textStyle: {
          color: '#333',
        },
        extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.15);',
      },
      visualMap: {
        show: hasScatter,
        min: minSim,
        max: maxSim,
        calculable: true,
        inRange: {
          color: ['#d32f2f', '#f57c00', '#fbc02d', '#7cb342', '#388e3c'],
          symbolSize: [8, 22],
        },
        text: ['高相似度', '低相似度'],
        textStyle: {
          color: '#333',
          fontSize: 13,
          fontWeight: 500,
        },
        right: '3%',
        top: 'middle',
        orient: 'vertical',
        itemWidth: 24,
        itemHeight: 140,
        padding: [10, 15],
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#ddd',
        borderWidth: 1,
        borderRadius: 6,
        formatter: (value: number) => `${(value * 100).toFixed(0)}%`,
      },
      geo: {
        map: 'china-outline',
        roam: true, // 允许缩放和平移
        // 扩展经纬度范围，确保海外点位（如日本/韩国）也可被绘制与缩放查看
        boundingCoords: [[70, 55], [150, 15]],
        zoom: 1.05,
        center: [120, 35],
        layoutCenter: ['50%', '50%'],
        layoutSize: '100%',
        itemStyle: {
          areaColor: '#f0f5f9',
          borderColor: '#8fb5d4',
          borderWidth: 1,
          shadowColor: 'rgba(0, 0, 0, 0.08)',
          shadowBlur: 10,
        },
        emphasis: {
          itemStyle: {
            areaColor: '#dae8f5',
            borderColor: '#5a8fc4',
            borderWidth: 1.5,
          },
          label: {
            show: true,
            color: '#1a1a1a',
            fontSize: 12,
            fontWeight: 'bold',
          },
        },
        label: {
          show: false,
          color: '#666',
          fontSize: 10,
        },
      },
      series: [
        // 地图底图（部分浏览器/渲染模式下，仅 geo 可能不稳定，叠加一个 map series 确保底图始终可见）
        {
          name: '中国底图',
          type: 'map',
          map: 'china-outline',
          geoIndex: 0,
          silent: true,
          tooltip: { show: false },
          itemStyle: {
            areaColor: '#f0f5f9',
            borderColor: '#8fb5d4',
            borderWidth: 1,
          },
          emphasis: {
            itemStyle: {
              areaColor: '#dae8f5',
              borderColor: '#5a8fc4',
              borderWidth: 1.5,
            },
          },
          z: 0,
        },
        // 校本散点
        {
          name: '版本分布',
          type: 'scatter',
          coordinateSystem: 'geo',
          geoIndex: 0,
          data: scatterData,
          symbolSize: (val: number[]) => {
            // 根据相似度调整圆点大小
            const sim = val[2]
            const size = 8 + sim * 14
            return Math.max(7, Math.min(22, size))
          },
          clip: false,
          itemStyle: {
            shadowBlur: 15,
            shadowColor: 'rgba(0, 0, 0, 0.3)',
            shadowOffsetY: 3,
          },
          label: {
            show: true,
            formatter: (params: any) => {
              // 显示藏经简称
              const name = params.data.name
              // 提取核心名称（去掉括号内容）
              const match = name.match(/[【《]?([^】》【《（）()]+)/)
              return match ? match[1].slice(0, 4) : name.slice(0, 4)
            },
            position: 'top',
            fontSize: 11,
            fontWeight: 500,
            color: '#1a1a1a',
            backgroundColor: 'rgba(255, 255, 255, 0.92)',
            padding: [3, 6],
            borderRadius: 4,
            borderColor: 'rgba(0, 0, 0, 0.1)',
            borderWidth: 1,
            shadowColor: 'rgba(0, 0, 0, 0.12)',
            shadowBlur: 4,
            shadowOffsetY: 2,
          },
          labelLayout: {
            hideOverlap: true,
            moveOverlap: 'shiftY',
            draggable: false,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 20,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
            label: {
              show: true,
              fontSize: 13,
              fontWeight: 'bold',
            },
          },
        },
        // 底本标记（红星图钉）
        ...(baseLocation ? [{
          name: '底本',
          type: 'scatter',
          coordinateSystem: 'geo',
          geoIndex: 0,
          data: [
            {
              name: base,
              value: [baseLocation.lng, baseLocation.lat, 1.0],
              city: baseLocation.city,
              system: baseLocation.system,
            },
          ],
          symbol: 'pin', // 图钉形状
          symbolSize: 55,
          symbolOffset: [0, -20], // 向上偏移，让图钉更明显
          itemStyle: {
            color: '#ff4757',
            borderColor: '#fff',
            borderWidth: 3,
            shadowBlur: 25,
            shadowColor: 'rgba(255, 71, 87, 0.7)',
            shadowOffsetY: 5,
          },
          label: {
            show: true,
            formatter: () => '★ 底本',
            position: 'top',
            distance: 10,
            fontSize: 14,
            fontWeight: 'bold',
            color: '#fff',
            backgroundColor: '#ff4757',
            padding: [6, 12],
            borderRadius: 5,
            borderColor: '#fff',
            borderWidth: 2,
            shadowColor: 'rgba(0, 0, 0, 0.3)',
            shadowBlur: 8,
            shadowOffsetY: 3,
          },
          emphasis: {
            itemStyle: {
              color: '#ff2d3a',
              shadowBlur: 30,
            },
            label: {
              fontSize: 16,
              backgroundColor: '#ff2d3a',
            },
          },
          z: 100, // 确保底本在最上层
        }] : []),
      ].filter(Boolean),
    }
  }, [baseName, canonLocationsLocal, names, similarity_matrix.matrix])

  // 地理聚类分析
  const geoClusteringAnalysis = useMemo(() => {
    if (!canonLocationsLocal) return null
    const matrix = similarity_matrix.matrix

    // 统计各省份的版本数量和平均相似度
    const provinceStats: Record<string, { count: number; avgSim: number; versions: string[] }> = {}

    names.forEach((name, idx) => {
      const loc = canonLocationsLocal[name]
      if (!loc || !loc.province) return

      const province = loc.province
      if (!provinceStats[province]) {
        provinceStats[province] = { count: 0, avgSim: 0, versions: [] }
      }

      provinceStats[province].count++
      provinceStats[province].versions.push(name)

      // 计算该版本与其他版本的平均相似度
      const sims = matrix[idx].filter((_, i) => i !== idx)
      const avgSim = sims.reduce((a, b) => a + b, 0) / sims.length
      provinceStats[province].avgSim += avgSim
    })

    // 计算平均值
    Object.keys(provinceStats).forEach((province) => {
      provinceStats[province].avgSim /= provinceStats[province].count
    })

    return provinceStats
  }, [canonLocationsLocal, names, similarity_matrix.matrix])

  const handleOpenEditor = () => {
    setDraftLocations(canonLocationsLocal || {})
    setEditorOpen(true)
  }

  const handleSaveLocations = async () => {
    if (!projectId) {
      message.warning('请先保存项目后再编辑地理位置信息')
      return
    }

    const payload: Record<string, CanonLocation> = {}
    for (const name of names) {
      const draft = draftLocations[name] || {}
      const lat = typeof draft.lat === 'number' ? draft.lat : undefined
      const lng = typeof draft.lng === 'number' ? draft.lng : undefined
      const city = typeof draft.city === 'string' ? draft.city.trim() : ''
      if (lat == null || lng == null || !city) continue

      payload[name] = {
        lat,
        lng,
        city,
        province: typeof draft.province === 'string' ? draft.province : undefined,
        system: (typeof draft.system === 'string' ? draft.system : inferredSystemFor(name)) || '未知',
        period: typeof draft.period === 'string' ? draft.period : undefined,
        year: typeof draft.year === 'number' ? draft.year : undefined,
        description: typeof draft.description === 'string' ? draft.description : undefined,
      }
    }

    if (Object.keys(payload).length === 0) {
      message.warning('请至少填写一条包含经纬度与城市的信息')
      return
    }

    setSaving(true)
    try {
      const resp = await fetch(`${API_BASE}/api/v1/multi-collation/projects/${projectId}/canon-locations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ locations: payload }),
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err?.detail || '保存失败')
      }
      const data = await resp.json()
      setCanonLocationsLocal(data.canon_locations || {})
      message.success('地理位置信息已保存')
      setEditorOpen(false)
    } catch (e: any) {
      message.error(e?.message ? `保存失败：${e.message}` : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card
      title="版本地理分布图"
      size="small"
      extra={
        <Space size={8}>
          <Tag color="blue">可缩放拖拽</Tag>
          <Button size="small" onClick={handleOpenEditor}>
            编辑位置信息
          </Button>
        </Space>
      }
    >
      {(knownCount === 0 || missingCount > 0) && (
        <Alert
          type={knownCount === 0 ? 'warning' : 'info'}
          message={knownCount === 0 ? '暂无地理位置信息' : '部分版本缺少地理位置信息'}
          description={
            <div>
              <div style={{ marginBottom: 6 }}>
                已匹配 {knownCount}/{names.length} 个版本{missingCount > 0 ? `（缺少 ${missingCount} 个）` : ''}
              </div>
              {missingVersions.length > 0 && (
                <div style={{ marginBottom: 6, padding: '8px', background: '#fff7e6', borderRadius: 4, border: '1px solid #ffd591' }}>
                  <div style={{ fontWeight: 'bold', marginBottom: 4, color: '#d46b08' }}>缺失地理位置的版本：</div>
                  <div style={{ fontSize: 12, color: '#8c8c8c', lineHeight: 1.6 }}>
                    {missingVersions.map((v, i) => (
                      <div key={i}>• {v}</div>
                    ))}
                  </div>
                </div>
              )}
              <div>可点击右上角"编辑位置信息"补充经纬度与城市。</div>
            </div>
          }
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Alert
        type="info"
        message="地理聚类现象"
        description={
          <div>
            <p style={{ marginBottom: 10, lineHeight: 1.6 }}>
              地理位置接近的版本往往相似度更高，反映了文本传播的<strong>地域性特征</strong>。系统可视化展示版本地理分布与相似度关系（含海外藏经）。
            </p>
            <ul style={{ marginBottom: 0, paddingLeft: 20, lineHeight: 1.8 }}>
              <li><strong>圆点大小</strong>：表示与底本的相似度（越大越相似）</li>
              <li><strong>颜色深浅</strong>：橙红色表示低相似度，黄色为中等，绿色表示高相似度</li>
              <li><strong>底本标记</strong>：红色图钉 (★) 标注底本位置，作为对比基准</li>
              <li><strong>智能标签</strong>：自动避让重叠，鼠标悬停查看完整信息</li>
              <li><strong>海外版本</strong>：日本、韩国等海外藏经的经纬度也会在地图上显示</li>
            </ul>
          </div>
        }
        style={{ marginBottom: 16 }}
        showIcon
      />

      {mapOption ? (
        <ReactECharts
          option={mapOption}
          style={{ height: 650 }}
          opts={{ renderer: 'canvas' }}
        />
      ) : (
        <Alert
          type="warning"
          message="暂无可绘制的地图点位"
          description="当前没有任何版本填入经纬度信息。请先补充至少一个版本的经纬度与城市。"
          showIcon
        />
      )}

      {/* 地理聚类分析 */}
      {mapOption && geoClusteringAnalysis && (
        <>
          <Divider orientation="left" style={{ marginTop: 24, marginBottom: 16 }}>
            地理聚类分析
          </Divider>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 16 }}>
            {Object.entries(geoClusteringAnalysis)
              .sort((a, b) => {
                // 将"海外"排到最后
                if (a[0] === '海外') return 1
                if (b[0] === '海外') return -1
                // 其他按版本数量降序
                return b[1].count - a[1].count
              })
              .map(([province, stats]) => (
                <Card
                  key={province}
                  size="small"
                  hoverable
                  style={{
                    borderRadius: 8,
                    background: 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)',
                    border: '1px solid #e8e8e8',
                  }}
                  bodyStyle={{ padding: 16 }}
                >
                  <Space direction="vertical" size={8} style={{ width: '100%' }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: 4,
                    }}>
                      <Text strong style={{ fontSize: 16, color: '#1a1a1a' }}>
                        {province}
                      </Text>
                      <Tag color="processing" style={{ margin: 0 }}>
                        {stats.count} 版本
                      </Tag>
                    </div>
                    <div style={{
                      background: '#f0f5ff',
                      padding: '8px 12px',
                      borderRadius: 6,
                      border: '1px solid #d6e4ff',
                    }}>
                      <div style={{ marginBottom: 4 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>平均相似度</Text>
                      </div>
                      <Text
                        strong
                        style={{
                          fontSize: 20,
                          color: stats.avgSim > 0.9 ? '#52c41a' : stats.avgSim > 0.8 ? '#1890ff' : '#fa8c16',
                        }}
                      >
                        {(stats.avgSim * 100).toFixed(1)}%
                      </Text>
                    </div>
                    <div style={{
                      padding: '6px 0',
                      borderTop: '1px dashed #e8e8e8',
                      marginTop: 4,
                    }}>
                      <div style={{ fontSize: 11, lineHeight: 1.8, color: '#595959' }}>
                        {stats.versions.map((v, idx) => {
                          // 提取藏经核心名称，保留版本区分信息
                          let displayName = v

                          // 提取【】内的系统和版本信息
                          const bracketMatch = v.match(/【([^】]+)】/)
                          if (bracketMatch) {
                            // 例如：【中系●高麗初雕高麗研究所版】→ 高麗初雕高麗研究所版
                            const innerText = bracketMatch[1]
                            const parts = innerText.split('●')
                            if (parts.length > 1) {
                              displayName = parts[1] // 取●后面的部分
                            } else {
                              displayName = innerText
                            }
                          }

                          // 移除《》及其内容（经名）
                          displayName = displayName.replace(/《[^》]*》/g, '').trim()

                          // 限制长度，但要保留足够信息区分不同版本
                          if (displayName.length > 12) {
                            displayName = displayName.slice(0, 12) + '…'
                          }

                          return (
                            <div key={idx} style={{ marginBottom: 2 }}>
                              <Text strong style={{ fontSize: 11 }}>• {displayName}</Text>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </Space>
                </Card>
              ))}
          </div>
        </>
      )}

      <Drawer
        title="编辑版本地理位置信息"
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        width={980}
        extra={
          <Space>
            <Button onClick={() => setEditorOpen(false)}>取消</Button>
            <Button type="primary" loading={saving} onClick={() => void handleSaveLocations()}>
              保存
            </Button>
          </Space>
        }
      >
        <Alert
          type="info"
          showIcon
          message="填写提示"
          description="至少填写“城市 + 经纬度”即可在地图上显示；其余字段用于展示与筛选。"
          style={{ marginBottom: 12 }}
        />

        <Table
          size="small"
          rowKey="name"
          pagination={{ pageSize: 10, showSizeChanger: true, showQuickJumper: true }}
          dataSource={names.map((name) => ({
            name,
            system: draftLocations[name]?.system ?? inferredSystemFor(name),
            city: draftLocations[name]?.city,
            province: draftLocations[name]?.province,
            lat: draftLocations[name]?.lat,
            lng: draftLocations[name]?.lng,
            period: draftLocations[name]?.period,
            year: draftLocations[name]?.year,
          }))}
          columns={[
            {
              title: '版本',
              dataIndex: 'name',
              key: 'name',
              width: 260,
              ellipsis: true,
              render: (t: string) => <Text style={{ fontSize: 12 }}>{t}</Text>,
            },
            {
              title: '系统',
              dataIndex: 'system',
              key: 'system',
              width: 110,
              render: (_: any, r: any) => (
                <Select
                  size="small"
                  value={(draftLocations[r.name]?.system ?? inferredSystemFor(r.name)) || '未知'}
                  options={SYSTEM_OPTIONS}
                  onChange={(v) => updateDraft(r.name, { system: v })}
                  style={{ width: '100%' }}
                />
              ),
            },
            {
              title: '城市',
              dataIndex: 'city',
              key: 'city',
              width: 160,
              render: (_: any, r: any) => (
                <Input
                  size="small"
                  value={draftLocations[r.name]?.city || ''}
                  onChange={(e) => updateDraft(r.name, { city: e.target.value })}
                  placeholder="如：北京"
                />
              ),
            },
            {
              title: '省份',
              dataIndex: 'province',
              key: 'province',
              width: 120,
              render: (_: any, r: any) => (
                <Input
                  size="small"
                  value={draftLocations[r.name]?.province || ''}
                  onChange={(e) => updateDraft(r.name, { province: e.target.value })}
                  placeholder="如：北京/海外"
                />
              ),
            },
            {
              title: '纬度',
              dataIndex: 'lat',
              key: 'lat',
              width: 120,
              render: (_: any, r: any) => (
                <InputNumber
                  size="small"
                  value={draftLocations[r.name]?.lat as any}
                  onChange={(v) => updateDraft(r.name, { lat: typeof v === 'number' ? v : undefined })}
                  style={{ width: '100%' }}
                  placeholder="lat"
                />
              ),
            },
            {
              title: '经度',
              dataIndex: 'lng',
              key: 'lng',
              width: 120,
              render: (_: any, r: any) => (
                <InputNumber
                  size="small"
                  value={draftLocations[r.name]?.lng as any}
                  onChange={(v) => updateDraft(r.name, { lng: typeof v === 'number' ? v : undefined })}
                  style={{ width: '100%' }}
                  placeholder="lng"
                />
              ),
            },
            {
              title: '朝代',
              dataIndex: 'period',
              key: 'period',
              width: 110,
              render: (_: any, r: any) => (
                <Input
                  size="small"
                  value={draftLocations[r.name]?.period || ''}
                  onChange={(e) => updateDraft(r.name, { period: e.target.value })}
                  placeholder="如：北宋"
                />
              ),
            },
            {
              title: '年代',
              dataIndex: 'year',
              key: 'year',
              width: 90,
              render: (_: any, r: any) => (
                <InputNumber
                  size="small"
                  value={draftLocations[r.name]?.year as any}
                  onChange={(v) => updateDraft(r.name, { year: typeof v === 'number' ? v : undefined })}
                  style={{ width: '100%' }}
                  placeholder="year"
                />
              ),
            },
          ]}
          scroll={{ x: 1100 }}
        />
      </Drawer>
    </Card>
  )
}
