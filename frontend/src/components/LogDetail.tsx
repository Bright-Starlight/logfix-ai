import { useState, useEffect } from 'react'
import { getLogDetail } from '../services/api'
import type { LogDetailResponse } from '../types'

interface LogDetailProps {
  logId: string
  onBack?: () => void
}

export default function LogDetail({ logId, onBack }: LogDetailProps) {
  const [log, setLog] = useState<LogDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadLogDetail()
  }, [logId])

  const loadLogDetail = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await getLogDetail(logId)
      if (response.success && response.data) {
        setLog(response.data)
      } else {
        setError(response.error?.message || '加载失败')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '网络请求失败')
    } finally {
      setLoading(false)
    }
  }

  const getLevelColor = (level?: string) => {
    switch (level?.toUpperCase()) {
      case 'ERROR':
        return '#EF4444'
      case 'WARNING':
        return '#F59E0B'
      case 'INFO':
        return '#3B82F6'
      case 'DEBUG':
        return '#6B7280'
      case 'FATAL':
        return '#7F1D1D'
      default:
        return '#6B7280'
    }
  }

  if (loading) {
    return (
      <div className="log-detail-loading">
        <span>加载中...</span>
      </div>
    )
  }

  if (error || !log) {
    return (
      <div className="log-detail-error">
        <span>错误: {error || '日志不存在'}</span>
        <button onClick={onBack}>返回列表</button>
      </div>
    )
  }

  return (
    <div className="log-detail">
      <div className="log-detail-header">
        <button onClick={onBack} className="back-button">
          返回列表
        </button>
        <h2>日志详情</h2>
      </div>

      <div className="log-detail-content">
        <div className="detail-section">
          <h3>基本信息</h3>
          <div className="detail-row">
            <span className="detail-label">ID:</span>
            <span className="detail-value">{log.id}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">级别:</span>
            <span
              className="log-level-badge"
              style={{ backgroundColor: getLevelColor(log.log_level) }}
            >
              {log.log_level || 'UNKNOWN'}
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">分类:</span>
            <span className="detail-value">{log.category || '未分类'}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">错误类型:</span>
            <span className="detail-value">{log.error_type || '-'}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">发生次数:</span>
            <span className="detail-value">{log.occurrence_count}</span>
          </div>
        </div>

        <div className="detail-section">
          <h3>时间信息</h3>
          <div className="detail-row">
            <span className="detail-label">首次出现:</span>
            <span className="detail-value">
              {log.first_seen_at ? new Date(log.first_seen_at).toLocaleString() : '-'}
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">最后出现:</span>
            <span className="detail-value">
              {log.last_seen_at ? new Date(log.last_seen_at).toLocaleString() : '-'}
            </span>
          </div>
        </div>

        {log.original_message && (
          <div className="detail-section">
            <h3>原始消息</h3>
            <pre className="detail-message">{log.original_message}</pre>
          </div>
        )}

        <div className="detail-section">
          <h3>归一化消息</h3>
          <pre className="detail-message">{log.normalized_message}</pre>
        </div>

        {log.stack_trace && (
          <div className="detail-section">
            <h3>堆栈跟踪</h3>
            <pre className="detail-stack-trace">{log.stack_trace}</pre>
          </div>
        )}

        {log.extracted_params && Object.keys(log.extracted_params).length > 0 && (
          <div className="detail-section">
            <h3>提取的参数</h3>
            <pre className="detail-params">
              {JSON.stringify(log.extracted_params, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
