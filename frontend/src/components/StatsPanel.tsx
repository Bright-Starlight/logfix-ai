import { useState, useEffect } from 'react'
import { getStats } from '../services/api'
import type { StatsResponse } from '../types'

export default function StatsPanel() {
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await getStats()
      if (response.success && response.data) {
        setStats(response.data)
      } else {
        setError(response.error?.message || '加载失败')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '网络请求失败')
    } finally {
      setLoading(false)
    }
  }

  const getCategoryColor = (name: string) => {
    switch (name) {
      case '异常错误':
        return '#EF4444'
      case '警告':
        return '#F59E0B'
      case '信息':
        return '#3B82F6'
      case '调试':
        return '#6B7280'
      case '致命错误':
        return '#7F1D1D'
      default:
        return '#6B7280'
    }
  }

  const maxDailyCount = stats?.daily_trend
    ? Math.max(...stats.daily_trend.map((d) => d.count), 1)
    : 1

  if (loading) {
    return (
      <div className="stats-panel-loading">
        <span>加载中...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="stats-panel-error">
        <span>错误: {error}</span>
        <button onClick={loadStats}>重试</button>
      </div>
    )
  }

  if (!stats) {
    return null
  }

  return (
    <div className="stats-panel">
      <h2>统计概览</h2>

      <div className="stats-summary">
        <div className="stat-card">
          <span className="stat-value">{stats.total_entries}</span>
          <span className="stat-label">总日志条数</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{stats.unique_errors}</span>
          <span className="stat-label">唯一错误数</span>
        </div>
      </div>

      <div className="stats-section">
        <h3>分类分布</h3>
        {stats.categories.length === 0 ? (
          <div className="stats-empty">暂无数据</div>
        ) : (
          <div className="category-chart">
            {stats.categories.map((cat) => (
              <div key={cat.name} className="category-bar">
                <div className="category-info">
                  <span
                    className="category-dot"
                    style={{ backgroundColor: getCategoryColor(cat.name) }}
                  />
                  <span className="category-name">{cat.name}</span>
                  <span className="category-count">{cat.count}</span>
                  <span className="category-percentage">
                    ({cat.percentage.toFixed(1)}%)
                  </span>
                </div>
                <div className="category-progress">
                  <div
                    className="category-progress-bar"
                    style={{
                      width: `${cat.percentage}%`,
                      backgroundColor: getCategoryColor(cat.name),
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="stats-section">
        <h3>每日趋势</h3>
        {stats.daily_trend.length === 0 ? (
          <div className="stats-empty">暂无数据</div>
        ) : (
          <div className="daily-trend">
            {stats.daily_trend.map((day) => (
              <div key={day.date} className="trend-bar">
                <div
                  className="trend-bar-fill"
                  style={{ height: `${(day.count / maxDailyCount) * 100}%` }}
                />
                <span className="trend-date">{day.date.slice(5)}</span>
                <span className="trend-count">{day.count}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
