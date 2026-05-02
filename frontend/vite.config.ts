import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, __dirname, '')
  const apiUrl = (env.VITE_API_URL || '').trim()
  const apiPort = (env.VITE_API_PORT || '').trim() || '8001'
  const apiTarget = apiUrl || `http://localhost:${apiPort}`

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      host: true, // 允许局域网访问
      port: 5173, // 本地开发端口（Docker 用 3000）
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          timeout: 300000, // 5分钟代理超时，确保长文本处理不会被中断
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'ui-vendor': ['antd', '@ant-design/icons'],
            'editor-vendor': ['slate', 'slate-react', 'slate-history'],
          },
        },
      },
    },
  }
})
