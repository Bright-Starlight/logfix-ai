import { useState } from 'react'
import FileUpload from './components/FileUpload'
import LogPreview from './components/LogPreview'
import SplitConfig from './components/SplitConfig'
import ResultList from './components/ResultList'

export interface AppState {
  fileId: string | null
  sessionId: string | null
  splitStatus: 'idle' | 'pending' | 'processing' | 'completed' | 'failed'
}

function App() {
  const [state, setState] = useState<AppState>({
    fileId: null,
    sessionId: null,
    splitStatus: 'idle',
  })

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
    setState({ fileId: null, sessionId: null, splitStatus: 'idle' })
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>LogFix AI</h1>
        <p>日志文件切分工具</p>
      </header>

      <main className="app-main">
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
      </main>
    </div>
  )
}

export default App
