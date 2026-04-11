import { useState, useEffect, useCallback, useRef } from 'react'
import { getClassificationProgress, getClassificationResult } from '../services/api'
import type { ClassificationResultResponse } from '../types'

export type ClassificationStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface ClassificationProgressState {
  status: ClassificationStatus
  totalItems: number
  processedItems: number
  currentPhase: string | undefined
  estimatedRemainingSeconds: number | undefined
  progressPercent: number
  result: ClassificationResultResponse | null
  error: string | null
}

const POLLING_INTERVAL = 2000 // 2 seconds

export function useClassificationProgress(sessionId: string | null) {
  const [state, setState] = useState<ClassificationProgressState>({
    status: 'pending',
    totalItems: 0,
    processedItems: 0,
    currentPhase: undefined,
    estimatedRemainingSeconds: undefined,
    progressPercent: 0,
    result: null,
    error: null,
  })

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const isMountedRef = useRef(true)

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  const fetchProgress = useCallback(async () => {
    if (!sessionId) return

    try {
      const response = await getClassificationProgress(sessionId)

      if (!isMountedRef.current) return

      if (response.success && response.data) {
        const data = response.data
        setState((prev) => ({
          ...prev,
          status: data.status as ClassificationStatus,
          totalItems: data.total_items,
          processedItems: data.processed_items,
          currentPhase: data.current_phase,
          estimatedRemainingSeconds: data.estimated_remaining_seconds,
          progressPercent: data.progress_percent,
          error: null,
        }))

        // Stop polling if completed or failed
        if (data.status === 'completed' || data.status === 'failed') {
          stopPolling()

          // Fetch final result if completed
          if (data.status === 'completed') {
            try {
              const resultResponse = await getClassificationResult(sessionId)
              if (isMountedRef.current && resultResponse.success && resultResponse.data) {
                setState((prev) => ({
                  ...prev,
                  result: resultResponse.data,
                }))
              }
            } catch {
              // Result fetch is optional, ignore errors
            }
          }
        }
      } else if (response.error) {
        setState((prev) => ({
          ...prev,
          error: response.error?.message || '获取进度失败',
        }))
        stopPolling()
      }
    } catch (err) {
      if (!isMountedRef.current) return

      setState((prev) => ({
        ...prev,
        error: err instanceof Error ? err.message : '获取进度失败',
      }))
      stopPolling()
    }
  }, [sessionId, stopPolling])

  // Start polling when sessionId is provided and status is pending or processing
  useEffect(() => {
    if (!sessionId) {
      setState({
        status: 'pending',
        totalItems: 0,
        processedItems: 0,
        currentPhase: undefined,
        estimatedRemainingSeconds: undefined,
        progressPercent: 0,
        result: null,
        error: null,
      })
      stopPolling()
      return
    }

    isMountedRef.current = true

    // Fetch immediately
    fetchProgress()

    // Start polling
    pollingRef.current = setInterval(fetchProgress, POLLING_INTERVAL)

    return () => {
      isMountedRef.current = false
      stopPolling()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  // Manual refresh function
  const refresh = useCallback(() => {
    if (sessionId) {
      fetchProgress()
    }
  }, [sessionId, fetchProgress])

  return {
    ...state,
    refresh,
    isPolling: pollingRef.current !== null,
  }
}
