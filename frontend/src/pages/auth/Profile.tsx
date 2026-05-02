/**
 * 个人中心页面
 */
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Form,
  Input,
  Button,
  message,
  Typography,
  Tabs,
  Avatar,
  Descriptions,
  Space,
  Row,
  Col,
} from 'antd'
import {
  UserOutlined,
  BankOutlined,
  BookOutlined,
  EditOutlined,
  LockOutlined,
  SaveOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../../store/authStore'
import type { UserUpdateRequest, PasswordChangeRequest } from '../../types/auth'

const { Title, Text } = Typography
const { TextArea } = Input

const Profile: React.FC = () => {
  const navigate = useNavigate()
  const { user, isAuthenticated, updateProfile, changePassword, isLoading } = useAuthStore()
  const [profileForm] = Form.useForm()
  const [passwordForm] = Form.useForm()
  const [editing, setEditing] = useState(false)

  // 未登录跳转
  if (!isAuthenticated || !user) {
    navigate('/login', { replace: true })
    return null
  }

  // 提交个人信息更新
  const handleProfileSubmit = async (values: UserUpdateRequest) => {
    try {
      await updateProfile(values)
      message.success('个人信息更新成功')
      setEditing(false)
    } catch (error: any) {
      message.error(error.message || '更新失败')
    }
  }

  // 提交密码修改
  const handlePasswordSubmit = async (values: PasswordChangeRequest & { confirmPassword: string }) => {
    if (values.new_password !== values.confirmPassword) {
      message.error('两次输入的密码不一致')
      return
    }

    try {
      await changePassword({
        old_password: values.old_password,
        new_password: values.new_password,
      })
      message.success('密码修改成功')
      passwordForm.resetFields()
    } catch (error: any) {
      message.error(error.message || '修改密码失败')
    }
  }

  // 格式化日期
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  return (
    <div style={{ padding: 24, maxWidth: 900, margin: '0 auto' }}>
      <Title level={3}>
        <UserOutlined /> 个人中心
      </Title>

      <Tabs
        defaultActiveKey="profile"
        items={[
          {
            key: 'profile',
            label: '基本信息',
            children: (
              <Card>
                <Row gutter={[24, 24]}>
                  <Col xs={24} md={8} style={{ textAlign: 'center' }}>
                    <Avatar
                      size={120}
                      src={user.avatar_url}
                      icon={!user.avatar_url && <UserOutlined />}
                      style={{ backgroundColor: '#1890ff', marginBottom: 16 }}
                    />
                    <div>
                      <Title level={4} style={{ margin: 0 }}>
                        {user.full_name || user.username}
                      </Title>
                      <Text type="secondary">
                        {user.role === 'admin' ? '管理员' : '普通用户'}
                      </Text>
                    </div>
                  </Col>
                  <Col xs={24} md={16}>
                    {!editing ? (
                      <>
                        <Descriptions column={1} bordered size="small">
                          <Descriptions.Item label="用户名">
                            {user.username}
                          </Descriptions.Item>
                          <Descriptions.Item label="邮箱">
                            {user.email}
                          </Descriptions.Item>
                          <Descriptions.Item label="姓名">
                            {user.full_name || '-'}
                          </Descriptions.Item>
                          <Descriptions.Item label="所属机构">
                            {user.institution || '-'}
                          </Descriptions.Item>
                          <Descriptions.Item label="研究领域">
                            {user.research_field || '-'}
                          </Descriptions.Item>
                          <Descriptions.Item label="个人简介">
                            {user.bio || '-'}
                          </Descriptions.Item>
                          <Descriptions.Item label="注册时间">
                            {formatDate(user.created_at)}
                          </Descriptions.Item>
                          <Descriptions.Item label="最后登录">
                            {formatDate(user.last_login)}
                          </Descriptions.Item>
                        </Descriptions>
                        <div style={{ marginTop: 16, textAlign: 'right' }}>
                          <Button
                            type="primary"
                            icon={<EditOutlined />}
                            onClick={() => {
                              profileForm.setFieldsValue({
                                full_name: user.full_name,
                                institution: user.institution,
                                research_field: user.research_field,
                                bio: user.bio,
                                avatar_url: user.avatar_url,
                              })
                              setEditing(true)
                            }}
                          >
                            编辑资料
                          </Button>
                        </div>
                      </>
                    ) : (
                      <Form
                        form={profileForm}
                        layout="vertical"
                        onFinish={handleProfileSubmit}
                      >
                        <Form.Item name="full_name" label="姓名">
                          <Input
                            prefix={<UserOutlined />}
                            placeholder="您的姓名"
                            maxLength={100}
                          />
                        </Form.Item>
                        <Form.Item name="institution" label="所属机构">
                          <Input
                            prefix={<BankOutlined />}
                            placeholder="所属机构或单位"
                            maxLength={200}
                          />
                        </Form.Item>
                        <Form.Item name="research_field" label="研究领域">
                          <Input
                            prefix={<BookOutlined />}
                            placeholder="您的研究领域"
                            maxLength={200}
                          />
                        </Form.Item>
                        <Form.Item name="bio" label="个人简介">
                          <TextArea
                            placeholder="简单介绍一下自己"
                            rows={4}
                            maxLength={2000}
                            showCount
                          />
                        </Form.Item>
                        <Form.Item name="avatar_url" label="头像URL">
                          <Input placeholder="头像图片地址" maxLength={500} />
                        </Form.Item>
                        <Form.Item>
                          <Space>
                            <Button
                              type="primary"
                              icon={<SaveOutlined />}
                              htmlType="submit"
                              loading={isLoading}
                            >
                              保存
                            </Button>
                            <Button onClick={() => setEditing(false)}>
                              取消
                            </Button>
                          </Space>
                        </Form.Item>
                      </Form>
                    )}
                  </Col>
                </Row>
              </Card>
            ),
          },
          {
            key: 'security',
            label: '安全设置',
            children: (
              <Card title="修改密码">
                <Form
                  form={passwordForm}
                  layout="vertical"
                  onFinish={handlePasswordSubmit}
                  style={{ maxWidth: 400 }}
                >
                  <Form.Item
                    name="old_password"
                    label="当前密码"
                    rules={[{ required: true, message: '请输入当前密码' }]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="当前密码"
                    />
                  </Form.Item>
                  <Form.Item
                    name="new_password"
                    label="新密码"
                    rules={[
                      { required: true, message: '请输入新密码' },
                      { min: 6, message: '密码至少6个字符' },
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="新密码"
                    />
                  </Form.Item>
                  <Form.Item
                    name="confirmPassword"
                    label="确认新密码"
                    rules={[
                      { required: true, message: '请确认新密码' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('new_password') === value) {
                            return Promise.resolve()
                          }
                          return Promise.reject(new Error('两次输入的密码不一致'))
                        },
                      }),
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="确认新密码"
                    />
                  </Form.Item>
                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={isLoading}
                    >
                      修改密码
                    </Button>
                  </Form.Item>
                </Form>
              </Card>
            ),
          },
        ]}
      />
    </div>
  )
}

export default Profile
