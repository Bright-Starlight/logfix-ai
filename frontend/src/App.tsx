import { useState, useEffect } from 'react'
import FileUpload from './components/FileUpload'
import LogPreview from './components/LogPreview'
import SplitConfig from './components/SplitConfig'
import ResultList from './components/ResultList'
import LogList from './components/LogList'
import LogDetail from './components/LogDetail'
import SearchFilter from './components/SearchFilter'
import StatsPanel from './components/StatsPanel'
import ClassificationStream from './components/ClassificationStream'
import type { SearchFilters } from './components/SearchFilter'
import type { SessionListItem } from './types'
import { getSessionList } from './services/api'

export interface AppState {
  fileId: string | null
  sessionId: string | null
  splitStatus: 'idle' | 'pending' | 'processing' | 'completed' | 'failed'
  activeView: 'split' | 'classify'
  selectedLogId: string | null
  searchFilters: SearchFilters
}

function App() {
  const [state, setState] = useState<AppState>({
    fileId: null,
    sessionId: null,
    splitStatus: 'idle',
    activeView: 'split',
    selectedLogId: null,
    searchFilters: {},
  })
  const [sessions, setSessions] = useState<SessionListItem[]>([])
  const [classificationStarted, setClassificationStarted] = useState(false)

  // 加载切分会话列表
  useEffect(() => {
    if (state.activeView === 'classify' && !classificationStarted) {
      loadSessions()
    }
  }, [state.activeView, classificationStarted])

  const loadSessions = async () => {
    try {
      const response = await getSessionList()
      if (response.success && response.data) {
        setSessions(response.data.sessions)
      }
    } catch (err) {
      console.error('加载会话列表失败:', err)
    }
  }

  const handleClassificationComplete = () => {
    setClassificationStarted(false)
    loadSessions() // 刷新会话列表
  }

  const handleClassificationCancel = () => {
    setClassificationStarted(false)
  }

  const handleFileUploaded = (fileId: string) => {
    setState((prev) => ({ ...prev, fileId, sessionId: null, splitStatus: 'idle' }))
  }

  const handleSplitStarted = (sessionId: string) => {
    setState((prev) => ({ ...prev, sessionId, splitStatus: 'processing' }))
  }

  const handleSplitCompleted = () => {
    setState((prev) => ({ ...prev, splitStatus: 'completed' }))
  }

  const handleReset = () => {
    setState((prev) => ({ ...prev, fileId: null, sessionId: null, splitStatus: 'idle' }))
  }

  const handleTabChange = (tab: 'split' | 'classify') => {
    setState((prev) => ({ ...prev, activeView: tab, selectedLogId: null }))
  }

  const handleLogSelect = (logId: string) => {
    setState((prev) => ({ ...prev, selectedLogId: logId }))
  }

  const handleLogBack = () => {
    setState((prev) => ({ ...prev, selectedLogId: null }))
  }

  const handleSearch = (filters: SearchFilters) => {
    setState((prev) => ({ ...prev, searchFilters: filters }))
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>LogFix AI</h1>
        <nav className="app-nav">
          <button
            className={`nav-tab ${state.activeView === 'split' ? 'active' : ''}`}
            onClick={() => handleTabChange('split')}
          >
            日志切分
          </button>
          <button
            className={`nav-tab ${state.activeView === 'classify' ? 'active' : ''}`}
            onClick={() => handleTabChange('classify')}
          >
            日志分类
          </button>
        </nav>
      </header>

      <main className="app-main">
        {state.activeView === 'split' && (
          <>
            {state.splitStatus === 'idle' && !state.fileId && (
              <FileUpload onFileUploaded={handleFileUploaded} />
            )}

            {state.fileId && state.splitStatus === 'idle' && (
              <>
                <LogPreview fileId={state.fileId} />
                <SplitConfig
                  fileId={state.fileId}
                  onSplitStarted={handleSplitStarted}
                />
              </>
            )}

            {state.splitStatus === 'processing' && state.sessionId && (
              <SplitConfig
                fileId={state.fileId!}
                sessionId={state.sessionId}
                onSplitCompleted={handleSplitCompleted}
              />
            )}

            {state.splitStatus === 'completed' && state.sessionId && (
              <>
                <ResultList sessionId={state.sessionId} />
                <button onClick={handleReset} className="reset-button">
                  上传新文件
                </button>
              </>
            )}
          </>
        )}

        {state.activeView === 'classify' && (
          <>
            {state.selectedLogId ? (
              <LogDetail logId={state.selectedLogId} onBack={handleLogBack} />
            ) : (
              <>
                {classificationStarted ? (
                  <ClassificationStream
                    sessions={sessions}
                    onComplete={handleClassificationComplete}
                    onCancel={handleClassificationCancel}
                  />
                ) : (
                  <>
                    <StatsPanel />
                    <SearchFilter onSearch={handleSearch} />
                    <LogList
                      onLogSelect={handleLogSelect}
                      filters={state.searchFilters}
                    />
                  </>
                )}
              </>
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App
