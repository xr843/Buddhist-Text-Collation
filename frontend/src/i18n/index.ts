/**
 * i18n 入口 / i18n entry
 *
 * 用法 / Usage:
 *   import { useTranslation } from 'react-i18next'
 *   const { t } = useTranslation()
 *   t('menu.workspace')   // → "工作台" or "Workbench"
 *
 * 切换语言 / Switch language:
 *   i18n.changeLanguage('en')  // 写到 localStorage，自动持久化
 *
 * 添加新翻译 / Adding translations:
 *   编辑 src/i18n/locales/<lang>/common.json
 *   逐步把组件里的硬编码中文换成 t('namespace.key')
 */
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

import zhCN from './locales/zh-CN/common.json'
import en from './locales/en/common.json'

export const resources = {
  'zh-CN': { common: zhCN },
  en: { common: en },
} as const

export const supportedLanguages = [
  { code: 'zh-CN', label: '中文' },
  { code: 'en', label: 'English' },
] as const

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'zh-CN',
    defaultNS: 'common',
    supportedLngs: ['zh-CN', 'en'],
    interpolation: {
      escapeValue: false, // React 已经做了 XSS 转义
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },
  })

export default i18n
