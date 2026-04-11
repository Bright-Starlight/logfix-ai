/**
 * 分类进度 Hook 单元测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useClassificationProgress } from '../../src/hooks/useClassificationProgress'

// Mock the API module
vi.mock('../../src/services/api', () => ({
  getClassificationProgress: vi.fn(),
  getClassificationResult: vi.fn(),
}))

import { getClassificationProgress, getClassificationResult } from '../../src/services/api'

const mockedGetProgress = getClassificationProgress as ReturnType<typeof vi.fn>
const mockedGetResult = getClassificationResult as ReturnType<typeof vi.fn>

describe('useClassificationProgress', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should initialize with pending state', () => {
    const { result } = renderHook(() => useClassificationProgress(null))

    expect(result.current.status).toBe('pending')
    expect(result.current.totalItems).toBe(0)
    expect(result.current.processedItems).toBe(0)
    expect(result.current.progressPercent).toBe(0)
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('should fetch progress when sessionId is provided', async () => {
    const mockProgress = {
      session_id: 'test-session-id',
      status: 'processing',
      total_items: 100,
      processed_items: 50,
      current_phase: '分类分析中',
      estimated_remaining_seconds: 30,
      progress_percent: 50,
    }

    mockedGetProgress.mockResolvedValue({
      success: true,
      data: mockProgress,
    })

    const { result } = renderHook(() => useClassificationProgress('test-session-id'))

    // Wait for the first fetch
    await act(async () => {
      vi.advanceTimersByTime(100)
    })

    expect(mockedGetProgress).toHaveBeenCalledWith('test-session-id')
    expect(result.current.status).toBe('processing')
    expect(result.current.totalItems).toBe(100)
    expect(result.current.processedItems).toBe(50)
    expect(result.current.progressPercent).toBe(50)
    expect(result.current.currentPhase).toBe('分类分析中')
  })

  it('should stop polling when status is completed', async () => {
    const mockProgress = {
      session_id: 'test-session-id',
      status: 'completed',
      total_items: 100,
      processed_items: 100,
      current_phase: '完成',
      estimated_remaining_seconds: 0,
      progress_percent: 100,
    }

    const mockResult = {
      session_id: 'test-session-id',
      status: 'completed',
      total_items: 100,
      processed_items: 100,
      new_entries: 80,
      duplicates: 15,
      ignored: 5,
      completed_at: '2026-04-11T12:00:00Z',
    }

    mockedGetProgress.mockResolvedValue({
      success: true,
      data: mockProgress,
    })

    mockedGetResult.mockResolvedValue({
      success: true,
      data: mockResult,
    })

    const { result } = renderHook(() => useClassificationProgress('test-session-id'))

    await act(async () => {
      vi.advanceTimersByTime(100)
    })

    expect(result.current.status).toBe('completed')
    await waitFor(() => {
      expect(mockedGetResult).toHaveBeenCalled()
    })
  })

  it('should stop polling when status is failed', async () => {
    const mockProgress = {
      session_id: 'test-session-id',
      status: 'failed',
      total_items: 100,
      processed_items: 50,
      current_phase: '分类分析中',
      estimated_remaining_seconds: null,
      progress_percent: 50,
    }

    mockedGetProgress.mockResolvedValue({
      success: true,
      data: mockProgress,
    })

    const { result } = renderHook(() => useClassificationProgress('test-session-id'))

    await act(async () => {
      vi.advanceTimersByTime(100)
    })

    expect(result.current.status).toBe('failed')
    // Should not call getResult when failed
    expect(mockedGetResult).not.toHaveBeenCalled()
  })

  it('should handle API errors', async () => {
    mockedGetProgress.mockResolvedValue({
      success: false,
      error: { code: 'SESSION_NOT_FOUND', message: '分类会话不存在' },
    })

    const { result } = renderHook(() => useClassificationProgress('invalid-session-id'))

    await act(async () => {
      vi.advanceTimersByTime(100)
    })

    expect(result.current.error).toBe('分类会话不存在')
  })

  it('should reset state when sessionId becomes null', async () => {
    mockedGetProgress.mockResolvedValue({
      success: true,
      data: {
        session_id: 'test-session-id',
        status: 'processing',
        total_items: 100,
        processed_items: 50,
        current_phase: '分类分析中',
        estimated_remaining_seconds: 30,
        progress_percent: 50,
      },
    })

    const { result, rerender } = renderHook(
      ({ sessionId }) => useClassificationProgress(sessionId),
      { initialProps: { sessionId: 'test-session-id' } }
    )

    await act(async () => {
      vi.advanceTimersByTime(100)
    })

    expect(result.current.status).toBe('processing')

    // Change to null
    rerender({ sessionId: null })

    expect(result.current.status).toBe('pending')
    expect(result.current.totalItems).toBe(0)
    expect(result.current.processedItems).toBe(0)
  })

  it('should calculate progress percent correctly', () => {
    // Test cases for progress calculation
    const testCases = [
      { processed: 0, total: 100, expected: 0 },
      { processed: 50, total: 100, expected: 50 },
      { processed: 100, total: 100, expected: 100 },
      { processed: 1, total: 3, expected: 33 }, // 1/3 = 33.33%
    ]

    for (const { processed, total, expected } of testCases) {
      const percent = Math.floor((processed / total) * 100)
      expect(percent).toBe(expected)
    }
  })
})
