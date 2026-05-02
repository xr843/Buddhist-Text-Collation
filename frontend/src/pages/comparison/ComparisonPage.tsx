/**
 * 标点版本对比页面 - 主组件
 * 支持上传两个带标点的文本文件，进行标点差异分析
 * 支持项目持久化存储（保存/加载/列表/删除）
 */

import { useCallback } from 'react'
import { Card, Space, Spin, message } from 'antd'
import { DiffOutlined } from '@ant-design/icons'

import FileUploadCompare from '../../components/FileUploadCompare'
import FloatingReviewDrawer from '../../components/FloatingReviewDrawer'
import PunctuationDefinitiveModal from '../../components/PunctuationDefinitiveModal'
import '../../components/HybridComparisonView.css'

import { downloadPunctuationDefinitiveText, downloadPunctuationChangeNotes } from '../../utils/exportUtils'
import { fetchProject, fetchDecisions } from './api'
import { exportComparisonReport } from './exportUtils'
import {
  useProjectManager,
  useDecisionManager,
  useReviewNavigation,
  useDifferenceFilter,
  useFileCompare,
} from './hooks'
import { PUNCTUATION_CATEGORIES } from './constants'

import PageHeader from './PageHeader'
import ProjectDrawer from './ProjectDrawer'
import StatisticsCard from './StatisticsCard'
import CompareWorkspace from './CompareWorkspace'
import KeyboardHints from './KeyboardHints'

