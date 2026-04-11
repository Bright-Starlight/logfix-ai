import type { ClassificationProgressState } from '../hooks/useClassificationProgress'

interface ProgressBarProps {
  progress: ClassificationProgressState
  onRetry?: () => void
}

export default function ProgressBar({ progress, onRetry }: ProgressBarProps) {
  const {
    status,
    totalItems,
    processedItems,
    currentPhase,
    estimatedRemainingSeconds,
    progressPercent,
    error,
    result,
  } = progress

  const formatTime = (seconds: number | undefined): string => {
    if (seconds === undefined || seconds === null) return '--'
    if (seconds === 0) return '完成'
    if (seconds < 60) return `${seconds}秒`
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${minutes}分${secs}秒`
  }

  // Completed state
  if (status === 'completed' && result) {
    return (
      <div className="progress-bar-container completed">
        <div className="progress-header">
          <span className="progress-title">分类完成</span>
          <span className="progress-badge success">100%</span>
        </div>

        <div className="progress-summary">
          <div className="summary-item">
            <span className="summary-value">{result.new_entries}</span>
            <span className="summary-label">新增条目</span>
          </div>
          <div className="summary-item">
            <span className="summary-value">{result.duplicates}</span>
            <span className="summary-label">去重条目</span>
          </div>
          <div className="summary-item">
            <span className="summary-value">{result.ignored}</span>
            <span className="summary-label">忽略条目</span>
          </div>
        </div>
      </div>
    )
  }

  // Failed state
  if (status === 'failed') {
    return (
      <div className="progress-bar-container failed">
        <div className="progress-header">
          <span className="progress-title">分类失败</span>
          <span className="progress-badge error">失败</span>
        </div>

        <div className="progress-error">
          <p>{error || '处理过程中发生错误'}</p>
          {onRetry && (
            <button className="retry-button" onClick={onRetry}>
              重试
            </button>
          )}
        </div>
      </div>
    )
  }

  // Pending or Processing state
  return (
    <div className="progress-bar-container">
      <div className="progress-header">
        <span className="progress-title">
          {status === 'pending' ? '等待开始' : '处理中'}
        </span>
        <span className="progress-percent">{progressPercent}%</span>
      </div>

      <div className="progress-track">
        <div
          className="progress-fill"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <div className="progress-details">
        <div className="detail-row">
          <span className="detail-label">当前阶段</span>
          <span className="detail-value">{currentPhase || '准备中'}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">处理进度</span>
          <span className="detail-value">
            {processedItems} / {totalItems}
          </span>
        </div>
        <div className="detail-row">
          <span className="detail-label">预估剩余</span>
          <span className="detail-value">
            {formatTime(estimatedRemainingSeconds)}
          </span>
        </div>
      </div>

      {error && (
        <div className="progress-error">
          <p>{error}</p>
        </div>
      )}
    </div>
  )
}
