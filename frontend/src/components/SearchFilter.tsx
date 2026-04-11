import { useState } from 'react'

export interface SearchFilters {
  keyword?: string
  level?: string
  category?: string
  start_date?: string
  end_date?: string
}

interface SearchFilterProps {
  onSearch: (filters: SearchFilters) => void
}

export default function SearchFilter({ onSearch }: SearchFilterProps) {
  const [keyword, setKeyword] = useState('')
  const [level, setLevel] = useState('')
  const [category, setCategory] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch({
      keyword: keyword || undefined,
      level: level || undefined,
      category: category || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    })
  }

  const handleReset = () => {
    setKeyword('')
    setLevel('')
    setCategory('')
    setStartDate('')
    setEndDate('')
    onSearch({})
  }

  return (
    <form className="search-filter" onSubmit={handleSubmit}>
      <div className="filter-row">
        <div className="filter-item">
          <label htmlFor="keyword">关键词</label>
          <input
            id="keyword"
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="搜索日志内容..."
          />
        </div>

        <div className="filter-item">
          <label htmlFor="level">日志级别</label>
          <select
            id="level"
            value={level}
            onChange={(e) => setLevel(e.target.value)}
          >
            <option value="">全部</option>
            <option value="FATAL">FATAL</option>
            <option value="ERROR">ERROR</option>
            <option value="WARNING">WARNING</option>
            <option value="INFO">INFO</option>
            <option value="DEBUG">DEBUG</option>
          </select>
        </div>

        <div className="filter-item">
          <label htmlFor="category">分类</label>
          <input
            id="category"
            type="text"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="分类名称..."
          />
        </div>
      </div>

      <div className="filter-row">
        <div className="filter-item">
          <label htmlFor="start_date">开始日期</label>
          <input
            id="start_date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>

        <div className="filter-item">
          <label htmlFor="end_date">结束日期</label>
          <input
            id="end_date"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
      </div>

      <div className="filter-actions">
        <button type="submit">搜索</button>
        <button type="button" onClick={handleReset}>
          重置
        </button>
      </div>
    </form>
  )
}
