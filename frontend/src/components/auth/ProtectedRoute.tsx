/**
 * 受保护路由组件
 * 未登录用户会被重定向到登录页
 */
import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireAdmin?: boolean
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAdmin = false,
}) => {
  const location = useLocation()
  const { isAuthenticated, isAdmin } = useAuthStore()

  // 未登录，跳转到登录页
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // 需要管理员权限但当前用户不是管理员
  if (requireAdmin && !isAdmin()) {
    return <Navigate to="/workspace" replace />
  }

  return <>{children}</>
}

export default ProtectedRoute
