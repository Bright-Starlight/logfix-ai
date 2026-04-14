import { useState, useCallback, useEffect } from 'react'
import { analysisApi } from '../services/api'
import type { QueueStatusResponse } from '../types'

interface UseAnalysisQueueReturn {
  queueStatus: QueueStatusResponse | null
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export function useAnalysisQueue(): UseAnalysisQueueReturn {
  const [queueStatus, setQueueStatus] = useState<QueueStatusResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await analysisApi.getQueueStatus()
      if (response.success && response.data) {
        setQueueStatus(response.data)
      } else {
        setError(response.error?.message || '获取队列状态失败')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '网络请求失败')
    } finally {
      setLoading(false)
    }
  }, [])

  // 定期刷新队列状态
  useEffect(() => {
    refresh()

    const interval = setInterval(refresh, 5000) // 每5秒刷新一次

    return () => clearInterval(interval)
  }, [refresh])

  return {
    queueStatus,
    loading,
    error,
    refresh,
  }
}
