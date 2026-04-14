import { useState, useCallback, useRef, useEffect } from 'react'
import type {
  AnalysisSSEProgressEvent,
  AnalysisSSEErrorEvent,
  SSEFixPlanEvent,
} from '../types'

interface UseAnalysisProgressOptions {
  onProgress?: (data: AnalysisSSEProgressEvent) => void
  onResult?: (data: SSEFixPlanEvent) => void
  onError?: (data: AnalysisSSEErrorEvent) => void
  onQueued?: (data: AnalysisSSEProgressEvent) => void
}

interface UseAnalysisProgressReturn {
  isConnected: boolean
  isQueued: boolean
  queuePosition: number | null
  progress: AnalysisSSEProgressEvent | null
  result: SSEFixPlanEvent | null
  error: AnalysisSSEErrorEvent | null
  startStream: (sessionId: string) => void
  cancel: () => void
}

export function useAnalysisProgress(
  options: UseAnalysisProgressOptions = {}
): UseAnalysisProgressReturn {
  const { onProgress, onResult, onError, onQueued } = options

  const [isConnected, setIsConnected] = useState(false)
  const [isQueued, setIsQueued] = useState(false)
  const [queuePosition, setQueuePosition] = useState<number | null>(null)
  const [progress, setProgress] = useState<AnalysisSSEProgressEvent | null>(null)
  const [result, setResult] = useState<SSEFixPlanEvent | null>(null)
  const [error, setError] = useState<AnalysisSSEErrorEvent | null>(null)

  const eventSourceRef = useRef<EventSource | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const cancel = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsConnected(false)
    setIsQueued(false)
    setQueuePosition(null)
  }, [])

  const startStream = useCallback(
    (sessionId: string) => {
      // 清理之前的连接
      cancel()

      // 重置状态
      setProgress(null)
      setResult(null)
      setError(null)
      setIsQueued(false)
      setQueuePosition(null)

      // 使用 fetch + ReadableStream 来处理 SSE（支持通过sessionId获取数据）
      abortControllerRef.current = new AbortController()

      const fetchSSE = async () => {
        try {
          setIsConnected(true)

          const response = await fetch(`/api/analysis/stream/${sessionId}`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
            signal: abortControllerRef.current?.signal,
          })

          if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`)
          }

          const reader = response.body?.getReader()
          if (!reader) {
            throw new Error('No response body')
          }

          const decoder = new TextDecoder()
          let buffer = ''
          let currentEvent = ''
          let currentData = ''

          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            buffer += decoder.decode(value, { stream: true })

            // 按 SSE 格式解析（event: xxx\ndata: yyy\n\n）
            const eventMatch = buffer.match(/^event: (\w+)\n/m)
            if (eventMatch) {
              currentEvent = eventMatch[1]
            }

            // 匹配 data: 内容（直到双换行或字符串结尾）
            const dataMatch = buffer.match(/^data: (.+?)\n\n/ms)
            if (dataMatch) {
              currentData = dataMatch[1]
              buffer = buffer.slice(dataMatch[0].length)

              try {
                const parsedData = JSON.parse(currentData)

                if (currentEvent === 'queued') {
                  setIsQueued(true)
                  setQueuePosition(parsedData.queue_position)
                  onQueued?.(parsedData)
                } else if (currentEvent === 'progress') {
                  setProgress(parsedData)
                  onProgress?.(parsedData)
                } else if (currentEvent === 'result' && parsedData.root_cause !== undefined) {
                  setResult(parsedData)
                  onResult?.(parsedData)
                } else if (currentEvent === 'error') {
                  setError(parsedData)
                  onError?.(parsedData)
                }
              } catch {
                // Ignore parse errors for incomplete data
              }

              // Reset
              currentEvent = ''
              currentData = ''
            }
          }
        } catch (err) {
          if ((err as Error).name === 'AbortError') {
            // Cancelled
          } else {
            setError({
              code: 'NETWORK_ERROR',
              message: (err as Error).message || 'Network error',
            })
            onError?.({
              code: 'NETWORK_ERROR',
              message: (err as Error).message || 'Network error',
            })
          }
        } finally {
          setIsConnected(false)
          setIsQueued(false)
        }
      }

      fetchSSE()
    },
    [cancel, onProgress, onResult, onError, onQueued]
  )

  // 清理 on unmount
  useEffect(() => {
    return () => {
      cancel()
    }
  }, [cancel])

  return {
    isConnected,
    isQueued,
    queuePosition,
    progress,
    result,
    error,
    startStream,
    cancel,
  }
}
