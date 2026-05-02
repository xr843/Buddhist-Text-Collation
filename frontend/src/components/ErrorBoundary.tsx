import React from 'react'
import { Alert, Button, Space, Typography } from 'antd'

const { Paragraph, Text } = Typography

type ErrorBoundaryState = {
  error: Error | null
  errorInfo: React.ErrorInfo | null
  source: 'render' | 'window.error' | 'unhandledrejection' | null
}

export default class ErrorBoundary extends React.Component<
  React.PropsWithChildren,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null, errorInfo: null, source: null }

  private onWindowError = (event: ErrorEvent) => {
    const err =
      event.error instanceof Error ? event.error : new Error(event.message || 'Unknown error')
    this.setState({ error: err, errorInfo: null, source: 'window.error' })
  }

  private onUnhandledRejection = (event: PromiseRejectionEvent) => {
    const reason = event.reason
    const err = reason instanceof Error ? reason : new Error(String(reason || 'Unhandled rejection'))
    this.setState({ error: err, errorInfo: null, source: 'unhandledrejection' })
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { error, source: 'render' }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ error, errorInfo })
  }

  componentDidMount() {
    window.addEventListener('error', this.onWindowError)
    window.addEventListener('unhandledrejection', this.onUnhandledRejection)
  }

  componentWillUnmount() {
    window.removeEventListener('error', this.onWindowError)
    window.removeEventListener('unhandledrejection', this.onUnhandledRejection)
  }

  private handleReset = () => {
    this.setState({ error: null, errorInfo: null, source: null })
  }

  private handleCopy = async () => {
    const { error, errorInfo, source } = this.state
    if (!error) return

    const content = [
      `Source: ${source || 'unknown'}`,
      `Message: ${error.message}`,
      '',
      error.stack || '',
      '',
      errorInfo?.componentStack || '',
    ]
      .filter(Boolean)
      .join('\n')

    try {
      await navigator.clipboard.writeText(content)
    } catch {
      const textarea = document.createElement('textarea')
      textarea.value = content
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
  }

  render() {
    const { error, errorInfo, source } = this.state

    if (!error) {
      return this.props.children
    }

    return (
      <div style={{ padding: 24 }}>
        <Alert
          type="error"
          showIcon
          message="页面运行出错（已拦截，避免白屏）"
          description={
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text type="secondary">来源：{source || 'unknown'}</Text>
              <Paragraph style={{ marginBottom: 0 }}>
                <Text strong>错误信息：</Text> {error.message || '(无)'}
              </Paragraph>
              <Space wrap>
                <Button onClick={this.handleCopy}>复制错误信息</Button>
                <Button onClick={this.handleReset}>尝试恢复</Button>
                <Button danger onClick={() => window.location.reload()}>
                  刷新页面
                </Button>
              </Space>
              {(error.stack || errorInfo?.componentStack) && (
                <pre
                  style={{
                    marginTop: 8,
                    padding: 12,
                    background: '#fafafa',
                    border: '1px solid #f0f0f0',
                    borderRadius: 8,
                    maxHeight: 320,
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    fontSize: 12,
                    lineHeight: 1.6,
                  }}
                >
                  {error.stack}
                  {errorInfo?.componentStack ? `\n\nComponent stack:\n${errorInfo.componentStack}` : ''}
                </pre>
              )}
            </Space>
          }
        />
      </div>
    )
  }
}

