/**
 * 登录页面
 */
import React, { useState } from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { Form, Input, Button, Card, message, Typography, Space } from 'antd'
import { UserOutlined, LockOutlined, BookOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../store/authStore'
import type { LoginRequest } from '../../types/auth'

const { Title, Text } = Typography

const Login: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()

  // 获取来源页面，登录后跳转回去
  const from = (location.state as any)?.from?.pathname || '/workspace'

  const handleSubmit = async (values: LoginRequest) => {
    setLoading(true)
    try {
      await login(values)
      message.success('登录成功')
      navigate(from, { replace: true })
    } catch (error: any) {
      message.error(error.message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        padding: 24,
      }}
    >
      <Card
        style={{
          width: '100%',
          maxWidth: 400,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <BookOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
          <Title level={3} style={{ margin: 0 }}>
            佛典标点与校勘研究平台
          </Title>
          <Text type="secondary">登录您的账户</Text>
        </div>

        <Form
          name="login"
          onFinish={handleSubmit}
          autoComplete="off"
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名或邮箱' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名或邮箱"
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
            >
              登录
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <Space>
              <Text type="secondary">还没有账户？</Text>
              <Link to="/register">立即注册</Link>
            </Space>
          </div>
        </Form>
      </Card>
    </div>
  )
}

export default Login
