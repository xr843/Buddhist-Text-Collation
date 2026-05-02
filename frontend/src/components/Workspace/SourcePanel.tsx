/**
 * 来源管理面板 - Workspace左栏
 */
import { useState } from 'react'
import { Button, Upload, Input, List, Checkbox, Space, Typography, Divider, message } from 'antd'
import { PlusOutlined, FileTextOutlined, SearchOutlined, FolderOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd'
import { useDocumentStore } from '../../store'

const { Text } = Typography
const { TextArea } = Input

export default function SourcePanel() {
  const {
    documents,
    selectedDocIds,
    selectDocument,
    deselectDocument,
    addDocument,
    getSelectedDocuments,
  } = useDocumentStore()

  const [showUpload, setShowUpload] = useState(false)
  const [uploadText, setUploadText] = useState('')
  const [uploadName, setUploadName] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  // 处理文本输入添加文档
  const handleAddText = () => {
    if (!uploadText.trim()) {
      message.warning('请输入文本内容')
      return
    }

    const doc = addDocument({
      name: uploadName.trim() || `文档 ${documents.length + 1}`,
      content: uploadText.trim(),
      type: 'original',
      charCount: uploadText.trim().length,
    })

    message.success(`已添加文档: ${doc.name}`)
    setUploadText('')
    setUploadName('')
    setShowUpload(false)
  }

  // 处理文件上传
  const handleFileUpload = async (file: UploadFile) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target?.result as string
      const doc = addDocument({
        name: file.name || `文档 ${documents.length + 1}`,
        content,
        type: 'original',
        charCount: content.length,
      })
      message.success(`已添加文档: ${doc.name}`)
    }
    reader.readAsText(file as any)
    return false // 阻止自动上传
  }

  // 过滤文档
  const filteredDocs = documents.filter((doc) =>
    doc.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const selectedCount = selectedDocIds.length
  const totalChars = getSelectedDocuments().reduce((sum, doc) => sum + doc.charCount, 0)

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: 16 }}>
      {/* 标题栏 */}
      <div style={{ marginBottom: 16 }}>
        <Text strong style={{ fontSize: 16 }}>📚 来源</Text>
      </div>

      {/* 添加来源按钮 */}
      {!showUpload ? (
        <Button
          type="primary"
          icon={<PlusOutlined />}
          block
          onClick={() => setShowUpload(true)}
          style={{ marginBottom: 16 }}
        >
          添加来源
        </Button>
      ) : (
        <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Input
              placeholder="文档名称（可选）"
              value={uploadName}
              onChange={(e) => setUploadName(e.target.value)}
              size="small"
            />
            <TextArea
              placeholder="直接输入文本..."
              value={uploadText}
              onChange={(e) => setUploadText(e.target.value)}
              rows={4}
              size="small"
            />
            <Space>
              <Button size="small" type="primary" onClick={handleAddText}>
                添加
              </Button>
              <Upload
                accept=".txt,.md"
                beforeUpload={handleFileUpload}
                showUploadList={false}
              >
                <Button size="small" icon={<FileTextOutlined />}>
                  上传文件
                </Button>
              </Upload>
              <Button size="small" onClick={() => setShowUpload(false)}>
                取消
              </Button>
            </Space>
          </Space>
        </div>
      )}

      {/* 搜索 */}
      <Input
        placeholder="搜索文档..."
        prefix={<SearchOutlined />}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        size="small"
        style={{ marginBottom: 12 }}
      />

      <Divider style={{ margin: '8px 0' }} />

      {/* 文档列表 */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {filteredDocs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 24, color: '#999' }}>
            <FolderOutlined style={{ fontSize: 48, marginBottom: 8 }} />
            <div>暂无文档</div>
            <div style={{ fontSize: 12 }}>点击"添加来源"开始</div>
          </div>
        ) : (
          <List
            dataSource={filteredDocs}
            renderItem={(doc) => (
              <List.Item
                style={{
                  padding: '8px 0',
                  cursor: 'pointer',
                  background: selectedDocIds.includes(doc.id) ? '#e6f7ff' : 'transparent',
                  borderRadius: 4,
                  marginBottom: 4,
                }}
                onClick={() => {
                  if (selectedDocIds.includes(doc.id)) {
                    deselectDocument(doc.id)
                  } else {
                    selectDocument(doc.id)
                  }
                }}
              >
                <Space style={{ width: '100%' }}>
                  <Checkbox checked={selectedDocIds.includes(doc.id)} />
                  <div style={{ flex: 1 }}>
                    <div>
                      <Text strong style={{ fontSize: 13 }}>
                        {doc.name}
                      </Text>
                    </div>
                    <div>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {doc.charCount} 字 · {doc.type === 'original' ? '原文' : '已标点'}
                      </Text>
                    </div>
                  </div>
                </Space>
              </List.Item>
            )}
          />
        )}
      </div>

      {/* 统计信息 */}
      <Divider style={{ margin: '8px 0' }} />
      <div style={{ padding: '8px 0' }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          已选择: {selectedCount} 个文档
        </Text>
        <br />
        <Text type="secondary" style={{ fontSize: 12 }}>
          总字数: {totalChars.toLocaleString()} 字
        </Text>
      </div>
    </div>
  )
}
