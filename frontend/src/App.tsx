import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './components/Layout/MainLayout'
import Workspace from './pages/Workspace'
import Comparison from './pages/Comparison'
import ComparisonNew from './pages/ComparisonNew'
import MultiCollation from './pages/MultiCollation'
import CBETAImport from './pages/CBETAImport'
import SutraReaderPage from './pages/SutraReaderPage'
import SutraParallelReader from './pages/SutraParallelReader'
import PunctuationTransfer from './pages/PunctuationTransfer'
import Settings from './pages/Settings'

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        {/* 默认跳转到标点版本对比 */}
        <Route index element={<Navigate to="/punctuation-compare" replace />} />
        <Route path="workspace" element={<Workspace />} />
        {/* 标点版本对比 */}
        <Route path="punctuation-compare" element={<Comparison />} />
        {/* 版本对勘 */}
        <Route path="two-version-collation" element={<ComparisonNew />} />
        <Route path="multi-collation" element={<MultiCollation />} />
        {/* CBETA数据导入 */}
        <Route path="cbeta-import" element={<CBETAImport />} />
        {/* CBETA经文阅读 */}
        <Route path="cbeta/read/:sutraId" element={<SutraReaderPage />} />
        {/* 经论注疏对读 */}
        <Route path="sutra-parallel-reader" element={<SutraParallelReader />} />
        {/* 标点迁移 */}
        <Route path="punctuation-transfer" element={<PunctuationTransfer />} />
        {/* 其他 */}
        <Route path="settings" element={<Settings />} />
        {/* 兼容旧路由 */}
        <Route path="comparison" element={<Navigate to="/punctuation-compare" replace />} />
      </Route>
    </Routes>
  )
}

export default App
