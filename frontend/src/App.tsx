import { Routes, Route, Navigate } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { Spin } from 'antd'
import MainLayout from './components/Layout/MainLayout'
import ProtectedRoute from './components/auth/ProtectedRoute'

// 路由级代码分割：每个 page 独立 chunk，按需加载，大幅缩短首屏 JS
const Workspace = lazy(() => import('./pages/Workspace'))
const Comparison = lazy(() => import('./pages/Comparison'))
const ComparisonNew = lazy(() => import('./pages/ComparisonNew'))
const MultiCollation = lazy(() => import('./pages/MultiCollation'))
const CBETAImport = lazy(() => import('./pages/CBETAImport'))
const OcrRecognition = lazy(() => import('./pages/OcrRecognition'))
const SutraReaderPage = lazy(() => import('./pages/SutraReaderPage'))
const SutraParallelReader = lazy(() => import('./pages/SutraParallelReader'))
const PunctuationTransfer = lazy(() => import('./pages/PunctuationTransfer'))
const Settings = lazy(() => import('./pages/Settings'))
const Login = lazy(() => import('./pages/auth/Login'))
const Register = lazy(() => import('./pages/auth/Register'))
const Profile = lazy(() => import('./pages/auth/Profile'))
const AdminUsers = lazy(() => import('./pages/admin/Users'))

function PageLoader() {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 'calc(100vh - 160px)',
      }}
    >
      <Spin size="large" tip="加载中…" />
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route
          element={
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route index element={<Navigate to="/punctuation-compare" replace />} />
                <Route path="workspace" element={<Workspace />} />
                <Route path="punctuation-compare" element={<Comparison />} />
                <Route path="two-version-collation" element={<ComparisonNew />} />
                <Route path="multi-collation" element={<MultiCollation />} />
                <Route path="ocr" element={<OcrRecognition />} />
                <Route path="cbeta-import" element={<CBETAImport />} />
                <Route path="cbeta/read/:sutraId" element={<SutraReaderPage />} />
                <Route path="sutra-parallel-reader" element={<SutraParallelReader />} />
                <Route path="punctuation-transfer" element={<PunctuationTransfer />} />
                <Route path="settings" element={<Settings />} />
                <Route path="login" element={<Login />} />
                <Route path="register" element={<Register />} />
                <Route
                  path="profile"
                  element={
                    <ProtectedRoute>
                      <Profile />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/users"
                  element={
                    <ProtectedRoute requireAdmin>
                      <AdminUsers />
                    </ProtectedRoute>
                  }
                />
                <Route path="comparison" element={<Navigate to="/punctuation-compare" replace />} />
              </Routes>
            </Suspense>
          }
          path="*"
        />
      </Route>
    </Routes>
  )
}

export default App
