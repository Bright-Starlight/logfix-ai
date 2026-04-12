import { useState } from 'react'
import RepoImport, { type RepoInfo } from './components/RepoImport'
import FileUpload from './components/FileUpload'
import LogPreview from './components/LogPreview'
import SplitConfig from './components/SplitConfig'
import ResultList from './components/ResultList'
import LogList from './components/LogList'
import LogDetail from './components/LogDetail'
import SearchFilter, { type SearchFilters } from './components/SearchFilter'
import StatsPanel from './components/StatsPanel'
import IgnoreRuleManager from './components/IgnoreRuleManager'

type PipelineStep = 'repo' | 'upload' | 'split' | 'classify' | 'results'
type SplitStatus = 'idle' | 'processing' | 'completed' | 'failed'

interface StepDef {
  id: PipelineStep
  label: string
  sublabel: string
}

const STEPS: StepDef[] = [
  { id: 'repo',     label: '仓库导入', sublabel: '选择仓库来源' },
  { id: 'upload',   label: '日志上传', sublabel: '选择日志文件' },
  { id: 'split',    label: '日志切分', sublabel: '按规则切片' },
  { id: 'classify', label: '日志分类', sublabel: 'AI 自动归类' },
  { id: 'results',  label: '分析结果', sublabel: '查看统计详情' },
]

const STEP_ORDER: PipelineStep[] = ['repo', 'upload', 'split', 'classify', 'results']

function stepIndex(step: PipelineStep) {
  return STEP_ORDER.indexOf(step)
}

function stepStatus(current: PipelineStep, target: PipelineStep): 'done' | 'active' | 'pending' | 'disabled' {
  const ci = stepIndex(current)
  const ti = stepIndex(target)
  if (ti < ci) return 'done'
  if (ti === ci) return 'active'
  return 'disabled'
}

// SVG icons
function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="step-check">
      <path d="M5 13l4 4L19 7" />
    </svg>
  )
}

function LogoIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <line x1="10" y1="9" x2="8" y2="9" />
    </svg>
  )
}

function ResetIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="13" height="13">
      <path d="M3 12a9 9 0 109-9M3 12V7M3 12H8" />
    </svg>
  )
}

