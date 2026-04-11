import { useState, useEffect } from 'react'
import { getIgnoreRules } from '../services/api'
import type { IgnoreRuleResponse } from '../types'

interface RuleMatchWarningProps {
  originalMessage?: string
}

export default function RuleMatchWarning({ originalMessage }: RuleMatchWarningProps) {
  const [rules, setRules] = useState<IgnoreRuleResponse[]>([])
  const [showWarning, setShowWarning] = useState(false)

  useEffect(() => {
    loadIgnoreRules()
  }, [])

  const loadIgnoreRules = async () => {
    try {
      const response = await getIgnoreRules()
      if (response.success && response.data) {
        setRules(response.data.rules)
      }
    } catch (err) {
      console.error('加载忽略规则失败:', err)
    }
  }

  const checkIfIgnored = () => {
    if (!originalMessage) return false

    for (const rule of rules) {
      if (!rule.enabled) continue

      let matched = false
      switch (rule.match_type) {
        case 'contains':
          matched = rule.pattern.toLowerCase().includes(originalMessage.toLowerCase())
          break
        case 'exact':
          matched = rule.pattern === originalMessage
          break
        case 'regex':
          try {
            const regex = new RegExp(rule.pattern)
            matched = regex.test(originalMessage)
          } catch {
            matched = false
          }
          break
      }

      if (matched) {
        return true
      }
    }

    return false
  }

  useEffect(() => {
    if (originalMessage && rules.length > 0) {
      setShowWarning(checkIfIgnored())
    }
  }, [originalMessage, rules])

  if (!showWarning) {
    return null
  }

  return (
    <div className="rule-match-warning">
      <div className="warning-icon">⚠️</div>
      <div className="warning-content">
        <h4>此日志被忽略规则匹配</h4>
        <p>该日志消息符合您配置的忽略规则，不会被存储到数据库中。</p>
        {originalMessage && (
          <details>
            <summary>查看原始消息</summary>
            <pre>{originalMessage}</pre>
          </details>
        )}
      </div>
    </div>
  )
}
