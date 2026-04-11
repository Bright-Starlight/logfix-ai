import { useState, useCallback, useRef, useEffect } from 'react'
import type {
  SSEProgressEvent,
  SSEResultEvent,
  SSEErrorEvent,
  SSEDoneEvent,
  ClassificationStartRequest,
} from '../types'

interface UseClassificationProgressOptions {
  onProgress?: (data: SSEProgressEvent) => void
  onResult?: (data: SSEResultEvent) => void
  onError?: (data: SSEErrorEvent) => void
  onDone?: (data: SSEDoneEvent) => void
}

interface UseClassificationProgressReturn {
  isConnected: boolean
  progress: SSEProgressEvent | null
  results: SSEResultEvent[]
  error: SSEErrorEvent | null
  done: SSEDoneEvent | null
  startStream: (request: ClassificationStartRequest) => void
  cancel: () => void
}

export function useClassificationProgress(
  options: UseClassificationProgressOptions = {}
): UseClassificationProgressReturn {
  const { onProgress, onResult, onError, onDone } = options

  const [isConnected, setIsConnected] = useState(false)
  const [progress, setProgress] = useState<SSEProgressEvent | null>(null)
  const [results, setResults] = useState<SSEResultEvent[]>([])
  const [error, setError] = useState<SSEErrorEvent | null>(null)
  const [done, setDone] = useState<SSEDoneEvent | null>(null)

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
  }, [])

  const startStream = useCallback(
    (request: ClassificationStartRequest) => {
      // 清理之前的连接
      cancel()

      // 重置状态
      setProgress(null)
      setResults([])
      setError(null)
      setDone(null)

      // 创建 EventSource
      // 注意：EventSource 不支持 POST 请求，我们使用 fetch + ReadableStream
      abortControllerRef.current = new AbortController()

      const fetchSSE = async () => {
        try {
          setIsConnected(true)

          const response = await fetch('/api/classify/stream', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
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
            // 匹配 event: 类型
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

                if (currentEvent === 'progress' && parsedData.processed !== undefined) {
                  setProgress(parsedData)
                  onProgress?.(parsedData)
                } else if (currentEvent === 'result' && parsedData.index !== undefined) {
                  setResults((prev) => [...prev, parsedData])
                  onResult?.(parsedData)
                } else if (currentEvent === 'error') {
                  setError(parsedData)
                  onError?.(parsedData)
                } else if (currentEvent === 'done') {
                  setDone(parsedData)
                  onDone?.(parsedData)
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
        }
      }

      fetchSSE()
    },
    [cancel, onProgress, onResult, onError, onDone]
  )

  // 清理 on unmount
  useEffect(() => {
    return () => {
      cancel()
    }
  }, [cancel])

  return {
    isConnected,
    progress,
    results,
    error,
    done,
    startStream,
    cancel,
  }
}
