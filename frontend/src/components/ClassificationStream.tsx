import { useState, useCallback, useEffect } from 'react'
import { useClassificationProgress } from '../hooks/useClassificationProgress'
import type { SessionListItem } from '../types'

interface ClassificationStreamProps {
  sessions: SessionListItem[]
  onComplete?: () => void
  onCancel?: () => void
}

export default function ClassificationStream({
  sessions,
  onComplete,
  onCancel,
}: ClassificationStreamProps) {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [isStarted, setIsStarted] = useState(false)

  const {
    isConnected,
    progress,
    results,
    error,
    done,
    startStream,
    cancel,
  } = useClassificationProgress()

  // 监听完成状态
  useEffect(() => {
    if (done && onComplete) {
      onComplete()
    }
  }, [done, onComplete])

  // 监听取消状态
  useEffect(() => {
    if (!isConnected && isStarted && !done && !error) {
      // 用户取消
      if (onCancel) {
        onCancel()
      }
    }
  }, [isConnected, isStarted, done, error, onCancel])

  const handleStartClassification = useCallback(() => {
    if (!selectedSessionId) return

    const session = sessions.find((s) => s.id === selectedSessionId)
    if (!session) return

    setIsStarted(true)
    startStream({
      split_session_id: session.id,
      mode: 'ai',
    })
  }, [selectedSessionId, sessions, startStream])

  const handleCancel = useCallback(() => {
    cancel()
    setIsStarted(false)
  }, [cancel])

  const getLevelColor = (category?: string) => {
    switch (category) {
      case '异常错误':
        return '#EF4444'
      case '警告':
        return '#F59E0B'
      case '信息':
        return '#3B82F6'
      case '调试':
        return '#6B7280'
      case '致命错误':
        return '#7F1D1D'
      default:
        return '#6B7280'
    }
  }

  // 未开始状态：显示会话选择
  if (!isStarted) {
    const completedSessions = sessions.filter(
      (s) => s.status === 'completed' && !s.has_classification
    )

    return (
      <div className="classification-stream">
        <div className="classification-header">
          <h2>AI 结构化</h2>
        </div>

        <div className="classification-select">
          <label htmlFor="session-select">选择切分会话：</label>
          <select
            id="session-select"
            value={selectedSessionId || ''}
            onChange={(e) => setSelectedSessionId(e.target.value || null)}
            className="session-select"
          >
            <option value="">-- 请选择 --</option>
            {completedSessions.length === 0 ? (
              <option value="" disabled>
                暂无可分类的会话（请先进行切分）
              </option>
            ) : (
              completedSessions.map((session) => (
                <option key={session.id} value={session.id}>
                  {session.rule_content} ({session.total_chunks} 条) -{' '}
                  {new Date(session.created_at).toLocaleString()}
                </option>
              ))
            )}
          </select>
        </div>

        <div className="classification-actions">
          <button
            onClick={handleStartClassification}
            disabled={!selectedSessionId}
            className="start-classify-button"
          >
            开始 AI 结构化
          </button>
        </div>

        {completedSessions.length === 0 && sessions.length === 0 && (
          <div className="classification-empty">
            <p>暂无切分会话</p>
            <p className="hint">请先在"日志切分"标签页上传文件并进行切分</p>
          </div>
        )}
      </div>
    )
  }

  // 进行中/完成状态：显示进度和结果
  return (
    <div className="classification-stream">
      <div className="classification-header">
        <h2>AI 结构化进度</h2>
        {isConnected && (
          <button onClick={handleCancel} className="cancel-button">
            取消
          </button>
        )}
      </div>

      {/* 进度条 */}
      <div className="classification-progress">
        <div className="progress-info">
          {progress ? (
            <>
              <span>
                已处理: {progress.processed} / {progress.total}
              </span>
              <span className="percentage">{progress.percentage}%</span>
            </>
          ) : (
            <span>准备中...</span>
          )}
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress?.percentage || 0}%` }}
          />
        </div>
      </div>

      {/* 实时结果列表 */}
      <div className="classification-results">
        <h3>实时结果 ({results.length})</h3>
        <div className="results-list">
          {results.slice(-10).map((result, index) => (
            <div key={index} className="result-item">
              <span
                className="result-category"
                style={{ backgroundColor: getLevelColor(result.category) }}
              >
                {result.category}
              </span>
              <span className="result-message">
                {result.normalized_message.slice(0, 80)}
                {result.normalized_message.length > 80 ? '...' : ''}
              </span>
              {result.error_type && (
                <span className="result-error-type">{result.error_type}</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 完成状态 */}
      {done && (
        <div className="classification-done">
          <h3>处理完成</h3>
          <div className="done-stats">
            <span>总处理: {done.total_processed}</span>
            <span>成功: {done.success_count}</span>
            <span>失败: {done.error_count}</span>
          </div>
        </div>
      )}

      {/* 错误状态 */}
      {error && (
        <div className="classification-error">
          <h3>处理错误</h3>
          <p>
            {error.code}: {error.message}
          </p>
          <button
            onClick={() => {
              setIsStarted(false)
              setSelectedSessionId(null)
            }}
            className="retry-button"
          >
            重新选择
          </button>
        </div>
      )}
    </div>
  )
}
