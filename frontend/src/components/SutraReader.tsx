/**
 * 经文阅读器组件
 * 类似CBETA官网的阅读体验
 */
import { useState, useEffect, useMemo, useCallback, Fragment } from 'react'
import {
  Card,
  Space,
  Button,
  Slider,
  Switch,
  Tooltip,
  Spin,
  Typography,
  Dropdown,
  Input,
  message,
  Divider,
  Tag,
  Popover,
} from 'antd'
import {
  FontSizeOutlined,
  BgColorsOutlined,
  FileTextOutlined,
  DownloadOutlined,
  LeftOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'

const { Text } = Typography
const { Search } = Input

interface Collation {
  position: number
  lemma?: string
  readings?: Array<{ wit?: string; text?: string; type?: string }>
  original?: string
  variants?: string[]
  note?: string
}

interface SutraData {
  id: string
  title: string
  text: string
  collations?: Collation[]
  metadata?: {
    dynasty?: string
    translator?: string
    author?: string
    byline?: string
    juan?: number
    category?: string
  }
}

interface SutraReaderProps {
  sutraId: string
  onBack?: () => void
  initialData?: SutraData | null
}

// 护眼色配置
const eyeProtectionColors = [
  { label: '默认白', value: '#ffffff', textColor: '#000000' },
  { label: '护眼绿', value: '#C7EDCC', textColor: '#333333' },
  { label: '羊皮纸', value: '#FAF9DE', textColor: '#333333' },
  { label: '淡黄', value: '#FFF2E2', textColor: '#333333' },
  { label: '浅灰', value: '#EAEAEA', textColor: '#333333' },
]

// CBETA风格的文本解析器
// 参考CBETA官网实际排版（基于截图分析）：
// - 经名标题：#91278f（紫红色）
// - 作者/译者：蓝色，右对齐
// - 章节品名：#008080（青色/蓝绿色），带下划线
// - 正文：蓝色，正常换行显示
interface ParsedBlock {
  type: 'byline' | 'section' | 'paragraph'
  content: string
  level?: number
}

// 判断一行是否是作者/译者信息
function isByline(line: string): boolean {
  const trimmed = line.trim()
  if (!trimmed || trimmed.length > 30 || trimmed.includes('。')) return false

  // 彌勒菩薩說、XX尊者造、XX法師譯 等
  if (trimmed.match(/(菩薩|尊者|比丘|沙門|居士).*(說|造|集|撰|述)$/)) {
    return true
  }
  // 三藏法師XX奉詔譯、XX譯 等
  if (trimmed.match(/(三藏|法師|大師).*(譯|詔譯|奉.*譯)/) ||
      trimmed.match(/^.{2,20}(奉\s*詔\s*譯|譯)$/)) {
    return true
  }
  return false
}

// 判断一行是否是章节标题
function isSectionTitle(line: string): { isSection: boolean; level: number } {
  const trimmed = line.trim()

  // 排除条件：
  // 1. 空行
  // 2. 太长（超过25字）
  // 3. 包含句号（。）- 说明是正文
  // 4. 包含逗号（，）- 说明是正文
  // 5. 包含冒号后有内容（：XX）- 说明是正文
  if (!trimmed ||
      trimmed.length > 25 ||
      trimmed.includes('。') ||
      trimmed.includes('，') ||
      trimmed.includes('、') ||
      /：.+/.test(trimmed)) {
    return { isSection: false, level: 0 }
  }

  // 章节标题必须是独立的标题格式
  // 分別界品第一、本地分中五識身相應地第一、XX品第X 等
  // 必须以"第X"结尾，或者以"品/分/地/章/節/卷"结尾
  if (trimmed.match(/第[一二三四五六七八九十百千]+$/) ||
      trimmed.match(/(品|分|地|章|節|卷)第[一二三四五六七八九十]+$/) ||
      trimmed.match(/(品|分|地|章|節|卷)$/) ||
      trimmed.match(/^[一二三四五六七八九十]+[、.．]\s*\S+$/)) {
    const isMainTitle = trimmed.includes('論') || trimmed.includes('經') || trimmed.includes('律')
    return { isSection: true, level: isMainTitle ? 1 : 2 }
  }

  return { isSection: false, level: 0 }
}

// 解析CBETA风格的文本结构
// CBETA官网特点：按原始数据中的空行分段，如果没有空行则按特定规则分段
function parseCBETAText(text: string): ParsedBlock[] {
  const blocks: ParsedBlock[] = []
  const lines = text.split('\n')

  let i = 0
  let paragraphBuffer = ''
  let hasAnyEmptyLine = false

  // 首先检查是否有空行
  for (const line of lines) {
    if (!line.trim()) {
      hasAnyEmptyLine = true
      break
    }
  }

  const flushParagraph = () => {
    if (paragraphBuffer) {
      blocks.push({ type: 'paragraph', content: paragraphBuffer })
      paragraphBuffer = ''
    }
  }

  while (i < lines.length) {
    const line = lines[i]
    const trimmedLine = line.trim()

    // 空行 - 作为段落分隔
    if (!trimmedLine) {
      flushParagraph()
      i++
      continue
    }

    // 1. 检查是否是作者/译者信息（byline）
    if (isByline(trimmedLine)) {
      flushParagraph()
      blocks.push({ type: 'byline', content: trimmedLine })
      i++
      continue
    }

    // 2. 检查是否是章节标题
    const sectionInfo = isSectionTitle(trimmedLine)
    if (sectionInfo.isSection) {
      flushParagraph()
      blocks.push({
        type: 'section',
        content: trimmedLine,
        level: sectionInfo.level
      })
      i++
      continue
    }

    // 3. 普通正文 - 合并到当前段落
    paragraphBuffer += trimmedLine

    // 如果原始数据没有空行，则按行分段（每行作为一个段落）
    if (!hasAnyEmptyLine) {
      flushParagraph()
    }

    i++
  }

  // 输出剩余的段落
  flushParagraph()

  return blocks
}

export default function SutraReader({ sutraId, onBack, initialData }: SutraReaderProps) {
  const [loading, setLoading] = useState(!initialData)
  const [sutraData, setSutraData] = useState<SutraData | null>(initialData || null)
  const [fontSize, setFontSize] = useState(18)
  const [lineHeight, setLineHeight] = useState(2)
  const [bgColorIndex, setBgColorIndex] = useState(0)
  const [showCollations, setShowCollations] = useState(true)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [isFullscreen, setIsFullscreen] = useState(false)

  const bgColor = eyeProtectionColors[bgColorIndex]

  // 获取经文数据
  useEffect(() => {
    if (initialData) {
      setSutraData(initialData)
      setLoading(false)
      return
    }

    const fetchSutra = async () => {
      setLoading(true)
      try {
        const response = await fetch(`/api/v1/cbeta/fetch/${sutraId}?strip_punctuation=false`)
        const data = await response.json()

        if (data.success) {
          setSutraData({
            id: sutraId,
            ...data.sutra,
          })
        } else {
          message.error(data.detail || '获取经文失败')
        }
      } catch (error) {
        message.error(`获取经文失败: ${error}`)
      } finally {
        setLoading(false)
      }
    }

    fetchSutra()
  }, [sutraId, initialData])

  // 处理校勘记位置映射
  const collationMap = useMemo(() => {
    if (!sutraData?.text || !sutraData.collations) return new Map<number, { collation: Collation; index: number }>()

    const rawText = sutraData.text
    const leadingMatch = rawText.match(/^[\s\n\r]+/)
    const offset = leadingMatch ? leadingMatch[0].length : 0

    const map = new Map<number, { collation: Collation; index: number }>()
    sutraData.collations
      .filter(col => col && typeof col.position === 'number' && (col.original || col.lemma))
      .forEach((col, idx) => {
        const adjustedPos = col.position - offset
        if (adjustedPos >= 0) {
          map.set(adjustedPos, { collation: col, index: idx + 1 })
        }
      })

    return map
  }, [sutraData])

  // 搜索高亮
  const highlightSearch = useCallback((text: string): React.ReactNode => {
    if (!searchKeyword.trim()) return text

    const regex = new RegExp(`(${searchKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    const parts = text.split(regex)

    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark key={i} style={{ backgroundColor: '#ffeb3b', padding: '0 2px' }}>
          {part}
        </mark>
      ) : (
        part
      )
    )
  }, [searchKeyword])

  // 渲染校勘记弹出内容
  const renderCollationPopover = (collation: Collation, index: number) => {
    const originalText = collation.original || collation.lemma || '-'
    let variantsList: string[] = collation.variants || []

    if (collation.readings && collation.readings.length > 0) {
      variantsList = collation.readings
        .filter((r) => r.text || r.wit)
        .map((r) => `${r.text || '（缺）'}${r.wit || ''}`)
    }

    return (
      <div style={{ maxWidth: 400 }}>
        <div style={{ marginBottom: 8 }}>
          <Tag color="blue">校勘 {index}</Tag>
        </div>
        <div style={{ marginBottom: 8 }}>
          <Text strong>底本：</Text>
          <Text>「{originalText}」</Text>
        </div>
        {variantsList.length > 0 && (
          <div style={{ marginBottom: 8 }}>
            <Text strong>異文：</Text>
            <div style={{ marginTop: 4, paddingLeft: 8, borderLeft: '2px solid #1890ff' }}>
              {variantsList.map((v, i) => (
                <div key={i} style={{ marginBottom: 2 }}><Text>{v}</Text></div>
              ))}
            </div>
          </div>
        )}
        {collation.note && (
          <div>
            <Text strong>校注：</Text>
            <Text type="secondary">{collation.note}</Text>
          </div>
        )}
      </div>
    )
  }

  // 渲染带校勘记标记的文本
  const renderTextWithCollations = (text: string, globalOffset: number) => {
    if (!showCollations || collationMap.size === 0) {
      return highlightSearch(text)
    }

    const result: React.ReactNode[] = []
    let lastIndex = 0

    for (let i = 0; i < text.length; i++) {
      const globalPos = globalOffset + i
      const colInfo = collationMap.get(globalPos)

      if (colInfo) {
        if (i > lastIndex) {
          result.push(
            <Fragment key={`text-${lastIndex}`}>
              {highlightSearch(text.slice(lastIndex, i))}
            </Fragment>
          )
        }

        const lemmaText = colInfo.collation.original || colInfo.collation.lemma || ''

        result.push(
          <Popover
            key={`col-${globalPos}`}
            content={renderCollationPopover(colInfo.collation, colInfo.index)}
            title="校勘记"
            trigger="hover"
            placement="top"
          >
            <span style={{ borderBottom: '2px dashed #1890ff', cursor: 'pointer' }}>
              {highlightSearch(lemmaText)}
              <sup style={{ color: '#1890ff', fontSize: '0.7em' }}>[{colInfo.index}]</sup>
            </span>
          </Popover>
        )

        lastIndex = i + lemmaText.length
        i = lastIndex - 1
      }
    }

    if (lastIndex < text.length) {
      result.push(
        <Fragment key={`text-end`}>
          {highlightSearch(text.slice(lastIndex))}
        </Fragment>
      )
    }

    return result.length > 0 ? result : highlightSearch(text)
  }

  // 渲染CBETA风格的内容块
  // CBETA官网颜色参考（基于截图分析）：
  // - 经名标题：#91278f（紫红色）
  // - 作者/译者：蓝色，右对齐
  // - 章节品名：#008080（青色/蓝绿色），带下划线
  // - 正文：蓝色，正常换行
  const renderBlock = (block: ParsedBlock, index: number, _blocks: ParsedBlock[], globalOffset: number) => {
    const baseStyle = {
      fontFamily: '"Noto Serif SC", "Source Han Serif SC", "SimSun", serif',
      fontSize,
      lineHeight,
      color: bgColor.textColor,
    }

    switch (block.type) {
      case 'byline':
        // 作者/译者信息 - 右对齐，蓝色
        return (
          <div
            key={index}
            style={{
              ...baseStyle,
              textAlign: 'right',
              color: '#0000bb',
              marginBottom: '0.5em',
            }}
          >
            {renderTextWithCollations(block.content, globalOffset)}
          </div>
        )

      case 'section':
        // 章节标题 - 青色，带下划线（与CBETA官网一致）
        return (
          <div
            key={index}
            style={{
              marginTop: '1em',
              marginBottom: '0.5em',
            }}
          >
            <span
              style={{
                ...baseStyle,
                color: '#008080',
                borderBottom: '1px dashed #008080',
                paddingBottom: '2px',
              }}
            >
              {renderTextWithCollations(block.content, globalOffset)}
            </span>
          </div>
        )

      case 'paragraph':
      default:
        // 正文段落 - 黑色，段落间有间距
        return (
          <p
            key={index}
            style={{
              ...baseStyle,
              color: '#000000',
              textAlign: 'justify',
              marginTop: 0,
              marginBottom: '1em',
              textIndent: 0,
            }}
          >
            {renderTextWithCollations(block.content, globalOffset)}
          </p>
        )
    }
  }

  // 解析并渲染经文内容
  const renderContent = () => {
    if (!sutraData?.text) return null

    const text = sutraData.text.trimStart()
    const blocks = parseCBETAText(text)

    let globalOffset = 0

    return blocks.map((block, index) => {
      const rendered = renderBlock(block, index, blocks, globalOffset)
      globalOffset += block.content.length + 1 // +1 for newline
      return rendered
    })
  }

  // 导出菜单
  const exportMenuItems = [
    {
      key: 'punct_notes',
      label: '含标点、校勘记',
      onClick: () => window.open(`/api/v1/cbeta/export/txt/${sutraId}?variant=punct_notes`, '_blank'),
    },
    {
      key: 'punct',
      label: '含标点',
      onClick: () => window.open(`/api/v1/cbeta/export/txt/${sutraId}?variant=punct`, '_blank'),
    },
    {
      key: 'plain',
      label: '纯文本',
      onClick: () => window.open(`/api/v1/cbeta/export/txt/${sutraId}?variant=plain`, '_blank'),
    },
  ]

  // 背景色菜单
  const bgColorMenuItems = eyeProtectionColors.map((color, index) => ({
    key: index.toString(),
    label: (
      <Space>
        <div
          style={{
            width: 16,
            height: 16,
            backgroundColor: color.value,
            border: '1px solid #d9d9d9',
            borderRadius: 2,
          }}
        />
        {color.label}
      </Space>
    ),
    onClick: () => setBgColorIndex(index),
  }))

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text type="secondary">正在从 CBETA 获取经文数据...</Text>
        </div>
      </div>
    )
  }

  if (!sutraData) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Text type="secondary">未找到经文</Text>
          {onBack && (
            <div style={{ marginTop: 16 }}>
              <Button icon={<LeftOutlined />} onClick={onBack}>返回</Button>
            </div>
          )}
        </div>
      </Card>
    )
  }

  const containerStyle: React.CSSProperties = isFullscreen
    ? {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 1000,
        backgroundColor: bgColor.value,
        overflow: 'auto',
      }
    : {}

  const validCollationCount = (sutraData.collations || []).filter(
    col => col && typeof col.position === 'number' && (col.original || col.lemma)
  ).length

  return (
    <div style={containerStyle}>
      <Card
        style={{ backgroundColor: bgColor.value, minHeight: isFullscreen ? '100vh' : 'auto' }}
        styles={{ body: { padding: isFullscreen ? '24px 48px' : '24px' } }}
      >
        {/* 顶部信息栏 */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            marginBottom: 16,
            paddingBottom: 12,
            borderBottom: '1px solid #e8e8e8',
          }}
        >
          {onBack && (
            <Button icon={<LeftOutlined />} onClick={onBack}>返回</Button>
          )}
          <Tag color="blue">{sutraId}</Tag>
          <span style={{ color: '#666', fontSize: 14 }}>
            No. {sutraId.replace(/[^\d]/g, '').slice(0, 4)}
          </span>
        </div>

        {/* 工具栏 */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            marginBottom: 16,
            flexWrap: 'wrap',
            gap: 8,
          }}
        >
          <Search
            placeholder="搜索经文"
            allowClear
            onSearch={setSearchKeyword}
            onChange={(e) => !e.target.value && setSearchKeyword('')}
            style={{ width: 160 }}
            size="small"
          />
          <Divider type="vertical" />

          <Tooltip title="字体大小">
            <Space size={4}>
              <FontSizeOutlined style={{ color: bgColor.textColor }} />
              <Slider min={14} max={28} value={fontSize} onChange={setFontSize} style={{ width: 80 }} />
            </Space>
          </Tooltip>

          <Tooltip title="行高">
            <Space size={4}>
              <FileTextOutlined style={{ color: bgColor.textColor }} />
              <Slider min={1.5} max={3} step={0.1} value={lineHeight} onChange={setLineHeight} style={{ width: 60 }} />
            </Space>
          </Tooltip>

          <Divider type="vertical" />

          <Dropdown menu={{ items: bgColorMenuItems }} trigger={['click']}>
            <Button size="small" icon={<BgColorsOutlined />}>{bgColor.label}</Button>
          </Dropdown>

          <Tooltip title="显示校勘记">
            <Switch
              checked={showCollations}
              onChange={setShowCollations}
              checkedChildren="校勘"
              unCheckedChildren="校勘"
              size="small"
            />
          </Tooltip>

          <Divider type="vertical" />

          <Dropdown menu={{ items: exportMenuItems }} trigger={['click']}>
            <Button size="small" icon={<DownloadOutlined />}>导出</Button>
          </Dropdown>

          <Tooltip title={isFullscreen ? '退出全屏' : '全屏阅读'}>
            <Button
              size="small"
              icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
              onClick={() => setIsFullscreen(!isFullscreen)}
            />
          </Tooltip>
        </div>

        {/* 经文标题 - 紫红色，类似CBETA官网 */}
        <div
          style={{
            color: '#91278f',
            fontSize: fontSize * 1.2,
            fontWeight: 500,
            fontFamily: '"Noto Serif SC", "Source Han Serif SC", serif',
            marginBottom: '1em',
          }}
        >
          {sutraData.title}
        </div>

        {/* 校勘记说明 */}
        {showCollations && validCollationCount > 0 && (
          <div style={{ marginBottom: 12 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              <InfoCircleOutlined style={{ marginRight: 4 }} />
              共 {validCollationCount} 处校勘记，鼠标悬停
              <span
                style={{
                  borderBottom: '2px dashed #1890ff',
                  padding: '0 4px',
                  margin: '0 4px',
                }}
              >
                蓝色标记
              </span>
              查看详情
            </Text>
          </div>
        )}

        {/* 经文内容 */}
        <div style={{
          padding: '8px 16px',
          maxWidth: '100%',
          lineHeight: lineHeight,
        }}>
          {renderContent()}
        </div>

        {/* 统计信息 */}
        <Divider />
        <div style={{ textAlign: 'center' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            共 {sutraData.text?.length || 0} 字
            {validCollationCount > 0 && <> | {validCollationCount} 处校勘</>}
            {' | '}数据来源：CBETA 中华电子佛典协会
          </Text>
        </div>
      </Card>
    </div>
  )
}
