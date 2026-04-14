import { useState, useEffect, useCallback, useMemo } from 'react'
import { getLogsList, analysisApi } from '../services/api'
import { useAnalysisProgress } from '../hooks/useAnalysisProgress'
import FixPlanViewer from './FixPlanViewer'
import type { LogListItemResponse, AnalysisStatus, FixPlanData, LogDetailResponse } from '../types'
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

  // 分析相关状态
  const [analysisStatuses, setAnalysisStatuses] = useState<Record<string, AnalysisStatus>>({})
  const [analyzingLogs, setAnalyzingLogs] = useState<Record<string, { sessionId: string; queuePosition?: number }>>({})
  const [fixPlans, setFixPlans] = useState<Record<string, FixPlanData>>({})
  const [viewingFixPlan, setViewingFixPlan] = useState<FixPlanData | null>(null)

  // SSE 流状态
  const { startStream, isConnected, isQueued, queuePosition, result, error: streamError } = useAnalysisProgress({
    onResult: (data) => {
      if (data.log_entry_id) {
        setFixPlans((prev) => ({ ...prev, [data.log_entry_id]: data as FixPlanData }))
        setAnalysisStatuses((prev) => ({ ...prev, [data.log_entry_id]: 'completed' }))
      }
    },
    onError: (data) => {
      if (data.log_entry_id) {
        setAnalysisStatuses((prev) => ({ ...prev, [data.log_entry_id]: 'failed' }))
      }
    },
    onQueued: (data) => {
      if (data.log_entry_id) {
        setAnalyzingLogs((prev) => ({
          ...prev,
          [data.log_entry_id]: {
            ...prev[data.log_entry_id],
            queuePosition: data.queue_position,
          },
        }))
      }
    },
  })

  // 将 filters 序列化为字符串作为依赖
  const filtersKey = useMemo(
    () => JSON.stringify(filters),
    [filters]
  )

  // filters 变化时重置页码到第1页
  useEffect(() => {
    setPage(1)
  }, [filtersKey])

  const loadLogs = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await getLogsList(page, pageSize, filters)
      if (response.success && response.data) {
        setLogs(response.data.entries)
        setTotal(response.data.total)
        setTotalPages(response.data.total_pages)

        // 获取每条日志的分析状态 (并行请求)
        const statusPromises = response.data.entries.map(entry =>
          analysisApi.getFixPlan(parseInt(entry.id)).catch(() => null)
        )
        const statusResults = await Promise.all(statusPromises)

        const newStatuses: Record<string, AnalysisStatus> = {}
        const newFixPlans: Record<string, FixPlanData> = {}
        statusResults.forEach((result, index) => {
          const entry = response.data.entries[index]
          if (result?.success && result.data) {
            newStatuses[entry.id] = result.data.status as AnalysisStatus
            if (result.data.fix_plan) {
              newFixPlans[entry.id] = result.data.fix_plan as FixPlanData
            }
          }
        })
        if (Object.keys(newStatuses).length > 0) {
          setAnalysisStatuses(prev => ({ ...prev, ...newStatuses }))
        }
        if (Object.keys(newFixPlans).length > 0) {
          setFixPlans(prev => ({ ...prev, ...newFixPlans }))
        }
      } else {
        setError(response.error?.message || '加载失败')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '网络请求失败')
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, filters])

  useEffect(() => {
    loadLogs()
  }, [loadLogs, filtersKey])

  // 启动分析
  const handleStartAnalysis = async (logId: string) => {
    try {
      const response = await analysisApi.start(parseInt(logId))
      if (response.success && response.data) {
        setAnalysisStatuses((prev) => ({ ...prev, [logId]: 'analyzing' }))
        setAnalyzingLogs((prev) => ({
          ...prev,
          [logId]: {
            sessionId: response.data!.session_id,
            queuePosition: response.data!.queue_position,
          },
        }))
        // 开始 SSE 流
        startStream(response.data.session_id)
      } else if (response.error?.code === 'QUEUE_FULL') {
        alert('队列已满，请稍后再试')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '启动分析失败')
    }
  }

  // 查看修复计划
  const handleViewFixPlan = async (logId: string) => {
    try {
      const response = await analysisApi.getFixPlan(parseInt(logId))
      if (response.success && response.data?.fix_plan) {
        setViewingFixPlan(response.data.fix_plan)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取修复计划失败')
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

  const getAnalysisStatusTag = (logId: string) => {
    const status = analysisStatuses[logId]
    const analyzing = analyzingLogs[logId]

    if (status === 'completed') {
      return <span className="analysis-tag completed">分析完成</span>
    }
    if (status === 'failed') {
      return <span className="analysis-tag failed">分析失败</span>
    }
    if (status === 'analyzing' || analyzing) {
      if (isQueued && analyzing?.queuePosition) {
        return <span className="analysis-tag queued">排队中(#{analyzing.queuePosition})</span>
      }
      return <span className="analysis-tag analyzing">分析中</span>
    }
    return <span className="analysis-tag un_analyzed">未分析</span>
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
                  {getAnalysisStatusTag(log.id)}
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
                <div className="log-item-actions">
                  {analysisStatuses[log.id] === 'completed' ? (
                    <button
                      className="btn-view-fix-plan"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleViewFixPlan(log.id)
                      }}
                    >
                      查看修复计划
                    </button>
                  ) : (analysisStatuses[log.id] === 'un_analyzed' || analysisStatuses[log.id] === 'failed') ? (
                    <button
                      className="btn-start-analysis"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleStartAnalysis(log.id)
                      }}
                      disabled={analysisStatuses[log.id] === 'analyzing'}
                    >
                      {analysisStatuses[log.id] === 'analyzing' ? '分析中...' : '生成修复计划'}
                    </button>
                  ) : null}
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

      {/* 修复计划查看弹窗 */}
      {viewingFixPlan && (
        <div className="fix-plan-modal" onClick={() => setViewingFixPlan(null)}>
          <div className="fix-plan-modal-content" onClick={(e) => e.stopPropagation()}>
            <FixPlanViewer fixPlan={viewingFixPlan} onClose={() => setViewingFixPlan(null)} />
          </div>
        </div>
      )}
    </div>
  )
}
