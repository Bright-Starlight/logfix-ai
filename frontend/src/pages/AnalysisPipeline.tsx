import { useState, useCallback } from 'react'
import FileUpload from '../components/FileUpload'
import LogPreview from '../components/LogPreview'
import SplitConfig from '../components/SplitConfig'
import ResultList from '../components/ResultList'
import LogList from '../components/LogList'
import LogDetail from '../components/LogDetail'
import SearchFilter, { SearchFilters } from '../components/SearchFilter'
import StatsPanel from '../components/StatsPanel'
import IgnoreRuleManager from '../components/IgnoreRuleManager'

type PipelineView = 'upload' | 'split' | 'classify' | 'results'
type ClassifyView = 'list' | 'detail'

export default function AnalysisPipeline() {
  // File upload state
  const [fileId, setFileId] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [splitStatus, setSplitStatus] = useState<'idle' | 'pending' | 'processing' | 'completed' | 'failed'>('idle')

  // View state
  const [currentView, setCurrentView] = useState<PipelineView>('upload')
  const [classifyView, setClassifyView] = useState<ClassifyView>('list')
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null)
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({})
  const [showIgnoreRules, setShowIgnoreRules] = useState(false)

  // Handlers
  const handleFileUploaded = useCallback((uploadedFileId: string) => {
    setFileId(uploadedFileId)
    setSessionId(null)
    setSplitStatus('idle')
    setCurrentView('split')
  }, [])

  const handleSplitStarted = useCallback((splitSessionId: string) => {
    setSessionId(splitSessionId)
    setSplitStatus('processing')
  }, [])

  const handleSplitCompleted = useCallback(() => {
    setSplitStatus('completed')
    setCurrentView('classify')
  }, [])

  const handleLogSelect = useCallback((logId: string) => {
    setSelectedLogId(logId)
    setClassifyView('detail')
  }, [])

  const handleLogBack = useCallback(() => {
    setSelectedLogId(null)
    setClassifyView('list')
  }, [])

  const handleSearch = useCallback((filters: SearchFilters) => {
    setSearchFilters(filters)
  }, [])

  const handleReset = useCallback(() => {
    setFileId(null)
    setSessionId(null)
    setSplitStatus('idle')
    setCurrentView('upload')
    setSelectedLogId(null)
    setClassifyView('list')
    setSearchFilters({})
  }, [])

  const handleBackToSplit = useCallback(() => {
    setCurrentView('split')
  }, [])

  return (
    <div className="analysis-pipeline">
      <header className="pipeline-header">
        <h1>日志分析流水线</h1>
        <nav className="pipeline-nav">
          <button
            className={`nav-btn ${currentView === 'upload' ? 'active' : ''}`}
            onClick={() => setCurrentView('upload')}
          >
            上传
          </button>
          <button
            className={`nav-btn ${currentView === 'split' ? 'active' : ''}`}
            onClick={() => setCurrentView('split')}
            disabled={!fileId}
          >
            切分
          </button>
          <button
            className={`nav-btn ${currentView === 'classify' ? 'active' : ''}`}
            onClick={() => setCurrentView('classify')}
            disabled={!sessionId}
          >
            分类
          </button>
          <button
            className={`nav-btn ${currentView === 'results' ? 'active' : ''}`}
            onClick={() => setCurrentView('results')}
          >
            结果
          </button>
        </nav>
      </header>

      <main className="pipeline-content">
        {/* 上传视图 */}
        {currentView === 'upload' && (
          <div className="pipeline-upload">
            <FileUpload onFileUploaded={handleFileUploaded} />
          </div>
        )}

        {/* 切分视图 */}
        {currentView === 'split' && fileId && (
          <div className="pipeline-split">
            {splitStatus === 'idle' && (
              <>
                <LogPreview fileId={fileId} />
                <SplitConfig
                  fileId={fileId}
                  onSplitStarted={handleSplitStarted}
                />
              </>
            )}

            {splitStatus === 'processing' && sessionId && (
              <SplitConfig
                fileId={fileId}
                sessionId={sessionId}
                onSplitCompleted={handleSplitCompleted}
              />
            )}

            {splitStatus === 'completed' && sessionId && (
              <>
                <ResultList sessionId={sessionId} />
                <div className="pipeline-actions">
                  <button onClick={handleBackToSplit} className="secondary-button">
                    重新切分
                  </button>
                  <button onClick={() => setCurrentView('classify')} className="primary-button">
                    继续分类
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* 分类视图 */}
        {currentView === 'classify' && sessionId && (
          <div className="pipeline-classify">
            <ResultList sessionId={sessionId} />
            <div className="pipeline-actions">
              <button onClick={() => setCurrentView('results')} className="primary-button">
                查看结果
              </button>
            </div>
          </div>
        )}

        {/* 结果视图 */}
        {currentView === 'results' && (
          <div className="pipeline-results">
            <div className="results-header">
              <button
                className="secondary-button"
                onClick={() => setShowIgnoreRules(!showIgnoreRules)}
              >
                {showIgnoreRules ? '关闭忽略规则' : '忽略规则配置'}
              </button>
            </div>

            {showIgnoreRules && (
              <div className="ignore-rules-section">
                <IgnoreRuleManager />
              </div>
            )}

            {classifyView === 'detail' && selectedLogId ? (
              <LogDetail logId={selectedLogId} onBack={handleLogBack} />
            ) : (
              <>
                <StatsPanel />
                <SearchFilter onSearch={handleSearch} />
                <LogList
                  onLogSelect={handleLogSelect}
                  filters={searchFilters}
                />
              </>
            )}
          </div>
        )}
      </main>

      <footer className="pipeline-footer">
        <button onClick={handleReset} className="reset-button">
          开始新任务
        </button>
      </footer>
    </div>
  )
}
