/**
 * 版本名称解析工具
 * 负责解析佛经版本全名，提取藏经系统、藏经名称、佛典名称等信息
 */

import {
  STANDARD_CANONS,
  VERSION_SUFFIX_REGEX,
  MAX_CANON_NAME_LENGTH,
  MAX_SHORT_NAME_LENGTH,
} from '../constants/multiCollation'

/**
 * 版本信息结构
 */
export interface VersionInfo {
  /** 藏经系统：南系、北系、中系、未知 */
  system: string
  /** 藏经名称 */
  canon: string
  /** 佛典名称 */
  sutra: string
}

/**
 * 解析版本名称为三层信息：藏经系统、藏经名称、佛典名称
 *
 * @param fullName - 完整版本名称，如 "【中系●中華藏中華書局版】《妙法莲华经》卷1"
 * @returns 结构化的版本信息
 *
 * @example
 * parseVersionInfo("【中系●中華藏中華書局版】")
 * // => { system: '中系', canon: '中華藏', sutra: '' }
 *
 * parseVersionInfo("【南系●洪武南藏】《妙法莲华经》卷1")
 * // => { system: '南系', canon: '洪武南藏', sutra: '《妙法莲华经》卷1' }
 */
export function parseVersionInfo(fullName: string): VersionInfo {
  let system = '未知'
  let canon = ''
  let sutra = ''

  // 1. 提取【】中的全部内容
  const bracketMatch = fullName.match(/【([^】]+)】/)
  const bracketContent = bracketMatch ? bracketMatch[1] : ''

  // 2. 提取藏经系统（南系、北系、中系、未知）
  if (bracketContent.includes('南系')) {
    system = '南系'
  } else if (bracketContent.includes('北系')) {
    system = '北系'
  } else if (bracketContent.includes('中系')) {
    system = '中系'
  } else if (bracketContent.includes('未知')) {
    system = '未知'
  }

  // 3. 提取藏经名称（从【】内容中，去掉系统前缀后的部分）
  // 使用通用的分隔符匹配（.匹配任意单个字符）
  const separatorMatch = bracketContent.match(/[南北中]系.(.+)/) || bracketContent.match(/未知.(.+)/)
  const canonRaw = separatorMatch ? separatorMatch[1] : bracketContent

  // 去掉末尾的"版"字
  const canonClean = canonRaw.replace(/版$/, '')

  if (canonClean) {
    // 先尝试匹配标准藏经名
    for (const [pattern, name] of STANDARD_CANONS) {
      if (pattern.test(canonClean)) {
        canon = name
        break
      }
    }
    // 如果没有标准藏经名，再检查版本标识（金陵版、华夏版等）
    if (!canon) {
      if (/金陵/.test(canonClean)) {
        canon = '金陵版'
      } else if (/华夏|華夏/.test(canonClean)) {
        canon = '华夏版'
      } else {
        // 其他情况：去掉版本后缀
        canon = canonClean.replace(VERSION_SUFFIX_REGEX, '')
        if (canon.length > MAX_CANON_NAME_LENGTH) {
          canon = canon.substring(0, MAX_CANON_NAME_LENGTH)
        }
      }
    }
  }

  // 4. 提取佛典名称（《书名》卷N）
  const sutraMatch = fullName.match(/《([^》]+)》(卷[^卷]*)?/)
  if (sutraMatch) {
    sutra = `《${sutraMatch[1]}》${sutraMatch[2] || ''}`
  }

  return { system, canon: canon || '未知', sutra: sutra || '' }
}

/**
 * 从版本全名提取简称（优先显示藏经系统+藏经名称）
 *
 * @param fullName - 完整版本名称
 * @returns 简短的显示名称，格式为"系统●藏经名"
 *
 * @example
 * getShortName("【中系●中華藏中華書局版】")
 * // => "中系●中華藏"
 *
 * getShortName("01丽增-底本")
 * // => "丽增"
 *
 * getShortName("丽藏-校本")
 * // => "丽藏"
 *
 * getShortName("乾隆")
 * // => "乾隆" (非标准格式，直接返回原文件名)
 */
export function getShortName(fullName: string): string {
  // 使用 parseVersionInfo 获取结构化信息
  const info = parseVersionInfo(fullName)

  // 如果能解析出藏经名称，返回"系统●藏经名"格式
  if (info.canon && info.canon !== '未知') {
    return `${info.system}●${info.canon}`
  }

  // 回退：尝试其他匹配规则
  // 匹配 "数字+藏经名-" 格式，如 "01丽增-底本" -> "丽增"
  const numMatch = fullName.match(/^\d*([^-\d（(]+)[-（(]/)
  if (numMatch) return numMatch[1]

  // 匹配 "藏经名-" 格式，如 "丽藏-校本" -> "丽藏"
  const simpleMatch = fullName.match(/^([^-（(]+)[-（(]/)
  if (simpleMatch && simpleMatch[1].length <= MAX_SHORT_NAME_LENGTH) {
    return simpleMatch[1]
  }

  // 非标准格式：直接返回原文件名（去掉扩展名）
  // 例如 "乾隆.txt" -> "乾隆"，"乾隆" -> "乾隆"
  const nameWithoutExt = fullName.replace(/\.[^.]+$/, '').trim()
  if (nameWithoutExt) {
    return nameWithoutExt
  }

  // 最后的回退：返回原始输入
  return fullName || '未知'
}
