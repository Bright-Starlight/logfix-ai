import { useState, useEffect } from 'react'
import { validateRegex, executeSplit, getSessionStatus } from '../services/api'
import type { SessionStatus } from '../types'

interface SplitConfigProps {
  fileId: string
  sessionId?: string
  onSplitStarted?: (sessionId: string) => void
  onSplitCompleted?: () => void
}

type RuleType = 'regex' | 'fixed_string'

export default function SplitConfig({
  fileId,
  sessionId: initialSessionId,
  onSplitStarted,
  onSplitCompleted,
}: SplitConfigProps) {
  const [ruleType, setRuleType] = useState<RuleType>('regex')
  const [ruleContent, setRuleContent] = useState('')
  const [regexError, setRegexError] = useState<string | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  const [isSplitting, setIsSplitting] = useState(false)
  const [splitError, setSplitError] = useState<string | null>(null)
  const [sessionStatus, setSessionStatus] = useState<SessionStatus | null>(null)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(initialSessionId || null)

  useEffect(() => {
    if (!currentSessionId) return

    const pollStatus = async () => {
      try {
        const response = await getSessionStatus(currentSessionId)
        if (response.success && response.data) {
          setSessionStatus(response.data)

          if (response.data.status === 'completed') {
            onSplitCompleted?.()
          } else if (response.data.status === 'failed') {
            setSplitError('切分任务失败')
          }
        }
      } catch (err) {
        console.error('获取状态失败:', err)
      }
    }

    pollStatus()
    const interval = setInterval(pollStatus, 2000)

    return () => clearInterval(interval)
  }, [currentSessionId, onSplitCompleted])

  const handleValidateRegex = async () => {
    if (!ruleContent.trim()) {
      setRegexError('请输入正则表达式')
      return
    }

    setIsValidating(true)
    setRegexError(null)

    try {
      const response = await validateRegex(ruleContent)
      if (response.success && response.data) {
        if (!response.data.valid) {
          setRegexError('正则表达式语法错误')
        } else if (response.data.sample_matches === 0) {
          setRegexError('未找到匹配项')
        }
      } else if (!response.success && response.error) {
        setRegexError(response.error.message)
      }
    } catch (err) {
      setRegexError(err instanceof Error ? err.message : '校验失败')
    } finally {
      setIsValidating(false)
    }
  }

  const handleExecuteSplit = async () => {
    if (ruleType === 'regex' && !regexError && !ruleContent.trim()) {
      setRegexError('请输入正则表达式')
      return
    }

    if (ruleType === 'fixed_string' && !ruleContent.trim()) {
      setSplitError('请输入分隔符')
      return
    }

    setIsSplitting(true)
    setSplitError(null)

    try {
      const response = await executeSplit({
        file_id: fileId,
        rule_type: ruleType,
        rule_content: ruleContent,
      })

      if (response.success && response.data) {
        setCurrentSessionId(response.data.session_id)
        onSplitStarted?.(response.data.session_id)
      } else if (!response.success && response.error) {
        setSplitError(response.error.message)
      }
    } catch (err) {
      setSplitError(err instanceof Error ? err.message : '切分执行失败')
    } finally {
      setIsSplitting(false)
    }
  }

  return (
    <div className="split-config">
      <h2>切分配置</h2>

      <div className="rule-type-selector">
        <label>
          <input
            type="radio"
            value="regex"
            checked={ruleType === 'regex'}
            onChange={() => setRuleType('regex')}
          />
          正则表达式
        </label>
        <label>
          <input
            type="radio"
            value="fixed_string"
            checked={ruleType === 'fixed_string'}
            onChange={() => setRuleType('fixed_string')}
          />
          固定分隔符
        </label>
      </div>

      <div className="rule-input">
        {ruleType === 'regex' ? (
          <>
            <input
              type="text"
              placeholder="输入正则表达式，如: ^\d{4}-\d{2}-\d{2}"
              value={ruleContent}
              onChange={(e) => {
                setRuleContent(e.target.value)
                setRegexError(null)
              }}
              className={regexError ? 'error' : ''}
            />
            <button onClick={handleValidateRegex} disabled={isValidating || !ruleContent.trim()}>
              {isValidating ? '校验中...' : '校验'}
            </button>
          </>
        ) : (
          <input
            type="text"
            placeholder="输入分隔符（如空行表示留空）"
            value={ruleContent}
            onChange={(e) => setRuleContent(e.target.value)}
          />
        )}
      </div>

      {regexError && ruleType === 'regex' && (
        <div className="error-message">{regexError}</div>
      )}

      {splitError && <div className="error-message">{splitError}</div>}

      {sessionStatus && currentSessionId && (
        <div className="split-progress">
          <div className="progress-info">
            <span>状态: {sessionStatus.status}</span>
            <span>
              进度: {sessionStatus.processed_chunks} / {sessionStatus.total_chunks}
            </span>
            <span>{sessionStatus.progress_percent}%</span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${sessionStatus.progress_percent}%` }}
            />
          </div>
        </div>
      )}

      {!currentSessionId && (
        <button
          onClick={handleExecuteSplit}
          disabled={
            isSplitting ||
            (ruleType === 'regex' && !ruleContent.trim()) ||
            (ruleType === 'fixed_string' && !ruleContent.trim())
          }
          className="split-button"
        >
          {isSplitting ? '执行中...' : '开始切分'}
        </button>
      )}
    </div>
  )
}
