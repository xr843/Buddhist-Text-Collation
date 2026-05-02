/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_API_URL?: string
  readonly VITE_API_PORT?: string
  // 更多环境变量可以在这里添加
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
