import { Typography, Empty } from 'antd'

const { Title } = Typography

export default function Settings() {
  return (
    <div>
      <Title level={2}>设置</Title>
      <Empty description="设置功能开发中..." />
    </div>
  )
}
