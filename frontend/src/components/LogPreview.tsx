import { useState, useEffect } from 'react'
import { getFilePreview } from '../services/api'
import type { FilePreviewResponse } from '../types'

interface LogPreviewProps {
  fileId: string
}

export default function LogPreview({ fileId }: LogPreviewProps) {
  const [preview, setPreview] = useState<FilePreviewResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPreview = async () => {
      try {
        setLoading(true)
        const response = await getFilePreview(fileId, 100)
        if (response.success && response.data) {
          setPreview(response.data)
        } else if (!response.success && response.error) {
          setError(response.error.message)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取预览失败')
      } finally {
        setLoading(false)
      }
    }

    fetchPreview()
  }, [fileId])

  if (loading) {
    return <div className="loading">加载预览中...</div>
  }

  if (error) {
    return <div className="error-message">{error}</div>
  }

  if (!preview) {
    return null
  }

  return (
    <div className="log-preview">
      <h2>文件预览</h2>

      <div className="preview-header">
        <span className="filename">{preview.filename}</span>
        <span className="encoding">编码: {preview.encoding}</span>
        <span className="total-lines">总行数: {preview.total_lines}</span>
      </div>

      <div className="preview-content">
        <pre>
          {preview.preview.map((line, index) => (
            <div key={index} className="preview-line">
              <span className="line-number">{index + 1}</span>
              <span className="line-content">{line}</span>
            </div>
          ))}
        </pre>
      </div>

      {preview.total_lines > 100 && (
        <p className="preview-note">显示前100行，共{preview.total_lines}行</p>
      )}
    </div>
  )
}
