/**
 * 校勘判取对话框组件
 * 基于陈垣"四校法"（对校、本校、他校、理校）框架
 */
import { useState, useEffect, useRef } from 'react'
import {
  Modal,
  Form,
  Radio,
  Checkbox,
  Input,
  Space,
  Typography,
  Divider,
  Tag,
  Alert,
  Collapse,
  Row,
  Col,
  Tooltip,
  List,
  Button,
  Spin,
} from 'antd'
import {
  QuestionCircleOutlined,
  EditOutlined,
  DragOutlined,
  BookOutlined,
} from '@ant-design/icons'
import Draggable from 'react-draggable'
import type { DraggableData, DraggableEvent } from 'react-draggable'

const { Text } = Typography
const { TextArea } = Input
const { Panel } = Collapse

// 四校法依据选项
const DUIJIAO_OPTIONS = [
  { value: 'majority', label: '多数版本一致' },
  { value: 'early_version', label: '版本年代较早' },
  { value: 'authority', label: '版本权威性高' },
  { value: 'system_reliable', label: '版本系统可靠（中系/南系/北系）' },
  { value: 'sanskrit_tibetan', label: '梵/藏本可参' },
]

const BENJIAO_OPTIONS = [
  { value: 'context_consistent', label: '同经前后文一致' },
  { value: 'style_match', label: '符合本经体例' },
  { value: 'chapter_echo', label: '与同经其他章节呼应' },
  { value: 'structure_consistent', label: '科判结构一致' },
  { value: 'dharma_term_consistent', label: '法相术语一致' },
]

const TAJIAO_OPTIONS = [
  { value: 'other_sutra', label: '他经引用一致' },
  { value: 'commentary', label: '注疏引文一致' },
  { value: 'related_text', label: '相关典籍佐证' },
  { value: 'parallel_translation', label: '同本异译一致' },
]

const LIJIAO_OPTIONS = [
  { value: 'meaning_better', label: '义理更通顺' },
  { value: 'shape_similar', label: '形近而讹（字形相近致误）' },
  { value: 'sound_similar', label: '音近而讹（字音相近致误）' },
  { value: 'buddhist_term', label: '符合佛教术语习惯' },
  { value: 'grammar', label: '符合语法规则' },
  { value: 'dharma_definition', label: '符合法相定义' },
  { value: 'doctrinal_position', label: '符合宗义立场' },
  { value: 'sanskrit_reconstruction', label: '梵文还原合理' },
]

// 判取结果接口
export interface CollationDecision {
  position: number              // 异文位置
  selectedVersion: string       // 采用的版本
  selectedText: string          // 采用的文字
  customText?: string           // 自定义文字（当选择"自定义"时）
  duijiao: string[]             // 对校依据
  benjiao: string[]             // 本校依据
  tajiao: string[]              // 他校依据
  lijiao: string[]              // 理校依据
  note: string                  // 详细说明
  uncertain: boolean            // 是否存疑
  createdAt: string             // 判取时间
  updatedAt: string             // 修改时间
}

// 异文项接口
export interface VariantItem {
  position: number
  context: string
  base_char: string
  coll_values: string[]
  category: string
}

interface CollationDecisionModalProps {
  visible: boolean
  onCancel: () => void
  onConfirm: (decision: CollationDecision) => void
  variantItem: VariantItem | null
  collationNames: string[]
  baseName: string
  existingDecision?: CollationDecision | null
  projectId?: string  // 新增：项目ID（用于调用注疏API）
}

