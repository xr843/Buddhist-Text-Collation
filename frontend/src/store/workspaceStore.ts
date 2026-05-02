/**
 * 工作台状态管理
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { StudioOutput, StudioToolType, LayoutConfig } from '../types/studio'

interface WorkspaceState {
  // 布局状态
  layout: LayoutConfig

  // Studio相关
  activeStudioTool: StudioToolType | null
  outputs: StudioOutput[]
  nextOutputId: number

  // 布局操作
  setLayout: (layout: Partial<LayoutConfig>) => void
  toggleLeftPanel: () => void
  toggleRightPanel: () => void
  setLeftWidth: (width: number) => void
  setRightWidth: (width: number) => void

  // Studio工具操作
  openStudioTool: (tool: StudioToolType) => void
  closeStudioTool: () => void

  // 输出管理
  addOutput: (output: Omit<StudioOutput, 'id' | 'createdAt'>) => StudioOutput
  removeOutput: (id: number) => void
  getOutput: (id: number) => StudioOutput | undefined
  getOutputsByTool: (toolType: StudioToolType) => StudioOutput[]
  getRecentOutputs: (limit?: number) => StudioOutput[]
  clearOldOutputs: (daysToKeep: number) => void
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set, get) => ({
      // 初始布局
      layout: {
        leftWidth: 280,
        rightWidth: 320,
        leftCollapsed: false,
        rightCollapsed: false,
      },

      // 初始Studio状态
      activeStudioTool: null,
      outputs: [],
      nextOutputId: 1,

      // 布局操作
      setLayout: (newLayout) => {
        set((state) => ({
          layout: { ...state.layout, ...newLayout },
        }))
      },

      toggleLeftPanel: () => {
        set((state) => ({
          layout: {
            ...state.layout,
            leftCollapsed: !state.layout.leftCollapsed,
          },
        }))
      },

      toggleRightPanel: () => {
        set((state) => ({
          layout: {
            ...state.layout,
            rightCollapsed: !state.layout.rightCollapsed,
          },
        }))
      },

      setLeftWidth: (width) => {
        set((state) => ({
          layout: { ...state.layout, leftWidth: width },
        }))
      },

      setRightWidth: (width) => {
        set((state) => ({
          layout: { ...state.layout, rightWidth: width },
        }))
      },

      // Studio工具操作
      openStudioTool: (tool) => {
        set({ activeStudioTool: tool })
      },

      closeStudioTool: () => {
        set({ activeStudioTool: null })
      },

      // 输出管理
      addOutput: (output) => {
        const newOutput: StudioOutput = {
          ...output,
          id: get().nextOutputId,
          createdAt: new Date(),
        }
        set((state) => ({
          outputs: [newOutput, ...state.outputs], // 新输出放在最前面
          nextOutputId: state.nextOutputId + 1,
        }))
        return newOutput
      },

      removeOutput: (id) => {
        set((state) => ({
          outputs: state.outputs.filter((output) => output.id !== id),
        }))
      },

      getOutput: (id) => {
        return get().outputs.find((output) => output.id === id)
      },

      getOutputsByTool: (toolType) => {
        return get().outputs.filter((output) => output.toolType === toolType)
      },

      getRecentOutputs: (limit = 5) => {
        return get().outputs.slice(0, limit)
      },

      clearOldOutputs: (daysToKeep) => {
        const cutoffDate = new Date()
        cutoffDate.setDate(cutoffDate.getDate() - daysToKeep)

        set((state) => ({
          outputs: state.outputs.filter(
            (output) => new Date(output.createdAt) > cutoffDate
          ),
        }))
      },
    }),
    {
      name: 'buddhist-workspace',
      partialize: (state) => ({
        layout: state.layout,
        outputs: state.outputs,
        nextOutputId: state.nextOutputId,
      }),
    }
  )
)
