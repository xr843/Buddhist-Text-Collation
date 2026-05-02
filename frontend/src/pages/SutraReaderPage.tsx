/**
 * 经文阅读页面
 * 路由: /cbeta/read/:sutraId
 */
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import SutraReader from '../components/SutraReader'

export default function SutraReaderPage() {
  const { sutraId } = useParams<{ sutraId: string }>()
  const navigate = useNavigate()
  const location = useLocation()

  // 从路由状态获取初始数据（如果有的话）
  const initialData = location.state?.sutraData || null

  const handleBack = () => {
    // 如果有历史记录，返回上一页；否则跳转到CBETA导入页
    if (window.history.length > 1) {
      navigate(-1)
    } else {
      navigate('/cbeta-import')
    }
  }

  if (!sutraId) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <p>未指定经文ID</p>
      </div>
    )
  }

  return (
    <SutraReader
      sutraId={sutraId}
      onBack={handleBack}
      initialData={initialData}
    />
  )
}
