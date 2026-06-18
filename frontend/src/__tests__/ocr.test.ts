/**
 * 古籍 OCR 功能冒烟测试
 *
 * 锁定 OCR 相关的 i18n key（菜单项 + 页面文案）在中英两套语言里都存在，
 * 防止后续改动漏配翻译导致页面出现裸 key。
 */
import { describe, it, expect } from 'vitest'
import zhCommon from '../i18n/locales/zh-CN/common.json'
import enCommon from '../i18n/locales/en/common.json'

const REQUIRED_OCR_KEYS = [
  'title',
  'notConfigured',
  'uploadTitle',
  'startRecognize',
  'startRecognizeRegion',
  'dragSelectHint',
  'regionSelectedHint',
  'reselect',
  'clearSelection',
  'resultTitle',
  'sendToCollation',
  'sendAsBase',
  'sendAsCollation',
] as const

describe('ocr i18n', () => {
  it('menu.ocr exists in both locales', () => {
    expect((zhCommon as any).menu.ocr).toBeTruthy()
    expect((enCommon as any).menu.ocr).toBeTruthy()
  })

  it('ocr page strings exist in both locales', () => {
    for (const key of REQUIRED_OCR_KEYS) {
      expect((zhCommon as any).ocr?.[key], `zh-CN ocr.${key}`).toBeTruthy()
      expect((enCommon as any).ocr?.[key], `en ocr.${key}`).toBeTruthy()
    }
  })
})
