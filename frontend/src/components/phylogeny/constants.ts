/**
 * 版本谱系分析 - 常量定义
 */

// 版本系统颜色映射（团队标准：汉文大藏经三系分类）
export const SYSTEM_COLORS: Record<string, string> = {
  '中系': '#faad14',
  '南系': '#52c41a',
  '北系': '#1890ff',
  '近现代藏经': '#722ed1',
  '未知': '#8c8c8c',
}

// 常见藏经名称列表（按长度降序排列，优先匹配更具体的名称）
export const KNOWN_CANONS = [
  '赵城金藏', '趙城金藏', '永乐南藏', '永樂南藏', '永乐北藏', '永樂北藏',
  '洪武南藏', '卍字正藏', '房山石经', '房山石經',
  '高麗藏', '高丽藏', '大正藏', '中华藏', '中華藏', '缩刻藏', '縮刻藏',
  '崇宁藏', '崇寧藏', '毗卢藏', '毘盧藏', '思溪藏',
  '碛砂藏', '磧砂藏', '普宁藏', '普寧藏',
  '嘉兴藏', '嘉興藏', '龙藏', '龍藏', '乾隆藏',
  '频伽藏', '頻伽藏', '卍续藏', '卍正藏',
  '契丹藏', '开宝藏', '開寶藏',
  '丽藏', '金藏', '南藏', '北藏',
]

// 相似度颜色方案
export const SIMILARITY_COLOR_SCHEME = [
  '#3182bd', '#6baed6', '#9ecae1', '#c6dbef',
  '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26', '#a50f15',
]

// 异文类型配置
export const VARIANT_TYPE_CONFIG = {
  error: {
    title: '共同讹误',
    colorScheme: ['#fff5f5', '#ffccc7', '#ffa39e', '#ff7875', '#ff4d4f', '#f5222d', '#cf1322', '#a8071a'],
    background: '#fff2f0',
    border: '#ffccc7',
    description: '共同讹误是版本亲缘关系的重要证据，同位置、同内容的讹误表明版本可能有共同来源',
  },
  variant: {
    title: '共同异体字',
    colorScheme: ['#f6ffed', '#d9f7be', '#b7eb8f', '#95de64', '#73d13d', '#52c41a', '#389e0d', '#237804'],
    background: '#f6ffed',
    border: '#b7eb8f',
    description: '共同异体字可能暗示版本关联，同位置使用相同异体字表明版本间可能有传承关系',
  },
  yantuo: {
    title: '共同衍脱',
    colorScheme: ['#fffbe6', '#fff1b8', '#ffe58f', '#ffd666', '#ffc53d', '#faad14', '#d48806', '#ad6800'],
    background: '#fffbe6',
    border: '#ffe58f',
    description: '共同衍脱暗示共同底本错误，同位置的衍文/脱文说明版本可能源自同一有误底本',
  },
  combined: {
    title: '共同异文',
    colorScheme: ['#f0f5ff', '#d6e4ff', '#adc6ff', '#85a5ff', '#597ef7', '#2f54eb', '#1d39c4', '#10239e'],
    background: '#e6f4ff',
    border: '#91caff',
    description: '综合分析讹误、异体字、衍脱三类异文，全面了解版本关联',
  },
}

// 类别颜色映射
export const CATEGORY_COLOR_MAP: Record<string, string> = {
  error: '#f5222d',
  variant: '#52c41a',
  tuowen: '#fa8c16',
  yanwen: '#fa8c16',
}
