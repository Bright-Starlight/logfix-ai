import { useState, useEffect } from 'react'
import { getSplitResults, getChunkDetail, startClassification, getClassificationProgress, getClassificationResult } from '../services/api'
import ClassificationModeSelect from './ClassificationModeSelect'
import ProgressBar from './ProgressBar'
import type { ResultsResponse, SplitResult, ClassificationMode, ClassificationProgressState } from '../types'

interface ResultListProps {
  sessionId: string
}

export default function ResultList({ sessionId }: ResultListProps) {
  const [results, setResults] = useState<ResultsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedChunk, setSelectedChunk] = useState<SplitResult | null>(null)
  const [chunkContent, setChunkContent] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)

  // Classification state
  const [classificationSessionId, setClassificationSessionId] = useState<string | null>(null)
  const [isClassifying, setIsClassifying] = useState(false)
  const [showModeSelect, setShowModeSelect] = useState(true)
  const [classificationError, setClassificationError] = useState<string | null>(null)
  const [classificationProgress, setClassificationProgress] = useState<ClassificationProgressState | null>(null)

  // Poll for classification progress
  useEffect(() => {
    if (!classificationSessionId) return

    const pollInterval = setInterval(async () => {
      try {
        const response = await getClassificationProgress(classificationSessionId)
        if (response.success && response.data) {
          const newStatus = response.data.status
          let resultData = undefined

          // 如果已完成，获取结果摘要
          if (newStatus === 'completed') {
            const resultResponse = await getClassificationResult(classificationSessionId)
            if (resultResponse.success && resultResponse.data) {
              resultData = {
                new_entries: resultResponse.data.new_entries,
                duplicates: resultResponse.data.duplicates,
                ignored: resultResponse.data.ignored,
              }
            }
          }

          setClassificationProgress({
            status: newStatus,
            totalItems: response.data.total_items,
            processedItems: response.data.processed_items,
            currentPhase: response.data.current_phase || '处理中',
            estimatedRemainingSeconds: response.data.estimated_remaining_seconds ?? undefined,
            progressPercent: response.data.progress_percent,
            result: resultData,
          })
          // 如果已完成或失败，停止轮询
          if (newStatus === 'completed' || newStatus === 'failed') {
            clearInterval(pollInterval)
          }
        }
      } catch (err) {
        console.error('获取分类进度失败:', err)
      }
    }, 2000)

    return () => clearInterval(pollInterval)
  }, [classificationSessionId])

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true)
        const response = await getSplitResults(sessionId, currentPage, 100)
        if (response.success && response.data) {
          setResults(response.data)
        } else if (!response.success && response.error) {
          setError(response.error.message)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取结果失败')
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [sessionId, currentPage])

  const handleChunkClick = async (chunk: SplitResult) => {
    setSelectedChunk(chunk)

    try {
      const response = await getChunkDetail(sessionId, chunk.chunk_index)
      if (response.success && response.data) {
        setChunkContent(response.data.content)
      }
    } catch (err) {
      console.error('获取片段详情失败:', err)
    }
  }

  const handleCopy = async () => {
    if (!chunkContent) return

    try {
      await navigator.clipboard.writeText(chunkContent)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('复制失败:', err)
    }
  }

  const handleModeSelected = async (mode: ClassificationMode) => {
    try {
      setClassificationError(null)
      setIsClassifying(true)

      const response = await startClassification({
        split_session_id: sessionId,
        mode: mode,
      })

      if (response.success && response.data) {
        setClassificationSessionId(response.data.session_id)
        setShowModeSelect(false)
      } else if (response.error) {
        setClassificationError(response.error.message)
        setIsClassifying(false)
      }
    } catch (err) {
      setClassificationError(err instanceof Error ? err.message : '启动分类失败')
      setIsClassifying(false)
    }
  }

  const handleRetry = () => {
    setClassificationSessionId(null)
    setShowModeSelect(true)
    setIsClassifying(false)
    setClassificationError(null)
  }

  if (loading) {
    return <div className="loading">加载结果中...</div>
  }

  if (error) {
    return <div className="error-message">{error}</div>
  }

  if (!results) {
    return null
  }

  return (
    <div className="result-list">
      <h2>切分结果</h2>

      <div className="results-summary">
        <span>总片段数: {results.total_chunks}</span>
        <span>
          第{results.page}页 / 共{results.total_pages}页
        </span>
      </div>

      {/* Classification Mode Selection */}
      {showModeSelect && !classificationSessionId && (
        <div className="classification-section">
          <ClassificationModeSelect
            onModeSelected={handleModeSelected}
            isProcessing={isClassifying}
          />
          {classificationError && (
            <div className="error-message">{classificationError}</div>
          )}
        </div>
      )}

      {/* Progress Bar */}
      {classificationSessionId && classificationProgress && (
        <div className="classification-progress-section">
          <ProgressBar progress={classificationProgress} onRetry={handleRetry} />
        </div>
      )}

      <div className="results-container">
        <div className="results-sidebar">
          <div className="results-items">
            {results.results.map((chunk) => (
              <div
                key={chunk.chunk_index}
                className={`result-item ${selectedChunk?.chunk_index === chunk.chunk_index ? 'selected' : ''}`}
                onClick={() => handleChunkClick(chunk)}
              >
                <span className="chunk-index">#{chunk.chunk_index}</span>
                <span className="chunk-range">
                  行 {chunk.start_line}-{chunk.end_line}
                </span>
              </div>
            ))}
          </div>

          {results.total_pages > 1 && (
            <div className="pagination">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                上一页
              </button>
              <span>
                {currentPage} / {results.total_pages}
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(results.total_pages, p + 1))}
                disabled={currentPage === results.total_pages}
              >
                下一页
              </button>
            </div>
          )}
        </div>

        <div className="chunk-detail">
          {selectedChunk ? (
            <>
              <div className="chunk-header">
                <h3>片段 #{selectedChunk.chunk_index}</h3>
                <button onClick={handleCopy} className="copy-button">
                  {copied ? '已复制!' : '复制'}
                </button>
              </div>
              <pre className="chunk-content">{chunkContent}</pre>
            </>
          ) : (
            <p className="no-selection">点击左侧片段查看详情</p>
          )}
        </div>
      </div>
    </div>
  )
}
