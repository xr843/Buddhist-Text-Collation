/**
 * 标点迁移主页面
 *
 * 功能：
 * - 左右双栏布局：来源文本（带标点）| 目标文本/结果
 * - 顶部工具栏：加载示例、清除标点、进行迁移、复制结果
 * - 支持上传/导出 txt 文件
 * - 字数上限5万字
 */
import React, { useState, useRef } from 'react'
import {
  Card,
  Button,
  Space,
  Typography,
  message,
  Spin,
  Tooltip,
} from 'antd'
import {
  SwapOutlined,
  ClearOutlined,
  CopyOutlined,
  FileTextOutlined,
  SyncOutlined,
  UploadOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import TextEditor from './TextEditor'
import { transferPunctuation, removePunctuation, getExample } from './api'
import { MAX_TEXT_LENGTH } from './constants'
import './PunctuationTransfer.css'

const { Title, Text } = Typography

export default function PunctuationTransferPage() {
  // 状态
  const [sourceText, setSourceText] = useState('')
  const [targetText, setTargetText] = useState('')
  const [resultText, setResultText] = useState('')
  const [loading, setLoading] = useState(false)

  // 隐藏的文件输入引用
  const sourceFileInputRef = useRef<HTMLInputElement>(null)
  const targetFileInputRef = useRef<HTMLInputElement>(null)

  // 处理文本变化（带字数限制检查）
  const handleSourceTextChange = (text: string) => {
    if (text.length > MAX_TEXT_LENGTH) {
      message.warning(`来源文本超出字数限制（最多${MAX_TEXT_LENGTH}字）`)
      setSourceText(text.slice(0, MAX_TEXT_LENGTH))
    } else {
      setSourceText(text)
    }
    // 清除之前的结果
    if (resultText) setResultText('')
  }

  const handleTargetTextChange = (text: string) => {
    if (text.length > MAX_TEXT_LENGTH) {
      message.warning(`目标文本超出字数限制（最多${MAX_TEXT_LENGTH}字）`)
      setTargetText(text.slice(0, MAX_TEXT_LENGTH))
    } else {
      setTargetText(text)
    }
    // 清除之前的结果
    if (resultText) setResultText('')
  }

  // 读取txt文件
  const readTextFile = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const text = e.target?.result as string
        resolve(text)
      }
      reader.onerror = () => reject(new Error('文件读取失败'))
      reader.readAsText(file, 'UTF-8')
    })
  }

  // 处理来源文本文件上传
  const handleSourceFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // 验证文件类型
    if (!file.name.endsWith('.txt')) {
      message.error('请上传 txt 格式的文本文件')
      return
    }

    try {
      const text = await readTextFile(file)
      if (text.length > MAX_TEXT_LENGTH) {
        message.warning(`文件内容超出字数限制，已截取前${MAX_TEXT_LENGTH}字`)
        setSourceText(text.slice(0, MAX_TEXT_LENGTH))
      } else {
        setSourceText(text)
        message.success(`已加载来源文本（${text.length}字）`)
      }
      if (resultText) setResultText('')
    } catch (error) {
      console.error('读取文件失败:', error)
      message.error('读取文件失败')
    }

    // 清空input，允许重复选择同一文件
    e.target.value = ''
  }

  // 处理目标文本文件上传
  const handleTargetFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.txt')) {
      message.error('请上传 txt 格式的文本文件')
      return
    }

    try {
      const text = await readTextFile(file)
      if (text.length > MAX_TEXT_LENGTH) {
        message.warning(`文件内容超出字数限制，已截取前${MAX_TEXT_LENGTH}字`)
        setTargetText(text.slice(0, MAX_TEXT_LENGTH))
      } else {
        setTargetText(text)
        message.success(`已加载目标文本（${text.length}字）`)
      }
      if (resultText) setResultText('')
    } catch (error) {
      console.error('读取文件失败:', error)
      message.error('读取文件失败')
    }

    e.target.value = ''
  }

  // 导出结果为txt文件
  const handleExportResult = () => {
    if (!resultText) {
      message.warning('没有可导出的结果')
      return
    }

    const blob = new Blob([resultText], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `标点迁移结果_${new Date().toISOString().slice(0, 10)}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    message.success('结果已导出')
  }

  // 加载示例
  const handleLoadExample = async () => {
    setLoading(true)
    try {
      const example = await getExample()
      setSourceText(example.source)
      setTargetText(example.target)
      setResultText('')
      message.success('示例文本已加载')
    } catch (error) {
      console.error('加载示例失败:', error)
      message.error('加载示例失败')
    } finally {
      setLoading(false)
    }
  }

  // 清除目标文本的标点
  const handleClearPunctuation = async () => {
    if (!targetText.trim()) {
      message.warning('请先输入目标文本')
      return
    }

    setLoading(true)
    try {
      const response = await removePunctuation({ text: targetText })
      setTargetText(response.result_text)
      message.success(`已清除 ${response.removed_count} 个标点符号`)
    } catch (error) {
      console.error('清除标点失败:', error)
      message.error('清除标点失败')
    } finally {
      setLoading(false)
    }
  }

  // 执行标点迁移
  const handleTransfer = async () => {
    if (!sourceText.trim()) {
      message.warning('请输入来源文本（带标点）')
      return
    }
    if (!targetText.trim()) {
      message.warning('请输入目标文本')
      return
    }

    setLoading(true)
    try {
      const response = await transferPunctuation({
        source_text: sourceText,
        target_text: targetText,
        preserve_existing: false,
      })
      setResultText(response.result_text)
      message.success('标点迁移完成')
    } catch (error) {
      console.error('标点迁移失败:', error)
      message.error('标点迁移失败')
    } finally {
      setLoading(false)
    }
  }

  // 复制结果
  const handleCopyResult = async () => {
    if (!resultText) {
      message.warning('没有可复制的结果')
      return
    }

    try {
      await navigator.clipboard.writeText(resultText)
      message.success('已复制到剪贴板')
    } catch (error) {
      console.error('复制失败:', error)
      message.error('复制失败，请手动复制')
    }
  }

  // 清空所有
  const handleClearAll = () => {
    setSourceText('')
    setTargetText('')
    setResultText('')
  }

  // 格式化字数显示
  const formatCharCount = (count: number) => {
    if (count >= 10000) {
      const wan = count / 10000
      // 整数万不显示小数点
      return wan === Math.floor(wan) ? `${wan}万` : `${wan.toFixed(1)}万`
    }
    return count.toString()
  }

  return (
    <div className="container">
      {/* 隐藏的文件输入 */}
      <input
        type="file"
        ref={sourceFileInputRef}
        onChange={handleSourceFileChange}
        accept=".txt"
        style={{ display: 'none' }}
      />
      <input
        type="file"
        ref={targetFileInputRef}
        onChange={handleTargetFileChange}
        accept=".txt"
        style={{ display: 'none' }}
      />

      {/* 页面标题 */}
      <div className="header">
        <Space>
          <SwapOutlined style={{ fontSize: 24 }} />
          <Title level={3} style={{ margin: 0 }}>
            标点迁移
          </Title>
        </Space>
        <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
          将已标点文本的标点符号迁移至另一份无标点的相似文本中（单次上限{formatCharCount(MAX_TEXT_LENGTH)}字）
        </Text>
      </div>

      {/* 工具栏 */}
      <Card className="toolbar" size="small">
        <Space wrap>
          <Button
            icon={<FileTextOutlined />}
            onClick={handleLoadExample}
            loading={loading}
          >
            加载示例
          </Button>
          <Button
            icon={<ClearOutlined />}
            onClick={handleClearPunctuation}
            loading={loading}
            disabled={!targetText.trim()}
          >
            清除标点
          </Button>
          <Button
            type="primary"
            icon={<SyncOutlined />}
            onClick={handleTransfer}
            loading={loading}
            disabled={!sourceText.trim() || !targetText.trim()}
          >
            进行迁移
          </Button>
          <Tooltip title="复制迁移结果">
            <Button
              icon={<CopyOutlined />}
              onClick={handleCopyResult}
              disabled={!resultText}
            >
              复制结果
            </Button>
          </Tooltip>
          <Tooltip title="导出为txt文件">
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExportResult}
              disabled={!resultText}
            >
              导出结果
            </Button>
          </Tooltip>
          <Button onClick={handleClearAll}>清空全部</Button>
        </Space>
      </Card>

      <Spin spinning={loading}>
        {/* 双栏编辑区 */}
        <div className="content-layout">
          {/* 左侧：来源文本 */}
          <Card
            className="text-column"
            title={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>来源文本（带标点）</span>
                <Space size="small">
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {formatCharCount(sourceText.length)} / {formatCharCount(MAX_TEXT_LENGTH)}字
                  </Text>
                  <Tooltip title="上传txt文件">
                    <Button
                      type="text"
                      size="small"
                      icon={<UploadOutlined />}
                      onClick={() => sourceFileInputRef.current?.click()}
                    />
                  </Tooltip>
                </Space>
              </div>
            }
            size="small"
          >
            <TextEditor
              title=""
              value={sourceText}
              onChange={handleSourceTextChange}
              placeholder="请输入带标点的来源文本，或点击右上角上传txt文件..."
              showCharCount={false}
            />
          </Card>

          {/* 右侧：目标文本/结果 */}
          <Card
            className="text-column"
            title={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>{resultText ? '迁移结果' : '目标文本（无标点）'}</span>
                <Space size="small">
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {formatCharCount(resultText ? resultText.length : targetText.length)} / {formatCharCount(MAX_TEXT_LENGTH)}字
                  </Text>
                  <Tooltip title={resultText ? "上传新的目标文本" : "上传txt文件"}>
                    <Button
                      type="text"
                      size="small"
                      icon={<UploadOutlined />}
                      onClick={() => targetFileInputRef.current?.click()}
                    />
                  </Tooltip>
                </Space>
              </div>
            }
            size="small"
          >
            {resultText ? (
              <TextEditor
                title=""
                value={resultText}
                readOnly
                placeholder=""
                showCharCount={false}
              />
            ) : (
              <TextEditor
                title=""
                value={targetText}
                onChange={handleTargetTextChange}
                placeholder="请输入无标点的目标文本，或点击右上角上传txt文件..."
                showCharCount={false}
              />
            )}
          </Card>
        </div>
      </Spin>
    </div>
  )
}
