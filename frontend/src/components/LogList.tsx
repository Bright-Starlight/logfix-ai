import { useState, useEffect } from 'react'
import { getLogsList } from '../services/api'
import type { LogListItemResponse, LogListResponse } from '../types'
import type { SearchFilters } from './SearchFilter'

interface LogListProps {
  onLogSelect?: (logId: string) => void
  filters?: SearchFilters
}

export default function LogList({ onLogSelect, filters = {} }: LogListProps) {
  const [logs, setLogs] = useState<LogListItemResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)

  useEffect(() => {
    loadLogs()
  }, [page, filters])

  const loadLogs = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await getLogsList(page, pageSize, filters)
      if (response.success && response.data) {
        setLogs(response.data.entries)
        setTotal(response.data.total)
        setTotalPages(response.data.total_pages)
      } else {
        setError(response.error?.message || '加载失败')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '网络请求失败')
    } finally {
      setLoading(false)
    }
  }

  const handlePrevPage = () => {
    if (page > 1) setPage(page - 1)
  }

  const handleNextPage = () => {
    if (page < totalPages) setPage(page + 1)
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
      <div className="log-list-loading">
        <span>加载中...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="log-list-error">
        <span>错误: {error}</span>
        <button onClick={loadLogs}>重试</button>
      </div>
    )
  }

  return (
    <div className="log-list">
      <div className="log-list-header">
        <h2>日志列表</h2>
        <span className="log-count">共 {total} 条记录</span>
      </div>

      {logs.length === 0 ? (
        <div className="log-list-empty">
          <span>暂无日志数据</span>
        </div>
      ) : (
        <>
          <div className="log-list-items">
            {logs.map((log) => (
              <div
                key={log.id}
                className="log-list-item"
                onClick={() => onLogSelect?.(log.id)}
              >
                <div className="log-item-header">
                  <span
                    className="log-level-badge"
                    style={{ backgroundColor: getLevelColor(log.log_level) }}
                  >
                    {log.log_level || 'UNKNOWN'}
                  </span>
                  <span className="log-category">{log.category || '未分类'}</span>
                  <span className="log-occurrence">
                    ×{log.occurrence_count}
                  </span>
                </div>
                <div className="log-item-message">
                  {log.normalized_message}
                </div>
                {log.error_type && (
                  <div className="log-item-error-type">
                    {log.error_type}
                  </div>
                )}
                <div className="log-item-time">
                  首次: {log.first_seen_at ? new Date(log.first_seen_at).toLocaleString() : '-'}
                </div>
              </div>
            ))}
          </div>

          <div className="log-list-pagination">
            <button onClick={handlePrevPage} disabled={page <= 1}>
              上一页
            </button>
            <span className="page-info">
              第 {page} / {totalPages} 页
            </span>
            <button onClick={handleNextPage} disabled={page >= totalPages}>
              下一页
            </button>
          </div>
        </>
      )}
    </div>
  )
}
