/**
 * 版本对勘模块常量配置
 */

// 校勘文件限制
export const MAX_COLLATION_FILES = 30

// 表格分页配置
export const DEFAULT_PAGE_SIZE = 50
export const PAGE_SIZE_OPTIONS = [20, 50, 100, 200]

// 藏经系统颜色映射
export const SYSTEM_COLORS: Record<string, string> = {
  '南系': '#52c41a',
  '北系': '#1890ff',
  '中系': '#722ed1',
  '未知': '#8c8c8c',
}

// 标准藏经名映射表
export const STANDARD_CANONS: [RegExp, string][] = [
  [/赵城金藏|趙城金藏/, '趙城金藏'],
  [/洪武南藏/, '洪武南藏'],
  [/永乐南藏|永樂南藏/, '永樂南藏'],
  [/永乐北藏|永樂北藏/, '永樂北藏'],
  [/嘉兴藏|嘉興藏/, '嘉興藏'],
  [/房山石经|房山石經/, '房山石經'],
  [/开宝藏|開寶藏/, '開寶藏'],
  [/中华藏|中華藏/, '中華藏'],
  [/大正藏/, '大正藏'],
  [/乾隆藏/, '乾隆藏'],
  [/龙藏|龍藏/, '龍藏'],
  [/契丹藏/, '契丹藏'],
  [/缩刻藏|縮刻藏/, '縮刻藏'],
  [/崇寧|崇宁/, '崇寧'],
  [/频伽|頻伽/, '頻伽'],
  [/碛砂|磧砂/, '磧砂'],
  [/普宁|普寧/, '普寧'],
  [/思溪/, '思溪'],
  [/毗卢|毘盧/, '毘盧'],
  [/高丽|高麗/, '高麗'],
  [/卍正藏/, '卍正藏'],
  [/卍续藏|卍續藏/, '卍續藏'],
  [/CBETA/i, 'CBETA'],
]

// 版本后缀正则
export const VERSION_SUFFIX_REGEX = /(國圖版|川佛協版|大學版|增上寺版|宮内廳版|書局版|刻經處版|精舍版|基金會版).*$/

// 字符串截取长度限制
export const MAX_CANON_NAME_LENGTH = 8
export const MAX_SHORT_NAME_LENGTH = 6
export const MAX_SUTRA_NAME_LENGTH = 10
