/**
 * 古籍 OCR 识别页
 *
 * 单张图片 → 调后端代理（古籍酷 /ocr_pro）→ 可编辑识别结果 →
 * 复制 / 下载 .txt / 一键送入版本对勘。
 */
import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Upload,
  Button,
  Input,
  Space,
  Card,
  Row,
  Col,
  message,
  Alert,
  Dropdown,
  Typography,
} from 'antd'
import type { UploadFile, MenuProps } from 'antd'
import {
  InboxOutlined,
  ScanOutlined,
  CopyOutlined,
  DownloadOutlined,
  SendOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { ocrApi } from '../services/api'

const { Dragger } = Upload
const { TextArea } = Input
const { Text } = Typography

interface Stats {
  charNumber?: number | null
  lineNumber?: number | null
}

export default function OcrRecognition() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const [enabled, setEnabled] = useState<boolean | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string>('')
  const [recognizing, setRecognizing] = useState(false)
  const [text, setText] = useState('')
  const [stats, setStats] = useState<Stats>({})

  // 进页面先探测 OCR 是否已配置
  useEffect(() => {
    ocrApi
      .status()
      .then((r) => setEnabled(r.enabled))
      .catch(() => setEnabled(false))
  }, [])

  // 释放预览 URL
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  const onSelectFile = useCallback(
    (f: File) => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
      setFile(f)
      setPreviewUrl(URL.createObjectURL(f))
      setText('')
      setStats({})
    },
    [previewUrl]
  )

  const handleRecognize = useCallback(async () => {
    if (!file) return
    setRecognizing(true)
    try {
      const result = await ocrApi.recognize(file)
      setText(result.text || '')
      setStats({ charNumber: result.char_number, lineNumber: result.line_number })
      if (!result.text) {
        message.warning(t('ocr.emptyResult'))
      } else {
        message.success(t('ocr.recognizeSuccess'))
      }
    } catch (e) {
      message.error((e as Error).message || t('ocr.recognizeFailed'))
    } finally {
      setRecognizing(false)
    }
  }, [file, t])

  const baseName = useCallback(() => {
    const raw = file?.name?.replace(/\.[^.]+$/, '').trim()
    return raw || t('ocr.defaultName')
  }, [file, t])

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text)
      message.success(t('ocr.copied'))
    } catch {
      message.error(t('ocr.copyFailed'))
    }
  }, [text, t])

  const handleDownload = useCallback(() => {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${baseName()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [text, baseName])

  const sendToCollation = useCallback(
    (role: 'base' | 'collation') => {
      const name = baseName()
      navigate('/multi-collation', {
        state: {
          prefill: true,
          source: 'ocr',
          ...(role === 'base'
            ? { baseText: text, baseName: name }
            : { collationText: text, collationName: name }),
        },
      })
    },
    [text, baseName, navigate]
  )

  const sendMenu: MenuProps = {
    items: [
      { key: 'base', label: t('ocr.sendAsBase') },
      { key: 'collation', label: t('ocr.sendAsCollation') },
    ],
    onClick: ({ key }) => sendToCollation(key as 'base' | 'collation'),
  }

  return (
    <div>
      <Space
        align="center"
        style={{ marginBottom: 16, justifyContent: 'space-between', width: '100%' }}
      >
        <h2 style={{ margin: 0 }}>
          <ScanOutlined style={{ marginRight: 8 }} />
          {t('ocr.title')}
        </h2>
        {enabled === true && <Text type="success">{t('ocr.ready')}</Text>}
      </Space>

      {enabled === false && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message={t('ocr.notConfigured')}
          description={t('ocr.notConfiguredHint')}
        />
      )}

      <Row gutter={16}>
        {/* 左：上传 + 预览 */}
        <Col xs={24} md={11}>
          <Card title={t('ocr.uploadTitle')} size="small">
            <Dragger
              accept="image/*"
              multiple={false}
              showUploadList={false}
              disabled={enabled === false}
              beforeUpload={(f) => {
                onSelectFile(f as unknown as File)
                return false // 阻止自动上传，由「开始识别」触发
              }}
              fileList={[] as UploadFile[]}
            >
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="preview"
                  style={{ maxWidth: '100%', maxHeight: 360, objectFit: 'contain' }}
                />
              ) : (
                <>
                  <p className="ant-upload-drag-icon">
                    <InboxOutlined />
                  </p>
                  <p className="ant-upload-text">{t('ocr.dragHint')}</p>
                  <p className="ant-upload-hint">{t('ocr.formatHint')}</p>
                </>
              )}
            </Dragger>

            <Button
              type="primary"
              icon={<ScanOutlined />}
              loading={recognizing}
              disabled={!file || enabled === false}
              onClick={handleRecognize}
              style={{ marginTop: 12 }}
              block
            >
              {t('ocr.startRecognize')}
            </Button>
          </Card>
        </Col>

        {/* 右：识别结果 */}
        <Col xs={24} md={13}>
          <Card title={t('ocr.resultTitle')} size="small">
            <TextArea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={t('ocr.resultPlaceholder')}
              autoSize={{ minRows: 14, maxRows: 24 }}
            />
            <Space style={{ marginTop: 12, justifyContent: 'space-between', width: '100%' }} wrap>
              <Text type="secondary">
                {t('ocr.stats', {
                  chars: stats.charNumber ?? text.length,
                  lines: stats.lineNumber ?? '-',
                })}
              </Text>
              <Space wrap>
                <Button icon={<CopyOutlined />} disabled={!text} onClick={handleCopy}>
                  {t('ocr.copy')}
                </Button>
                <Button icon={<DownloadOutlined />} disabled={!text} onClick={handleDownload}>
                  {t('ocr.download')}
                </Button>
                <Dropdown menu={sendMenu} disabled={!text}>
                  <Button type="primary" icon={<SendOutlined />}>
                    {t('ocr.sendToCollation')}
                  </Button>
                </Dropdown>
              </Space>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
