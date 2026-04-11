import { useState, useEffect, useCallback } from 'react'
import { getIgnoreRules, createIgnoreRule, deleteIgnoreRule } from '../services/api'
import type { IgnoreRuleResponse, CreateIgnoreRuleRequest } from '../types'

export default function IgnoreRuleManager() {
  const [rules, setRules] = useState<IgnoreRuleResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)

  // Form state
  const [name, setName] = useState('')
  const [matchType, setMatchType] = useState<'contains' | 'regex' | 'exact'>('contains')
  const [pattern, setPattern] = useState('')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const loadRules = useCallback(async () => {
    try {
      setLoading(true)
      const response = await getIgnoreRules()
      if (response.success && response.data) {
        setRules(response.data.rules)
      } else {
        setError(response.error?.message || '加载失败')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '网络请求失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadRules()
  }, [loadRules])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!name || !pattern) {
      setError('名称和匹配模式不能为空')
      return
    }

    try {
      setSubmitting(true)
      const request: CreateIgnoreRuleRequest = {
        name,
        match_type: matchType,
        pattern,
        description: description || undefined,
        enabled: true,
      }

      const response = await createIgnoreRule(request)
      if (response.success) {
        setShowForm(false)
        setName('')
        setMatchType('contains')
        setPattern('')
        setDescription('')
        loadRules()
      } else {
        setError(response.error?.message || '创建失败')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (ruleId: string) => {
    if (!confirm('确定要删除这条忽略规则吗？')) {
      return
    }

    try {
      const response = await deleteIgnoreRule(ruleId)
      if (response.success) {
        loadRules()
      } else {
        setError(response.error?.message || '删除失败')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  const getMatchTypeLabel = (type: string) => {
    switch (type) {
      case 'contains':
        return '包含'
      case 'regex':
        return '正则'
      case 'exact':
        return '精确'
      default:
        return type
    }
  }

  if (loading) {
    return <div className="ignore-rule-loading">加载中...</div>
  }

  return (
    <div className="ignore-rule-manager">
      <div className="manager-header">
        <h3>忽略规则管理</h3>
        <button onClick={() => setShowForm(!showForm)} className="add-button">
          {showForm ? '取消' : '添加规则'}
        </button>
      </div>

      {error && (
        <div className="manager-error">
          <span>{error}</span>
          <button onClick={() => setError(null)}>关闭</button>
        </div>
      )}

      {showForm && (
        <form className="ignore-rule-form" onSubmit={handleSubmit}>
          <div className="form-row">
            <label htmlFor="rule-name">规则名称</label>
            <input
              id="rule-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例如：忽略连接超时"
              required
            />
          </div>

          <div className="form-row">
            <label htmlFor="match-type">匹配类型</label>
            <select
              id="match-type"
              value={matchType}
              onChange={(e) => setMatchType(e.target.value as 'contains' | 'regex' | 'exact')}
            >
              <option value="contains">包含</option>
              <option value="regex">正则表达式</option>
              <option value="exact">精确匹配</option>
            </select>
          </div>

          <div className="form-row">
            <label htmlFor="pattern">匹配模式</label>
            <input
              id="pattern"
              type="text"
              value={pattern}
              onChange={(e) => setPattern(e.target.value)}
              placeholder={matchType === 'regex' ? '例如: timeout|Connection refused' : '例如: Connection timeout'}
              required
            />
          </div>

          <div className="form-row">
            <label htmlFor="description">描述（可选）</label>
            <input
              id="description"
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="规则的用途说明..."
            />
          </div>

          <div className="form-actions">
            <button type="submit" disabled={submitting}>
              {submitting ? '创建中...' : '创建规则'}
            </button>
          </div>
        </form>
      )}

      <div className="rules-list">
        {rules.length === 0 ? (
          <div className="rules-empty">暂无忽略规则</div>
        ) : (
          rules.map((rule) => (
            <div key={rule.id} className="rule-item">
              <div className="rule-info">
                <div className="rule-header">
                  <span className="rule-name">{rule.name}</span>
                  <span className={`rule-badge ${rule.enabled ? 'enabled' : 'disabled'}`}>
                    {rule.enabled ? '启用' : '禁用'}
                  </span>
                </div>
                <div className="rule-details">
                  <span className="rule-type">{getMatchTypeLabel(rule.match_type)}</span>
                  <code className="rule-pattern">{rule.pattern}</code>
                </div>
                {rule.description && (
                  <div className="rule-description">{rule.description}</div>
                )}
              </div>
              <button
                className="delete-button"
                onClick={() => handleDelete(rule.id)}
                title="删除规则"
              >
                删除
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