export default function App() {
  const [currentStep, setCurrentStep] = useState<PipelineStep>('repo')
  const [repo, setRepo] = useState<RepoInfo | null>(null)
  const [fileId, setFileId] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [splitStatus, setSplitStatus] = useState<SplitStatus>('idle')
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null)
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({})
  const [showIgnoreRules, setShowIgnoreRules] = useState(false)

  // ── Handlers ──────────────────────────────────────────────
  const handleRepoImported = (repoInfo: RepoInfo) => {
    setRepo(repoInfo)
    setCurrentStep('upload')
  }

  const handleFileUploaded = (uploadedFileId: string) => {
    setFileId(uploadedFileId)
    setSessionId(null)
    setSplitStatus('idle')
    setCurrentStep('split')
  }

  const handleSplitStarted = (splitSessionId: string) => {
    setSessionId(splitSessionId)
    setSplitStatus('processing')
  }

  const handleSplitCompleted = () => {
    setSplitStatus('completed')
  }

  const handleReset = () => {
    setRepo(null)
    setFileId(null)
    setSessionId(null)
    setSplitStatus('idle')
    setSelectedLogId(null)
    setSearchFilters({})
    setShowIgnoreRules(false)
    setCurrentStep('repo')
  }

  const handleStepClick = (step: PipelineStep) => {
    const status = stepStatus(currentStep, step)
    if (status === 'done') {
      setCurrentStep(step)
    }
  }

  // ── Page Header ────────────────────────────────────────────
  const pageMeta: Record<PipelineStep, { title: string; subtitle: string }> = {
    repo:     { title: '仓库导入', subtitle: '选择需要分析的代码仓库' },
    upload:   { title: '日志上传', subtitle: `当前仓库：${repo?.name ?? '—'}` },
    split:    { title: '日志切分', subtitle: '配置切分规则，提取结构化日志片段' },
    classify: { title: '日志分类', subtitle: 'AI 自动对切分结果进行分类归档' },
    results:  { title: '分析结果', subtitle: '查看日志统计与详情' },
  }

  const meta = pageMeta[currentStep]

  return (
    <div className="app-shell">
      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">
            <LogoIcon />
          </div>
          <span className="sidebar-brand-name">LogFix AI</span>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section-label">流水线</div>
          <div className="pipeline-steps">
            {STEPS.map((step, idx) => {
              const status = stepStatus(currentStep, step.id)
              const clickable = status === 'done'
              return (
                <div
                  key={step.id}
                  className={[
                    'step-item',
                    status === 'active' ? 'step-active' : '',
                    status === 'done' ? 'step-done' : '',
                    status === 'disabled' ? 'step-disabled' : '',
                  ].filter(Boolean).join(' ')}
                  onClick={() => clickable && handleStepClick(step.id)}
                  role={clickable ? 'button' : undefined}
                  tabIndex={clickable ? 0 : undefined}
                  onKeyDown={(e) => { if (e.key === 'Enter' && clickable) handleStepClick(step.id) }}
                >
                  <div className="step-icon-wrap">
                    {status === 'done' ? (
                      <CheckIcon />
                    ) : (
                      <span className="step-number">{idx + 1}</span>
                    )}
                  </div>
                  <div className="step-text">
                    <span className="step-label">{step.label}</span>
                    <span className="step-sublabel">{step.sublabel}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </nav>

        <div className="sidebar-footer">
          <button className="btn-reset" onClick={handleReset}>
            <ResetIcon />
            重置流程
          </button>
        </div>
      </aside>

      {/* ── Main ─────────────────────────────────────────────── */}
      <div className="main-content">
        <div className="page-header">
          <div className="page-title">{meta.title}</div>
          <div className="page-subtitle">{meta.subtitle}</div>
        </div>

        <div className="page-body">
          {/* Step: Repo Import */}
          {currentStep === 'repo' && (
            <RepoImport onRepoImported={handleRepoImported} />
          )}

          {/* Step: Upload */}
          {currentStep === 'upload' && (
            <FileUpload onFileUploaded={handleFileUploaded} />
          )}

          {/* Step: Split */}
          {currentStep === 'split' && fileId && (
            <>
              {splitStatus === 'idle' && (
                <>
                  <LogPreview fileId={fileId} />
                  <SplitConfig fileId={fileId} onSplitStarted={handleSplitStarted} />
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
                    <button
                      className="btn btn-secondary"
                      onClick={() => setSplitStatus('idle')}
                    >
                      重新切分
                    </button>
                    <div className="pipeline-actions-right">
                      <button
                        className="btn btn-primary btn-lg"
                        onClick={() => setCurrentStep('classify')}
                      >
                        继续分类
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ width: 14, height: 14 }}>
                          <path d="M5 12h14M12 5l7 7-7 7" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </>
              )}
            </>
          )}

          {/* Step: Classify */}
          {currentStep === 'classify' && sessionId && (
            <>
              <ResultList sessionId={sessionId} />
              <div className="pipeline-actions">
                <div className="pipeline-actions-right">
                  <button
                    className="btn btn-primary btn-lg"
                    onClick={() => setCurrentStep('results')}
                  >
                    查看结果
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ width: 14, height: 14 }}>
                      <path d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Step: Results */}
          {currentStep === 'results' && (
            <>
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--c-text-1)' }}>忽略规则</div>
                  <button
                    className="btn btn-secondary"
                    onClick={() => setShowIgnoreRules(!showIgnoreRules)}
                  >
                    {showIgnoreRules ? '收起' : '配置忽略规则'}
                  </button>
                </div>

                {showIgnoreRules && (
                  <div style={{ marginTop: 'var(--sp-5)' }}>
                    <IgnoreRuleManager />
                  </div>
                )}
              </div>

              {selectedLogId ? (
                <LogDetail
                  logId={selectedLogId}
                  onBack={() => setSelectedLogId(null)}
                />
              ) : (
                <>
                  <StatsPanel />
                  <SearchFilter onSearch={setSearchFilters} />
                  <div className="card">
                    <LogList
                      onLogSelect={setSelectedLogId}
                      filters={searchFilters}
                    />
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
