import { useState, useRef } from 'react'
import { uploadFile } from '../services/api'
import type { UploadResponse } from '../types'

interface FileUploadProps {
  onFileUploaded: (fileId: string) => void
}

const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100MB
const CHUNK_SIZE = 5 * 1024 * 1024 // 5MB chunks

export default function FileUpload({ onFileUploaded }: FileUploadProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (file.size > MAX_FILE_SIZE) {
      setError('文件大小超过100MB限制')
      return
    }

    setSelectedFile(file)
    setError(null)
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('请选择文件')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      const totalChunks = Math.ceil(selectedFile.size / CHUNK_SIZE)

      if (totalChunks > 1) {
        // Chunked upload
        let uploadId: string | undefined
        for (let i = 0; i < totalChunks; i++) {
          const chunk = selectedFile.slice(i * CHUNK_SIZE, (i + 1) * CHUNK_SIZE)
          const chunkFile = new File([chunk], selectedFile.name, { type: selectedFile.type })

          const response = await uploadFile(chunkFile, i, totalChunks, uploadId)
          if (response.success && response.data) {
            uploadId = response.data.upload_id
            setProgress(Math.round(((i + 1) / totalChunks) * 100))
          } else if (!response.success && response.error) {
            throw new Error(response.error.message)
          }
        }
      } else {
        // Single file upload
        const response = await uploadFile(selectedFile)
        if (response.success && response.data) {
          setProgress(100)
          onFileUploaded(response.data.file_id)
        } else if (!response.success && response.error) {
          throw new Error(response.error.message)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault()
    const file = event.dataTransfer.files?.[0]
    if (file) {
      if (file.size > MAX_FILE_SIZE) {
        setError('文件大小超过100MB限制')
        return
      }
      setSelectedFile(file)
      setError(null)
    }
  }

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault()
  }

  return (
    <div className="file-upload">
      <h2>上传日志文件</h2>

      <div
        className="upload-zone"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".log,.txt,.json"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />

        {selectedFile ? (
          <div className="selected-file">
            <p className="filename">{selectedFile.name}</p>
            <p className="filesize">{(selectedFile.size / 1024).toFixed(2)} KB</p>
          </div>
        ) : (
          <p>拖拽文件到此处，或点击选择文件</p>
        )}

        <p className="hint">支持 .log, .txt, .json 格式，最大100MB</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      {isUploading && (
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
          <span className="progress-text">{progress}%</span>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!selectedFile || isUploading}
        className="upload-button"
      >
        {isUploading ? '上传中...' : '上传文件'}
      </button>
    </div>
  )
}
