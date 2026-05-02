/**
 * 谱系树组件
 */
import { useMemo, useState } from 'react'
import { Card, Tree, Tag, Space, Typography, Alert, Button, Collapse } from 'antd'
import { SYSTEM_COLORS } from './constants'
import type { PhylogenyNode } from './types'

const { Text, Paragraph } = Typography
const { Panel } = Collapse

interface PhylogenyTreeProps {
  tree: PhylogenyNode
  systems?: Record<string, string>
}

export default function PhylogenyTree({ tree, systems }: PhylogenyTreeProps) {
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([])
  const [autoExpandParent, setAutoExpandParent] = useState(false)

  // 转换为 Tree 组件需要的格式
  const treeData = useMemo(() => {
    const convertNode = (node: PhylogenyNode): any => {
      const system = node.system || systems?.[node.name]
      const systemColor = SYSTEM_COLORS[system || '未知'] || SYSTEM_COLORS['未知']

      return {
        title: (
          <Space size={4}>
            {node.is_group ? (
              <Text italic style={{ color: '#666' }}>{node.name}</Text>
            ) : (
              <>
                <Text strong>{node.name}</Text>
                {node.similarity !== undefined && (
                  <Tag
                    color={node.similarity > 90 ? 'green' : node.similarity > 80 ? 'blue' : 'orange'}
                    style={{ fontSize: 11, marginLeft: 4 }}
                  >
                    {node.similarity.toFixed(1)}%
                  </Tag>
                )}
                {system && system !== '未知' && (
                  <Tag color={systemColor} style={{ fontSize: 10, marginLeft: 2 }}>
                    {system}
                  </Tag>
                )}
              </>
            )}
          </Space>
        ),
        key: node.name,
        children: node.children?.map(convertNode),
      }
    }

    return [convertNode(tree)]
  }, [tree, systems])

  // 获取所有树节点的keys
  const allTreeKeys = useMemo(() => {
    const keys: React.Key[] = []
    const collectKeys = (nodes: any[]) => {
      nodes.forEach(node => {
        keys.push(node.key)
        if (node.children) {
          collectKeys(node.children)
        }
      })
    }
    collectKeys(treeData)
    return keys
  }, [treeData])

  const handleExpandAll = () => {
    setExpandedKeys(allTreeKeys)
    setAutoExpandParent(true)
  }

  const handleCollapseAll = () => {
    setExpandedKeys([])
    setAutoExpandParent(false)
  }

  return (
    <Card
      title="UPGMA 层次聚类谱系树"
      size="small"
      extra={
        <Space size="small">
          <Button size="small" onClick={handleExpandAll}>展开全部</Button>
          <Button size="small" onClick={handleCollapseAll}>折叠全部</Button>
        </Space>
      }
    >
      <Alert
        type="info"
        message="使用 UPGMA 算法基于相似度矩阵生成"
        style={{ marginBottom: 12, fontSize: 12 }}
      />
      <div style={{
        maxHeight: '600px',
        overflowY: 'auto',
        overflowX: 'hidden',
        padding: 16,
        background: '#fafafa',
        borderRadius: 8,
        border: '1px solid #e8e8e8'
      }}>
        <Tree
          showLine={{ showLeafIcon: false }}
          expandedKeys={expandedKeys}
          autoExpandParent={autoExpandParent}
          onExpand={(keys) => {
            setExpandedKeys(keys)
            setAutoExpandParent(false)
          }}
          treeData={treeData}
        />
      </div>
    </Card>
  )
}

interface SystemInfoCardProps {
  systems?: Record<string, string>
}

export function SystemInfoCard({ systems }: SystemInfoCardProps) {
  return (
    <Card title="版本系统归属（团队标准）" size="small">
      <Paragraph type="secondary" style={{ marginBottom: 12 }}>
        基于团队标准自动识别版本谱系归属（中系/南系/北系）
      </Paragraph>
      {systems && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {Object.entries(systems).map(([name, system]) => (
            <Tag
              key={name}
              color={SYSTEM_COLORS[system] || SYSTEM_COLORS['未知']}
              style={{ marginBottom: 4 }}
            >
              {name}: {system}
            </Tag>
          ))}
        </div>
      )}

      <Collapse ghost style={{ marginTop: 16 }}>
        <Panel header="版本系统说明（团队标准）" key="1">
          <Paragraph type="secondary" style={{ fontSize: 12, marginBottom: 12 }}>
            汉文刻本大藏经三大系统分类（团队标准）
          </Paragraph>
          <ul style={{ paddingLeft: 20, margin: 0, fontSize: 12, color: '#666', lineHeight: 2 }}>
            <li>
              <Tag color={SYSTEM_COLORS['中系']}>中系</Tag>
              <strong>祖本：《开宝藏》</strong>（北宋971-983，益州）
              <br />
              <span style={{ marginLeft: 60 }}>高丽藏（初雕/再雕）、赵城金藏、大正藏、中华藏、缩刻藏</span>
            </li>
            <li style={{ marginTop: 8 }}>
              <Tag color={SYSTEM_COLORS['南系']}>南系</Tag>
              <strong>起源：两宋福建/江浙民间募刻</strong>
              <br />
              <span style={{ marginLeft: 60 }}>
                福州系：崇宁藏、毗卢藏<br />
                <span style={{ marginLeft: 60 }}>湖州系：思溪藏（圆觉藏/资福藏）</span><br />
                <span style={{ marginLeft: 60 }}>苏杭系：碛砂藏、普宁藏</span><br />
                <span style={{ marginLeft: 60 }}>明清：洪武南藏、永乐南/北藏、嘉兴藏、龙藏、频伽藏、卍续藏</span>
              </span>
            </li>
            <li style={{ marginTop: 8 }}>
              <Tag color={SYSTEM_COLORS['北系']}>北系</Tag>
              <strong>核心：《契丹藏》</strong>（辽1031-1064）
              <br />
              <span style={{ marginLeft: 60 }}>房山石经（辽刻部分）</span>
            </li>
            <li style={{ marginTop: 8 }}>
              <Tag color={SYSTEM_COLORS['近现代藏经']}>近现代藏经</Tag>
              CBETA等
            </li>
          </ul>
          <Paragraph type="secondary" style={{ fontSize: 11, marginTop: 12, fontStyle: 'italic' }}>
            注：《高丽再雕藏》集中系、北系之长；《大正藏》归入中系
          </Paragraph>
        </Panel>
      </Collapse>
    </Card>
  )
}
