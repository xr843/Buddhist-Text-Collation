/**
 * 对话面板 - Workspace中栏
 */
import { useState, useRef, useEffect } from 'react'
import { Input, Button, Card, Space, Typography, Divider, Tag, Empty, message } from 'antd'
import { SendOutlined, UserOutlined, RobotOutlined } from '@ant-design/icons'
import { useChatStore, useDocumentStore } from '../../store'

const { Text, Paragraph } = Typography
const { TextArea } = Input

export default function ChatPanel() {
  const {
    currentSessionId,
    sessions,
    createSession,
    addMessage,
    getMessagesBySession,
    suggestedQuestions,
    setSuggestedQuestions,
  } = useChatStore()

  const { getSelectedDocuments } = useDocumentStore()

  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 确保有当前会话
  useEffect(() => {
    if (!currentSessionId && sessions.length === 0) {
      createSession('新对话')
    }
  }, [currentSessionId, sessions, createSession])

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentSessionId, getMessagesBySession(currentSessionId || 0)])

  const handleSend = () => {
    if (!inputValue.trim()) {
      message.warning('请输入消息')
      return
    }

    if (!currentSessionId) {
      message.warning('请先创建会话')
      return
    }

    const selectedDocs = getSelectedDocuments()
    if (selectedDocs.length === 0) {
      message.warning('请先选择文档')
      return
    }

    // 添加用户消息
    addMessage({
      sessionId: currentSessionId,
      role: 'user',
      content: inputValue.trim(),
    })

    setInputValue('')

    // 模拟AI回复（MVP版本）
    setTimeout(() => {
      addMessage({
        sessionId: currentSessionId!,
        role: 'assistant',
        content: `这是一个模拟回复。您选择了 ${selectedDocs.length} 个文档，共 ${selectedDocs.reduce(
          (sum, doc) => sum + doc.charCount,
          0
        )} 字。\n\nMVP版本暂时返回模拟数据，完整的AI对话功能将在后续版本实现。`,
        sources: selectedDocs.map((doc) => ({
          documentId: doc.id,
          documentName: doc.name,
          position: 0,
          excerpt: doc.content.slice(0, 50) + '...',
        })),
      })

      // 更新建议问题
      setSuggestedQuestions([
        { id: '1', text: '为选中的文档添加标点', category: 'analysis' },
        { id: '2', text: '对比不同版本的差异', category: 'comparison' },
        { id: '3', text: '生成思维导图', category: 'analysis' },
      ])
    }, 500)
  }

  const currentMessages = getMessagesBySession(currentSessionId || 0)
  const selectedDocs = getSelectedDocuments()

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 顶部状态栏 */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>
        <Space>
          <Text strong>💬 对话</Text>
          {selectedDocs.length > 0 && (
            <Tag color="blue">{selectedDocs.length} 个来源</Tag>
          )}
        </Space>
      </div>

      {/* 消息列表 */}
      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        {currentMessages.length === 0 ? (
          <Empty
            description="开始与文档对话"
            style={{ marginTop: 60 }}
          >
            <Text type="secondary">选择左侧的文档，然后提出您的问题</Text>
          </Empty>
        ) : (
          <>
            {currentMessages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  marginBottom: 16,
                  display: 'flex',
                  gap: 12,
                }}
              >
                {/* 头像 */}
                <div>
                  {msg.role === 'user' ? (
                    <UserOutlined
                      style={{
                        fontSize: 24,
                        padding: 8,
                        background: '#1890ff',
                        color: '#fff',
                        borderRadius: '50%',
                      }}
                    />
                  ) : (
                    <RobotOutlined
                      style={{
                        fontSize: 24,
                        padding: 8,
                        background: '#52c41a',
                        color: '#fff',
                        borderRadius: '50%',
                      }}
                    />
                  )}
                </div>

                {/* 消息内容 */}
                <div style={{ flex: 1 }}>
                  <div style={{ marginBottom: 4 }}>
                    <Text strong>{msg.role === 'user' ? '你' : 'AI助手'}</Text>
                    <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </Text>
                  </div>
                  <Card size="small" style={{ background: msg.role === 'user' ? '#e6f7ff' : '#f6ffed' }}>
                    <Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </Paragraph>

                    {/* 引用来源 */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid #f0f0f0' }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          📎 引用来源:
                        </Text>
                        <div style={{ marginTop: 4 }}>
                          {msg.sources.map((source, index) => (
                            <Tag key={index} style={{ marginBottom: 4 }}>
                              [{index + 1}] {source.documentName}
                            </Tag>
                          ))}
                        </div>
                      </div>
                    )}
                  </Card>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* 建议问题 */}
      {suggestedQuestions.length > 0 && (
        <div style={{ padding: '0 16px 12px' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            💡 你可能想要:
          </Text>
          <div style={{ marginTop: 8 }}>
            {suggestedQuestions.map((q) => (
              <Button
                key={q.id}
                size="small"
                style={{ marginRight: 8, marginBottom: 8 }}
                onClick={() => setInputValue(q.text)}
              >
                {q.text}
              </Button>
            ))}
          </div>
        </div>
      )}

      <Divider style={{ margin: 0 }} />

      {/* 输入框 */}
      <div style={{ padding: 16 }}>
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="输入你的问题..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            style={{ height: 'auto' }}
          >
            发送
          </Button>
        </Space.Compact>
        <div style={{ marginTop: 4 }}>
          <Text type="secondary" style={{ fontSize: 11 }}>
            Enter 发送 · Shift+Enter 换行 · {selectedDocs.length} 个来源
          </Text>
        </div>
      </div>
    </div>
  )
}
