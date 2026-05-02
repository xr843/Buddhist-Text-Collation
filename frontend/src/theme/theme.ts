/**
 * 主题配置 - "禅意/学术" 设计语言
 *
 * 设计理念：
 * - 服务于"可读性、专注、低疲劳"
 * - 沉稳、护眼的配色
 * - 人文气息的 Typography
 */
import type { ThemeConfig } from 'antd'

// ==================== 配色方案 ====================

/**
 * 色彩系统 - 浅色模式
 */
export const colors = {
  // 主色 - 靛青（沉稳、专业）
  primary: '#384E77',
  primaryHover: '#4A6491',
  primaryActive: '#2D3E5F',

  // 强调色 - 朱砂（用于重要操作、错误提示）
  accent: '#C64153',
  accentHover: '#D4596A',
  accentActive: '#A33545',

  // 背景色 - 米白（模拟纸张质感）
  bgBase: '#FDFBF7',
  bgContainer: '#FFFFFF',
  bgElevated: '#FFFFFF',
  bgLayout: '#F5F3EF',

  // 文字色
  textPrimary: 'rgba(0, 0, 0, 0.88)',
  textSecondary: 'rgba(0, 0, 0, 0.65)',
  textTertiary: 'rgba(0, 0, 0, 0.45)',
  textDisabled: 'rgba(0, 0, 0, 0.25)',

  // 边框色
  border: '#E8E4DC',
  borderSecondary: '#F0ECE4',

  // 功能色 - 差异标识（柔和版）
  diffInsert: '#73D13D',      // 草绿 - 新增
  diffInsertBg: '#F6FFED',
  diffDelete: '#FF4D4F',      // 砖红 - 删除
  diffDeleteBg: '#FFF1F0',
  diffReplace: '#FAAD14',     // 琥珀 - 替换
  diffReplaceBg: '#FFFBE6',
  diffVariant: '#52C41A',     // 绿色 - 异体字
  diffVariantBg: '#F6FFED',

  // 状态色
  success: '#52C41A',
  warning: '#FAAD14',
  error: '#C64153',           // 使用朱砂作为错误色
  info: '#384E77',            // 使用主色作为信息色
}

// ==================== Typography ====================

/**
 * 字体配置
 * - 标题：衬线体（典雅）
 * - 正文：无衬线体（清晰）
 * - 古籍：专用衬线体 + 大字号
 */
export const typography = {
  // 标题字体（衬线体优先）
  fontFamilyHeading: [
    '"Noto Serif SC"',
    '"Source Han Serif SC"',
    '"STSong"',
    '"SimSun"',
    'serif',
  ].join(', '),

  // 正文字体（无衬线体）
  fontFamilyBase: [
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    '"PingFang SC"',
    '"Hiragino Sans GB"',
    '"Microsoft YaHei"',
    '"Helvetica Neue"',
    'Helvetica',
    'Arial',
    'sans-serif',
  ].join(', '),

  // 古籍文本字体
  fontFamilyAncient: [
    '"Noto Serif SC"',
    '"Source Han Serif SC"',
    '"STSong"',
    '"SimSun"',
    'serif',
  ].join(', '),

  // 代码字体
  fontFamilyCode: [
    '"Fira Code"',
    '"Source Code Pro"',
    'Consolas',
    'Monaco',
    'monospace',
  ].join(', '),

  // 字号
  fontSize: 14,
  fontSizeSM: 12,
  fontSizeLG: 16,
  fontSizeXL: 20,
  fontSizeHeading1: 38,
  fontSizeHeading2: 30,
  fontSizeHeading3: 24,
  fontSizeHeading4: 20,
  fontSizeHeading5: 16,

  // 行高
  lineHeight: 1.6,
  lineHeightLG: 1.8,      // 古籍文本行高
  lineHeightSM: 1.4,
  lineHeightHeading: 1.4,
}

// ==================== 主题配置生成 ====================

/**
 * 生成 Ant Design 主题配置（仅浅色模式）
 */