export default function ComparisonPage() {
  // 文件对比
  const { result, setResult, loading, handleCompare: doCompare } = useFileCompare()

  // 差异筛选
  const {
    selectedCategories,
    setSelectedCategories,
    filteredDifferences,
    toggleCategory,
    selectAllCategories,
    clearCategories,
  } = useDifferenceFilter(result)

  // 审核导航
  const {
    reviewStatus,
    currentDiffIndex,
    setCurrentDiffIndex,
    selectedDiff,
    setSelectedDiff,
    diffNotes,
    setDiffNotes,
    reviewDrawerVisible,
    setReviewDrawerVisible,
    reviewedCount,
    reviewProgress,
    initReviewStatus,
    gotoPrevious,
    gotoNext,
    markCurrentAsReviewed,
  } = useReviewNavigation(filteredDifferences)

  // 项目管理
  const projectManager = useProjectManager()
  const {
    currentProjectId,
    setCurrentProjectId,
    currentProjectTitle,
    setCurrentProjectTitle,
    projectDrawerOpen,
    setProjectDrawerOpen,
    filteredProjectList,
    projectList,
    projectListLoading,
    projectListTotal,
    editingTitle,
    setEditingTitle,
    projectSearch,
    setProjectSearch,
    openProjectDrawer,
    deleteProject,
    updateProjectTitle,
    createNewProject: doCreateNewProject,
    copyProjectId,
  } = projectManager

  // 判取管理
  const decisionManager = useDecisionManager(
    currentProjectId,
    result,
    selectedDiff,
    filteredDifferences,
    currentDiffIndex,
    setCurrentDiffIndex,
    setSelectedDiff
  )
  const {
    decisionMode,
    setDecisionMode,
    decisions,
    setDecisions,
    definitiveModalOpen,
    setDefinitiveModalOpen,
    definitiveData,
    generatingDefinitive,
    savingDecisions,
    decisionCount,
    handleDecision,
    saveDecisions,
    generateDefinitiveText,
    resetDecisions,
  } = decisionManager

  // 文件上传后的对比处理
  const handleFileCompare = useCallback(
    async (file1: File, file2: File, version1Name: string, version2Name: string) => {
      const compareResult = await doCompare(file1, file2, version1Name, version2Name)
      if (!compareResult) return

      const { result: response, projectId, projectTitle } = compareResult

      // 更新项目状态
      if (projectId) {
        setCurrentProjectId(projectId)
        setCurrentProjectTitle(projectTitle || '')
      }

      // 初始化审核状态
      if (response.punctuation_analysis) {
        const diffCount = response.punctuation_analysis.differences?.length || 0
        initReviewStatus(diffCount)

        // 默认选中所有分类
        if (response.punctuation_analysis.categories) {
          setSelectedCategories([...PUNCTUATION_CATEGORIES])
        }

        // 设置第一个差异为选中
        if (response.punctuation_analysis.differences?.length > 0) {
          setSelectedDiff(response.punctuation_analysis.differences[0])
        }
      }
    },
    [doCompare, setCurrentProjectId, setCurrentProjectTitle, initReviewStatus, setSelectedCategories, setSelectedDiff]
  )

  // 加载项目详情
  const loadProject = useCallback(
    async (projectId: string) => {
      setProjectDrawerOpen(false)
      try {
        const project = await fetchProject(projectId)

        // 设置结果
        setResult(project.data.result)
        setCurrentProjectId(project.id)
        setCurrentProjectTitle(project.title)

        // 初始化审核状态
        if (project.data.result.punctuation_analysis) {
          const diffCount = project.data.result.punctuation_analysis.differences?.length || 0
          initReviewStatus(diffCount)
          setSelectedCategories([...PUNCTUATION_CATEGORIES])
          if (project.data.result.punctuation_analysis.differences?.length > 0) {
            setSelectedDiff(project.data.result.punctuation_analysis.differences[0])
          }
        }

        message.success(`已加载项目: ${project.title}`)

        // 加载已有判取结果
        const loadedDecisions = await fetchDecisions(project.id)
        if (Object.keys(loadedDecisions).length > 0) {
          setDecisions(loadedDecisions)
          message.info(`已加载 ${Object.keys(loadedDecisions).length} 条判取结果`)
        }
      } catch (error: any) {
        message.error('加载项目失败: ' + error.message)
      }
    },
    [setProjectDrawerOpen, setResult, setCurrentProjectId, setCurrentProjectTitle, initReviewStatus, setSelectedCategories, setSelectedDiff, setDecisions]
  )

  // 处理项目搜索
  const handleProjectSearch = useCallback(
    (value: string) => {
      const query = value.trim()
      if (!query) return
      const exact = projectList.find((p) => p.id === query)
      if (exact) {
        void loadProject(exact.id)
      }
    },
    [loadProject, projectList]
  )

  // 处理删除项目
  const handleDeleteProject = useCallback(
    async (projectId: string) => {
      const deletedCurrent = await deleteProject(projectId)
      if (deletedCurrent) {
        setResult(null)
        resetDecisions()
      }
    },
    [deleteProject, setResult, resetDecisions]
  )

  // 新建项目
  const createNewProject = useCallback(() => {
    doCreateNewProject()
    setResult(null)
    resetDecisions()
    initReviewStatus(0)
    setSelectedDiff(null)
  }, [doCreateNewProject, setResult, resetDecisions, initReviewStatus, setSelectedDiff])

  // 处理差异点击
  const handleDiffClick = useCallback(
    (diff: any, index: number) => {
      setCurrentDiffIndex(index)
      setSelectedDiff(diff)
      // 点击差异时自动打开审核抽屉
      if (!reviewDrawerVisible) {
        setReviewDrawerVisible(true)
      }
    },
    [setCurrentDiffIndex, setSelectedDiff, reviewDrawerVisible, setReviewDrawerVisible]
  )

  // 导出报告
  const handleExportReport = useCallback(() => {
    if (result) {
      exportComparisonReport(result)
    }
  }, [result])

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题 */}
        <PageHeader
          currentProjectId={currentProjectId}
          currentProjectTitle={currentProjectTitle}
          editingTitle={editingTitle}
          onOpenProjectDrawer={openProjectDrawer}
          onCreateNew={createNewProject}
          onEditTitle={() => setEditingTitle(true)}
          onUpdateTitle={updateProjectTitle}
          onCopyProjectId={() => void copyProjectId()}
        />

        {/* 文件上传区域 */}
        <Card title="上传文件或输入文本">
          <FileUploadCompare onCompare={handleFileCompare} loading={loading} />
        </Card>

        {/* 加载状态 */}
        {loading && (
          <Card>
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
              <Spin size="large" />
              <p style={{ marginTop: 20, color: '#666' }}>正在分析标点差异，AI正在深度分析...</p>
            </div>
          </Card>
        )}

        {/* 分析结果 */}
        {!loading && result && result.punctuation_analysis && (
          <>
            {/* 统计仪表板 */}
            <StatisticsCard
              result={result}
              selectedCategories={selectedCategories}
              filteredDifferencesCount={filteredDifferences.length}
              reviewedCount={reviewedCount}
              reviewProgress={reviewProgress}
              onToggleCategory={toggleCategory}
              onSelectAllCategories={selectAllCategories}
              onClearCategories={clearCategories}
              onExportReport={handleExportReport}
            />

            {/* 对比工作区 */}
            <CompareWorkspace
              result={result}
              selectedDiff={selectedDiff}
              filteredDifferences={filteredDifferences}
              decisionMode={decisionMode}
              decisionCount={decisionCount}
              currentProjectId={currentProjectId}
              savingDecisions={savingDecisions}
              generatingDefinitive={generatingDefinitive}
              reviewDrawerVisible={reviewDrawerVisible}
              onDecisionModeToggle={() => setDecisionMode(!decisionMode)}
              onSaveDecisions={() => void saveDecisions()}
              onGenerateDefinitive={() => void generateDefinitiveText()}
              onReviewDrawerToggle={() => setReviewDrawerVisible(!reviewDrawerVisible)}
              onDiffClick={handleDiffClick}
            />

            {/* 浮动审核抽屉 */}
            <FloatingReviewDrawer
              visible={reviewDrawerVisible}
              difference={selectedDiff}
              currentIndex={currentDiffIndex}
              totalCount={filteredDifferences.length}
              reviewedCount={reviewedCount}
              progress={reviewProgress}
              isReviewed={reviewStatus[currentDiffIndex] || false}
              note={selectedDiff ? diffNotes[selectedDiff.id] || '' : ''}
              version1Name={result.version1_name}
              version2Name={result.version2_name}
              canGoPrev={currentDiffIndex > 0}
              canGoNext={currentDiffIndex < filteredDifferences.length - 1}
              onReview={markCurrentAsReviewed}
              onPrevious={gotoPrevious}
              onNext={gotoNext}
              onSkip={gotoNext}
              onNoteChange={(note) => {
                if (selectedDiff) {
                  setDiffNotes((prev) => ({ ...prev, [selectedDiff.id]: note }))
                }
              }}
              onClose={() => setReviewDrawerVisible(false)}
              // 判取功能
              decisionMode={decisionMode}
              currentDecision={selectedDiff ? decisions[selectedDiff.id] || null : null}
              decisionCount={decisionCount}
              onDecision={handleDecision}
            />

            {/* 底部快捷键提示 */}
            <KeyboardHints visible={filteredDifferences.length > 0} />
          </>
        )}

        {/* 无结果提示 */}
        {!loading && !result && (
          <Card>
            <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
              <DiffOutlined style={{ fontSize: 64, marginBottom: 16 }} />
              <p style={{ fontSize: 16 }}>请上传两个带标点的文本文件开始分析</p>
            </div>
          </Card>
        )}
      </Space>

      {/* 项目列表抽屉 */}
      <ProjectDrawer
        open={projectDrawerOpen}
        projectList={projectList}
        filteredProjectList={filteredProjectList}
        projectListLoading={projectListLoading}
        projectListTotal={projectListTotal}
        currentProjectId={currentProjectId}
        projectSearch={projectSearch}
        onSearchChange={setProjectSearch}
        onSearch={handleProjectSearch}
        onClose={() => setProjectDrawerOpen(false)}
        onLoad={loadProject}
        onDelete={handleDeleteProject}
        onCreateNew={createNewProject}
      />

      {/* 标点定本预览 Modal */}
      <PunctuationDefinitiveModal
        open={definitiveModalOpen}
        data={definitiveData}
        projectTitle={currentProjectTitle}
        onClose={() => setDefinitiveModalOpen(false)}
        onDownloadText={() => downloadPunctuationDefinitiveText(definitiveData, currentProjectTitle)}
        onDownloadNotes={() => downloadPunctuationChangeNotes(definitiveData, currentProjectTitle)}
      />
    </div>
  )
}