export default function CollationDecisionModal({
  visible,
  onCancel,
  onConfirm,
  variantItem,
  collationNames,
  baseName,
  existingDecision,
  projectId,  // 新增
}: CollationDecisionModalProps) {
  const [form] = Form.useForm()
  const [selectedVersion, setSelectedVersion] = useState<string>('')
  const [showCustomInput, setShowCustomInput] = useState(false)

  // 注疏匹配结果状态
  const [commentaryMatches, setCommentaryMatches] = useState<any[]>([])
  const [loadingMatches, setLoadingMatches] = useState(false)

  // 拖动相关状态
  const [disabled, setDisabled] = useState(true)
  const [bounds, setBounds] = useState({ left: 0, top: 0, bottom: 0, right: 0 })
  const draggleRef = useRef<HTMLDivElement>(null!)

  const onStart = (_event: DraggableEvent, uiData: DraggableData) => {
    const { clientWidth, clientHeight } = window.document.documentElement
    const targetRect = draggleRef.current?.getBoundingClientRect()
    if (!targetRect) return
    setBounds({
      left: -targetRect.left + uiData.x,
      right: clientWidth - (targetRect.right - uiData.x),
      top: -targetRect.top + uiData.y,
      bottom: clientHeight - (targetRect.bottom - uiData.y),
    })
  }

  // 构建异文分组（按用字分组）
  const buildVariantGroups = () => {
    if (!variantItem) return []

    const groups: Map<string, string[]> = new Map()

    // 添加底本
    const baseChar = variantItem.base_char
    if (!groups.has(baseChar)) {
      groups.set(baseChar, [])
    }
    groups.get(baseChar)!.push(baseName)

    // 添加各校本
    collationNames.forEach((name, idx) => {
      const char = variantItem.coll_values[idx]
      if (!groups.has(char)) {
        groups.set(char, [])
      }
      groups.get(char)!.push(name)
    })

    // 转换为数组并按版本数量排序（多数在前）
    return Array.from(groups.entries())
      .map(([char, versions]) => ({ char, versions, count: versions.length }))
      .sort((a, b) => b.count - a.count)
  }

  // 初始化表单
  useEffect(() => {
    if (visible && variantItem) {
      if (existingDecision) {
        // 编辑已有判取
        form.setFieldsValue({
          selectedVersion: existingDecision.selectedVersion,
          customText: existingDecision.customText,
          duijiao: existingDecision.duijiao,
          benjiao: existingDecision.benjiao,
          tajiao: existingDecision.tajiao,
          lijiao: existingDecision.lijiao,
          note: existingDecision.note,
          uncertain: existingDecision.uncertain,
        })
        setSelectedVersion(existingDecision.selectedVersion)
        setShowCustomInput(existingDecision.selectedVersion === 'custom')
      } else {
        // 新建判取，默认选择底本
        form.resetFields()
        form.setFieldsValue({
          selectedVersion: baseName,
          duijiao: [],
          benjiao: [],
          tajiao: [],
          lijiao: [],
          note: '',
          uncertain: false,
        })
        setSelectedVersion(baseName)
        setShowCustomInput(false)
      }
    }
  }, [visible, variantItem, existingDecision, baseName, form])

  // 加载注疏匹配结果
  useEffect(() => {
    const fetchCommentaryMatches = async () => {
      if (!visible || !variantItem || !projectId) {
        setCommentaryMatches([])
        return
      }

      setLoadingMatches(true)
      try {
        const API_BASE = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').trim()
        const response = await fetch(
          `${API_BASE}/api/v1/multi-collation/projects/${projectId}/commentary/position/${variantItem.position}?window_size=10&threshold=0.75`
        )

        if (!response.ok) {
          console.error('获取注疏匹配失败')
          setCommentaryMatches([])
          return
        }

        const data = await response.json()
        setCommentaryMatches(data.matches || [])
      } catch (error) {
        console.error('加载注疏匹配失败:', error)
        setCommentaryMatches([])
      } finally {
        setLoadingMatches(false)
      }
    }

    fetchCommentaryMatches()
  }, [visible, variantItem, projectId])

  // 处理版本选择变化
  const handleVersionChange = (e: any) => {
    const value = e.target.value
    setSelectedVersion(value)
    setShowCustomInput(value === 'custom')
  }

  // 采用注疏引证
  const adoptCommentaryMatch = (match: any) => {
    // 自动勾选"注疏引文一致"
    const currentTajiao = form.getFieldValue('tajiao') || []
    if (!currentTajiao.includes('commentary')) {
      form.setFieldsValue({
        tajiao: [...currentTajiao, 'commentary']
      })
    }

    // 在详细说明中追加引文信息
    const currentNote = form.getFieldValue('note') || ''
    const citationInfo = `【注疏引证】（相似度${(match.similarity * 100).toFixed(0)}%）\n来源：${match.commentary_title || '注疏'}\n标记词：${match.marker}\n引文：${match.text || match.commentary_text}\n上下文：${match.context}`
    form.setFieldsValue({
      note: currentNote ? currentNote + '\n\n' + citationInfo : citationInfo
    })
  }

  // 获取选中版本的文字
  const getSelectedText = (): string => {
    if (!variantItem) return ''

    if (selectedVersion === baseName) {
      return variantItem.base_char
    } else if (selectedVersion === 'custom') {
      return form.getFieldValue('customText') || ''
    } else {
      const idx = collationNames.indexOf(selectedVersion)
      if (idx >= 0 && idx < variantItem.coll_values.length) {
        return variantItem.coll_values[idx]
      }
    }
    return ''
  }

  // 提交判取
  const handleSubmit = () => {
    form.validateFields().then((values) => {
      const now = new Date().toISOString()
      const decision: CollationDecision = {
        position: variantItem!.position,
        selectedVersion: values.selectedVersion,
        selectedText: values.selectedVersion === 'custom'
          ? values.customText
          : getSelectedText(),
        customText: values.selectedVersion === 'custom' ? values.customText : undefined,
        duijiao: values.duijiao || [],
        benjiao: values.benjiao || [],
        tajiao: values.tajiao || [],
        lijiao: values.lijiao || [],
        note: values.note || '',
        uncertain: values.uncertain || false,
        createdAt: existingDecision?.createdAt || now,
        updatedAt: now,
      }
      onConfirm(decision)
    })
  }

  if (!variantItem) return null

  const variantGroups = buildVariantGroups()

  return (
    <Modal
      title={
        <div
          style={{ width: '100%', cursor: 'move' }}
          onMouseOver={() => disabled && setDisabled(false)}
          onMouseOut={() => setDisabled(true)}
        >
          <Space>
            <EditOutlined />
            <span>校勘判取</span>
            <Tag color="blue">位置 {variantItem.position}</Tag>
            <Tooltip title="拖动标题栏可移动窗口">
              <DragOutlined style={{ color: '#999', fontSize: 12 }} />
            </Tooltip>
          </Space>
        </div>
      }
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      okText="确认判取"
      cancelText="取消"
      width={700}
      destroyOnClose
      modalRender={(modal) => (
        <Draggable
          disabled={disabled}
          bounds={bounds}
          nodeRef={draggleRef}
          onStart={(event, uiData) => onStart(event, uiData)}
        >
          <div ref={draggleRef}>{modal}</div>
        </Draggable>
      )}
    >
      {/* 异文信息展示 */}
      <Alert
        type="info"
        showIcon={false}
        message={
          <div>
            <Text strong>上下文：</Text>
            <Text code style={{ fontSize: 14, marginLeft: 8 }}>
              {variantItem.context}
            </Text>
          </div>
        }
        style={{ marginBottom: 16 }}
      />

      <Form form={form} layout="vertical">
        {/* 采用版本选择（按用字分组） */}
        <Form.Item
          name="selectedVersion"
          label={
            <Space>
              <Text strong>选择采用版本</Text>
              <Text type="secondary" style={{ fontSize: 12, fontWeight: 'normal' }}>
                （按用字分组，多数在前）
              </Text>
            </Space>
          }
          rules={[{ required: true, message: '请选择采用的版本' }]}
        >
          <Radio.Group onChange={handleVersionChange} style={{ width: '100%' }}>
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              {/* 按用字分组展示 */}
              {variantGroups.map((group, groupIdx) => (
                <div
                  key={group.char}
                  style={{
                    background: groupIdx === 0 ? '#e6f7ff' : '#fffbe6',
                    border: groupIdx === 0 ? '1px solid #91d5ff' : '1px solid #ffe58f',
                    borderRadius: 6,
                    padding: '8px 12px',
                  }}
                >
                  {/* 分组标题 */}
                  <div style={{ marginBottom: 6, display: 'flex', alignItems: 'center' }}>
                    <Tag
                      color={groupIdx === 0 ? 'blue' : 'orange'}
                      style={{ fontSize: 15, padding: '1px 10px', marginRight: 8 }}
                    >
                      {group.char}
                    </Tag>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {group.count} 个版本
                      {groupIdx === 0 && group.count > 1 && (
                        <Text type="success" style={{ marginLeft: 4, fontSize: 11 }}>
                          （多数）
                        </Text>
                      )}
                    </Text>
                  </div>
                  {/* 该分组下的版本选项 */}
                  <div style={{ paddingLeft: 4 }}>
                    <Space direction="vertical" size={2}>
                      {group.versions.map((ver) => (
                        <Radio key={ver} value={ver} style={{ fontSize: 13 }}>
                          {ver}
                          {ver === baseName && (
                            <Tag color="processing" style={{ marginLeft: 6, fontSize: 11 }}>
                              底本
                            </Tag>
                          )}
                        </Radio>
                      ))}
                    </Space>
                  </div>
                </div>
              ))}
              {/* 自定义选项 */}
              <div
                style={{
                  background: '#f9f0ff',
                  border: '1px dashed #d3adf7',
                  borderRadius: 6,
                  padding: '8px 12px',
                }}
              >
                <Radio value="custom">自定义文字</Radio>
              </div>
            </Space>
          </Radio.Group>
        </Form.Item>

        {/* 自定义文字输入 */}
        {showCustomInput && (
          <Form.Item
            name="customText"
            label="自定义文字"
            rules={[{ required: true, message: '请输入自定义文字' }]}
          >
            <Input placeholder="输入校勘者认为正确的文字" style={{ width: 200 }} />
          </Form.Item>
        )}

        <Divider style={{ margin: '16px 0' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>判取依据（四校法）</Text>
        </Divider>

        {/* 四校法依据 */}
        <Collapse
          defaultActiveKey={['duijiao', 'benjiao', 'tajiao', 'lijiao']}
          ghost
          style={{ background: '#fff' }}
        >
          {/* 对校 */}
          <Panel
            header={
              <Space>
                <Tag color="blue">对校</Tag>
                <Text type="secondary">版本对勘</Text>
              </Space>
            }
            key="duijiao"
          >
            <Form.Item name="duijiao" style={{ marginBottom: 0 }}>
              <Checkbox.Group>
                <Row>
                  {DUIJIAO_OPTIONS.map((opt) => (
                    <Col span={12} key={opt.value}>
                      <Checkbox value={opt.value}>{opt.label}</Checkbox>
                    </Col>
                  ))}
                </Row>
              </Checkbox.Group>
            </Form.Item>
          </Panel>

          {/* 本校 */}
          <Panel
            header={
              <Space>
                <Tag color="green">本校</Tag>
                <Text type="secondary">书内自校</Text>
              </Space>
            }
            key="benjiao"
          >
            <Form.Item name="benjiao" style={{ marginBottom: 0 }}>
              <Checkbox.Group>
                <Row>
                  {BENJIAO_OPTIONS.map((opt) => (
                    <Col span={12} key={opt.value}>
                      <Checkbox value={opt.value}>{opt.label}</Checkbox>
                    </Col>
                  ))}
                </Row>
              </Checkbox.Group>
            </Form.Item>
          </Panel>

          {/* 他校 */}
          <Panel
            header={
              <Space>
                <Tag color="purple">他校</Tag>
                <Text type="secondary">他书互证</Text>
              </Space>
            }
            key="tajiao"
          >
            <Form.Item name="tajiao" style={{ marginBottom: 0 }}>
              <Checkbox.Group>
                <Row>
                  {TAJIAO_OPTIONS.map((opt) => (
                    <Col span={12} key={opt.value}>
                      <Checkbox value={opt.value}>{opt.label}</Checkbox>
                    </Col>
                  ))}
                </Row>
              </Checkbox.Group>
            </Form.Item>

            {/* 注疏匹配结果 */}
            {commentaryMatches.length > 0 && (
              <Collapse
                ghost
                defaultActiveKey={['commentary']}
                style={{
                  marginTop: 12,
                  background: '#f6ffed',
                  border: '1px solid #b7eb8f',
                  borderRadius: 6,
                  padding: 8,
                }}
              >
                <Collapse.Panel
                  header={
                    <Space>
                      <BookOutlined style={{ color: '#52c41a' }} />
                      <Text strong style={{ color: '#52c41a' }}>
                        注疏引证匹配（{commentaryMatches.length} 条）
                      </Text>
                    </Space>
                  }
                  key="commentary"
                >
                  <List
                    size="small"
                    dataSource={commentaryMatches}
                    renderItem={(match: any) => (
                      <List.Item
                        style={{
                          background: '#fff',
                          padding: '8px 12px',
                          marginBottom: 8,
                          borderRadius: 6,
                        }}
                      >
                        <div style={{ width: '100%' }}>
                          <div style={{ marginBottom: 4 }}>
                            <Tag
                              color={
                                match.confidence === 'high'
                                  ? 'green'
                                  : match.confidence === 'medium'
                                  ? 'blue'
                                  : 'orange'
                              }
                            >
                              相似度 {(match.similarity * 100).toFixed(0)}%
                            </Tag>
                            <Tag>{match.marker}</Tag>
                            {match.commentary_title && (
                              <Tag color="purple">{match.commentary_title}</Tag>
                            )}
                          </div>
                          <Text
                            style={{
                              fontFamily: "'Noto Serif SC', 'Source Han Serif SC', serif",
                              fontSize: 14,
                              lineHeight: 1.8,
                              display: 'block',
                              marginTop: 4,
                            }}
                          >
                            {match.text || match.commentary_text}
                          </Text>
                          <div style={{ marginTop: 4 }}>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              上下文：{match.context}
                            </Text>
                          </div>
                          <div style={{ marginTop: 8 }}>
                            <Button
                              size="small"
                              type="primary"
                              onClick={() => adoptCommentaryMatch(match)}
                            >
                              采用此条引证
                            </Button>
                          </div>
                        </div>
                      </List.Item>
                    )}
                  />
                </Collapse.Panel>
              </Collapse>
            )}

            {/* 加载中提示 */}
            {loadingMatches && (
              <div style={{ marginTop: 12, textAlign: 'center' }}>
                <Spin size="small" />
                <Text type="secondary" style={{ marginLeft: 8 }}>正在匹配注疏引文...</Text>
              </div>
            )}
          </Panel>

          {/* 理校 */}
          <Panel
            header={
              <Space>
                <Tag color="orange">理校</Tag>
                <Text type="secondary">依理推断</Text>
              </Space>
            }
            key="lijiao"
          >
            <Form.Item name="lijiao" style={{ marginBottom: 0 }}>
              <Checkbox.Group>
                <Row>
                  {LIJIAO_OPTIONS.map((opt) => (
                    <Col span={12} key={opt.value}>
                      <Checkbox value={opt.value}>{opt.label}</Checkbox>
                    </Col>
                  ))}
                </Row>
              </Checkbox.Group>
            </Form.Item>
          </Panel>
        </Collapse>

        {/* 详细说明 */}
        <Form.Item
          name="note"
          label={<Text strong>详细说明</Text>}
          style={{ marginTop: 16 }}
        >
          <TextArea
            rows={3}
            placeholder="可填写更详细的判取理由、参考文献等..."
            maxLength={500}
            showCount
          />
        </Form.Item>

        {/* 存疑标记 */}
        <Form.Item name="uncertain" valuePropName="checked">
          <Checkbox>
            <Space>
              <QuestionCircleOutlined style={{ color: '#ff4d4f' }} />
              <span>存疑待考（暂不确定，留待进一步研究）</span>
            </Space>
          </Checkbox>
        </Form.Item>
      </Form>
    </Modal>
  )
}

// 导出依据选项常量，供其他组件使用
export const DECISION_OPTIONS = {
  duijiao: DUIJIAO_OPTIONS,
  benjiao: BENJIAO_OPTIONS,
  tajiao: TAJIAO_OPTIONS,
  lijiao: LIJIAO_OPTIONS,
}

// 获取依据标签的辅助函数
export function getDecisionLabel(type: string, value: string): string {
  const options = DECISION_OPTIONS[type as keyof typeof DECISION_OPTIONS]
  const opt = options?.find((o) => o.value === value)
  return opt?.label || value
}