export function createThemeConfig(_mode: 'light' | 'dark' = 'light'): ThemeConfig {
  return {
    token: {
      // 主色
      colorPrimary: colors.primary,
      colorPrimaryHover: colors.primaryHover,
      colorPrimaryActive: colors.primaryActive,

      // 错误色（使用朱砂）
      colorError: colors.error,

      // 成功/警告/信息色
      colorSuccess: colors.success,
      colorWarning: colors.warning,
      colorInfo: colors.info,

      // 背景色
      colorBgBase: colors.bgBase,
      colorBgContainer: colors.bgContainer,
      colorBgElevated: colors.bgElevated,
      colorBgLayout: colors.bgLayout,

      // 文字色
      colorText: colors.textPrimary,
      colorTextSecondary: colors.textSecondary,
      colorTextTertiary: colors.textTertiary,
      colorTextDisabled: colors.textDisabled,

      // 边框色
      colorBorder: colors.border,
      colorBorderSecondary: colors.borderSecondary,

      // 字体
      fontFamily: typography.fontFamilyBase,
      fontSize: typography.fontSize,
      fontSizeSM: typography.fontSizeSM,
      fontSizeLG: typography.fontSizeLG,
      fontSizeXL: typography.fontSizeXL,
      fontSizeHeading1: typography.fontSizeHeading1,
      fontSizeHeading2: typography.fontSizeHeading2,
      fontSizeHeading3: typography.fontSizeHeading3,
      fontSizeHeading4: typography.fontSizeHeading4,
      fontSizeHeading5: typography.fontSizeHeading5,

      // 行高
      lineHeight: typography.lineHeight,
      lineHeightLG: typography.lineHeightLG,
      lineHeightSM: typography.lineHeightSM,
      lineHeightHeading1: typography.lineHeightHeading,
      lineHeightHeading2: typography.lineHeightHeading,
      lineHeightHeading3: typography.lineHeightHeading,
      lineHeightHeading4: typography.lineHeightHeading,
      lineHeightHeading5: typography.lineHeightHeading,

      // 圆角
      borderRadius: 6,
      borderRadiusLG: 8,
      borderRadiusSM: 4,

      // 动画
      motionDurationFast: '0.1s',
      motionDurationMid: '0.2s',
      motionDurationSlow: '0.3s',
    },

    components: {
      // Typography 组件 - 标题使用衬线体
      Typography: {
        fontFamilyCode: typography.fontFamilyCode,
        titleMarginBottom: '0.5em',
        titleMarginTop: '1.2em',
      },

      // Layout 组件
      Layout: {
        headerBg: colors.bgContainer,
        bodyBg: colors.bgLayout,
        siderBg: colors.bgContainer,
        headerHeight: 56,
      },

      // Menu 组件
      Menu: {
        itemBg: 'transparent',
        subMenuItemBg: 'transparent',
        itemSelectedBg: '#EDE9E3',
        itemSelectedColor: colors.primary,
        itemHoverBg: '#F5F3EF',
      },

      // Card 组件
      Card: {
        headerBg: 'transparent',
      },

      // Table 组件
      Table: {
        headerBg: '#FAF8F4',
        rowHoverBg: '#F5F3EF',
      },

      // Button 组件
      Button: {
        primaryShadow: 'none',
        defaultShadow: 'none',
      },

      // Input 组件
      Input: {
        activeBorderColor: colors.primary,
        hoverBorderColor: colors.primaryHover,
      },

      // Select 组件
      Select: {
        optionSelectedBg: '#EDE9E3',
      },

      // Modal 组件
      Modal: {
        contentBg: colors.bgContainer,
        headerBg: colors.bgContainer,
      },

      // Drawer 组件
      Drawer: {
        colorBgElevated: colors.bgContainer,
      },

      // Tag 组件 - 柔和色彩
      Tag: {
        defaultBg: '#F5F3EF',
        defaultColor: colors.textSecondary,
      },

      // Alert 组件
      Alert: {
        colorInfoBg: '#F0EDE8',
        colorInfoBorder: '#D9D4CC',
      },
    },
  }
}

// 导出默认主题
export const defaultTheme = createThemeConfig('light')
