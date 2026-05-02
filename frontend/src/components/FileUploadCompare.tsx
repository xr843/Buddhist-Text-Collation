/**
 * 文件上传组件
 * 支持：
 * 1. 分别上传两个文件
 * 2. 直接文本输入
 */
import { useState } from 'react'
import { Upload, Card, Button, Typography, Space, Alert, message, Input, Segmented, Tooltip } from 'antd'
import {
  InboxOutlined,
  FileTextOutlined,
  EditOutlined,
  SwapOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import type { UploadProps } from 'antd'

const { Text } = Typography
const { TextArea } = Input

type InputMode = 'file' | 'text'

interface FileInfo {
  file: File | null
  fileName: string
  charCount: number
  preview: string
  versionName: string
}

interface TextInfo {
  content: string
  versionName: string
}

interface FileUploadCompareProps {
  onCompare: (file1: File, file2: File, version1Name: string, version2Name: string) => void
  loading?: boolean
}

export default function FileUploadCompare({ onCompare, loading = false }: FileUploadCompareProps) {
  // 输入模式
  const [inputMode, setInputMode] = useState<InputMode>('file')

  // 文件上传模式的状态
  const [file1Info, setFile1Info] = useState<FileInfo>({
    file: null,
    fileName: '',
    charCount: 0,
    preview: '',
    versionName: '版本A',
  })

  const [file2Info, setFile2Info] = useState<FileInfo>({
    file: null,
    fileName: '',
    charCount: 0,
    preview: '',
    versionName: '版本B',
  })

  // 文本输入模式的状态
  const [text1Info, setText1Info] = useState<TextInfo>({
    content: '',
    versionName: '版本A',
  })

  const [text2Info, setText2Info] = useState<TextInfo>({
    content: '',
    versionName: '版本B',
  })

  // 读取文件内容（用于预览和字符统计）
  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()

      reader.onload = (e) => {
        const content = e.target?.result as string
        resolve(content)
      }

      reader.onerror = () => {
        reject(new Error('文件读取失败'))
      }

      // 如果是txt文件，直接读取文本
      if (file.name.endsWith('.txt')) {
        reader.readAsText(file, 'utf-8')
      } else if (file.name.endsWith('.docx')) {
        // docx文件无法在前端直接预览，仅显示文件名
        resolve('[docx文件，上传后查看内容]')
      } else {
        reject(new Error('不支持的文件格式'))
      }
    })
  }

  // 处理单个文件
  const processFile = async (file: File, slot: 'file1' | 'file2') => {
    const isValidType = file.name.endsWith('.txt') || file.name.endsWith('.docx')
    if (!isValidType) {
      message.error(`${file.name}: 仅支持 .txt 和 .docx 文件`)
      return false
    }

    const isLt10M = file.size / 1024 / 1024 < 10
    if (!isLt10M) {
      message.error(`${file.name}: 文件大小不能超过 10MB`)
      return false
    }

    try {
      const content = await readFileContent(file)
      const charCount = file.name.endsWith('.txt') ? content.length : 0
      const preview = file.name.endsWith('.txt') ? content.slice(0, 500) : content
      const fileNameWithoutExt = file.name.replace(/\.(txt|docx)$/, '')

      const fileInfo: FileInfo = {
        file,
        fileName: file.name,
        charCount,
        preview,
        versionName: fileNameWithoutExt,
      }

      if (slot === 'file1') {
        setFile1Info(fileInfo)
      } else {
        setFile2Info(fileInfo)
      }

      return true
    } catch (error) {
      message.error(`${file.name}: 文件读取失败`)
      return false
    }
  }

  // 将文本内容转换为 File 对象
  const textToFile = (content: string, fileName: string): File => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    return new File([blob], fileName, { type: 'text/plain' })
  }

  // 文件上传配置（版本1）- 用于单独上传
  const uploadProps1: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.txt,.docx',
    showUploadList: false,
    beforeUpload: async (file) => {
      await processFile(file, 'file1')
      return false
    },
  }

  // 文件上传配置（版本2）- 用于单独上传
  const uploadProps2: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.txt,.docx',
    showUploadList: false,
    beforeUpload: async (file) => {
      await processFile(file, 'file2')
      return false
    },
  }

  // 清除文件
  const clearFile1 = () => {
    setFile1Info({
      file: null,
      fileName: '',
      charCount: 0,
      preview: '',
      versionName: '版本A',
    })
  }

  const clearFile2 = () => {
    setFile2Info({
      file: null,
      fileName: '',
      charCount: 0,
      preview: '',
      versionName: '版本B',
    })
  }

  // 交换两个文件
  const swapFiles = () => {
    const temp = file1Info
    setFile1Info(file2Info)
    setFile2Info(temp)
    message.info('已交换版本A和版本B')
  }

  // 开始对比
  const handleCompare = () => {
    if (inputMode === 'file') {
      if (!file1Info.file || !file2Info.file) {
        message.warning('请上传两个文件')
        return
      }
      onCompare(file1Info.file, file2Info.file, file1Info.versionName, file2Info.versionName)
    } else {
      if (!text1Info.content.trim() || !text2Info.content.trim()) {
        message.warning('请输入两个版本的文本')
        return
      }
      const file1 = textToFile(text1Info.content, `${text1Info.versionName}.txt`)
      const file2 = textToFile(text2Info.content, `${text2Info.versionName}.txt`)
      onCompare(file1, file2, text1Info.versionName, text2Info.versionName)
    }
  }

  // 检查是否可以开始对比
  const canCompare = inputMode === 'file'
    ? (file1Info.file && file2Info.file)
    : (text1Info.content.trim() && text2Info.content.trim())

  // 渲染文件卡片
  const renderFileCard = (
    info: FileInfo,
    label: string,
    onClear: () => void,
    uploadProps: UploadProps,
    color: string
  ) => {
    if (info.file) {
      // 已有文件
      return (
        <div style={{ flex: 1, minWidth: 0 }}>
          <Card
            size="small"
            style={{
              border: `2px solid ${color}`,
              borderRadius: 8,
              height: '100%',
            }}
            title={
              <span style={{ color }}>{label}</span>
            }
            extra={
              <Tooltip title="移除文件">
                <Button
                  type="text"
                  danger
                  size="small"
                  icon={<DeleteOutlined />}
                  onClick={onClear}
                />
              </Tooltip>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <div>
                <Text type="secondary">文件：</Text>
                <Text strong>{info.fileName}</Text>
              </div>
              {info.charCount > 0 && (
                <div>
                  <Text type="secondary">字数：</Text>
                  <Text>{info.charCount.toLocaleString()} 字</Text>
                </div>
              )}
              {info.preview && info.preview !== '[docx文件，上传后查看内容]' && (
                <div
                  style={{
                    marginTop: 8,
                    padding: 8,
                    background: '#f5f5f5',
                    borderRadius: 4,
                    maxHeight: 100,
                    overflow: 'auto',
                    fontSize: 12,
                    lineHeight: 1.6,
                    color: '#666',
                  }}
                >
                  {info.preview.slice(0, 200)}
                  {info.preview.length > 200 && '...'}
                </div>
              )}
            </Space>
          </Card>
        </div>
      )
    }

    // 无文件：显示上传区域
    return (
      <div style={{ flex: 1, minWidth: 0 }}>
        <Upload.Dragger
          {...uploadProps}
          style={{
            border: `2px dashed ${color}`,
            borderRadius: 8,
            background: '#fafafa',
          }}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined style={{ color }} />
          </p>
          <p className="ant-upload-text" style={{ color }}>{label}</p>
          <p className="ant-upload-hint">点击或拖拽上传</p>
        </Upload.Dragger>
      </div>
    )
  }

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 输入模式切换 */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <Segmented
            value={inputMode}
            onChange={(value) => setInputMode(value as InputMode)}
            options={[
              { label: <span><FileTextOutlined /> 文件上传</span>, value: 'file' },
              { label: <span><EditOutlined /> 文本输入</span>, value: 'text' },
            ]}
            size="large"
          />
        </div>

        {inputMode === 'file' ? (
          /* 文件上传模式 */
          <div>
            {/* 分别上传区域 */}
            <div style={{ display: 'flex', gap: 16, alignItems: 'stretch' }}>
              {renderFileCard(file1Info, '版本A（底本）', clearFile1, uploadProps1, '#1890ff')}

              {/* 中间交换按钮 */}
              {(file1Info.file || file2Info.file) && (
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <Tooltip title="交换版本A和版本B">
                    <Button
                      type="default"
                      shape="circle"
                      icon={<SwapOutlined />}
                      onClick={swapFiles}
                      disabled={!file1Info.file || !file2Info.file}
                    />
                  </Tooltip>
                </div>
              )}

              {renderFileCard(file2Info, '版本B（校本）', clearFile2, uploadProps2, '#52c41a')}
            </div>

            {/* 提示信息 */}
            <Alert
              message="使用提示"
              description={
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  <li>分别点击或拖拽文件到对应的版本框</li>
                  <li>支持格式：.txt、.docx | 单个文件最大 10MB</li>
                </ul>
              }
              type="info"
              showIcon
              style={{ marginTop: 16 }}
            />
          </div>
        ) : (
          /* 文本输入模式 */
          <div style={{ display: 'flex', gap: '16px' }}>
            {/* 版本A文本输入 */}
            <Card
              title={
                <span style={{ color: '#1890ff' }}>版本A（底本）</span>
              }
              style={{ flex: 1, border: '2px solid #1890ff' }}
              extra={
                text1Info.content && (
                  <Text type="secondary">{text1Info.content.length.toLocaleString()} 字</Text>
                )
              }
            >
              <TextArea
                value={text1Info.content}
                onChange={(e) => setText1Info({ ...text1Info, content: e.target.value })}
                placeholder="请输入或粘贴版本A（底本）的文本内容..."
                autoSize={{ minRows: 10, maxRows: 16 }}
                style={{ fontSize: 14, lineHeight: 1.8 }}
              />
            </Card>

            {/* 版本B文本输入 */}
            <Card
              title={
                <span style={{ color: '#52c41a' }}>版本B（校本）</span>
              }
              style={{ flex: 1, border: '2px solid #52c41a' }}
              extra={
                text2Info.content && (
                  <Text type="secondary">{text2Info.content.length.toLocaleString()} 字</Text>
                )
              }
            >
              <TextArea
                value={text2Info.content}
                onChange={(e) => setText2Info({ ...text2Info, content: e.target.value })}
                placeholder="请输入或粘贴版本B（校本）的文本内容..."
                autoSize={{ minRows: 10, maxRows: 16 }}
                style={{ fontSize: 14, lineHeight: 1.8 }}
              />
            </Card>
          </div>
        )}

        {/* 开始对比按钮 */}
        <div style={{ textAlign: 'center' }}>
          <Button
            type="primary"
            size="large"
            onClick={handleCompare}
            disabled={!canCompare}
            loading={loading}
            icon={<SwapOutlined />}
            style={{ minWidth: 200, height: 48, fontSize: 16 }}
          >
            开始对比分析
          </Button>
        </div>
      </Space>
    </div>
  )
}
