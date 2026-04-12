import { useState } from 'react'
import { repoApi } from '../services/api'
import type { RepoInfoResponse } from '../types'

export interface RepoInfo {
  type: 'local' | 'github'
  local_path: string
  remote_url?: string
  name: string
  description?: string
  imported_at: string
}

interface RepoImportProps {
  onRepoImported: (repo: RepoInfo) => void
}

type ImportMethod = 'local' | 'github'

export default function RepoImport({ onRepoImported }: RepoImportProps) {
  const [method, setMethod] = useState<ImportMethod>('local')
  const [localPath, setLocalPath] = useState('')
  const [githubUrl, setGithubUrl] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [clonePath, setClonePath] = useState('')
  const [preview, setPreview] = useState<RepoInfo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  const [isImporting, setIsImporting] = useState(false)

  const parseGithubUrl = (input: string): string | null => {
    const trimmed = input.trim()
    // owner/repo shorthand
    if (/^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/.test(trimmed)) {
      return `https://github.com/${trimmed}`
    }
    // Full HTTPS URL
    if (/^https?:\/\/github\.com\/[^/]+\/[^/]+/.test(trimmed)) {
      return trimmed.replace(/\.git$/, '')
    }
    return null
  }

  const handleValidate = async () => {
    setError(null)
    setPreview(null)
    setIsValidating(true)

    try {
      if (method === 'local') {
        const path = localPath.trim()
        if (!path) {
          setError('请输入本地仓库路径')
          return
        }

        // 调用真实 API 验证
        const response: RepoInfoResponse = await repoApi.validate('local', path)
        if (response.success && response.data) {
          setPreview({
            type: 'local',
            local_path: response.data.local_path,
            name: response.data.name,
            imported_at: response.data.imported_at,
          })
        } else {
          setError(response.error?.message || '验证失败')
        }
      } else {
        const normalizedUrl = parseGithubUrl(githubUrl)
        if (!normalizedUrl) {
          setError('请输入有效的 GitHub 仓库地址（如 owner/repo 或完整 URL）')
          return
        }

        // 调用真实 API 验证
        const response: RepoInfoResponse = await repoApi.validate('github', normalizedUrl, githubToken || undefined)
        if (response.success && response.data) {
          setPreview({
            type: 'github',
            local_path: response.data.local_path || '',
            remote_url: response.data.remote_url,
            name: response.data.name,
            description: response.data.description,
            imported_at: response.data.imported_at,
          })
        } else {
          setError(response.error?.message || '验证失败')
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '验证请求失败')
    } finally {
      setIsValidating(false)
    }
  }

  const handleConfirm = async () => {
    if (!preview) return

    setIsImporting(true)
    setError(null)

    try {
      // 调用真实 API 导入
      const response: RepoInfoResponse = await repoApi.import(
        preview.type,
        preview.type === 'github' ? preview.remote_url || preview.local_path : preview.local_path,
        preview.name,
        method === 'github' ? githubToken : undefined,
        method === 'github' ? clonePath : undefined
      )

      if (response.success && response.data) {
        const importedRepo: RepoInfo = {
          type: response.data.type as 'local' | 'github',
          local_path: response.data.local_path,
          remote_url: response.data.remote_url,
          name: response.data.name,
          description: response.data.description,
          imported_at: response.data.imported_at,
        }
        onRepoImported(importedRepo)
      } else {
        setError(response.error?.message || '导入失败')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '导入请求失败')
    } finally {
      setIsImporting(false)
    }
  }

  const handleMethodChange = (m: ImportMethod) => {
    setMethod(m)
    setPreview(null)
    setError(null)
  }

  const handleFolderBrowse = async (target: 'local' | 'clone') => {
    // File System Access API - Chrome 86+, Edge 86+, Opera 72+
    if ('showDirectoryPicker' in window) {
      try {
        // @ts-ignore - File System Access API
        const dirHandle = await window.showDirectoryPicker()
        // @ts-ignore - path is experimental but available in Chromium
        const selectedPath = dirHandle.path || dirHandle.name

        if (selectedPath) {
          if (target === 'local') {
            setLocalPath(selectedPath)
            setPreview(null)
            setError(null)
          } else {
            setClonePath(selectedPath)
            setPreview(null)
            setError(null)
          }
        }
      } catch (err) {
        // User cancelled - do nothing
        if ((err as Error).name !== 'AbortError') {
          console.error('Directory picker error:', err)
        }
      }
    } else {
      setError('您的浏览器不支持文件夹选择，请手动输入路径')
    }
  }

  return (
    <div className="repo-import-page">
      {/* Method Tabs */}
      <div className="import-method-tabs">
        <button
          className={`import-tab ${method === 'local' ? 'active' : ''}`}
          onClick={() => handleMethodChange('local')}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 7a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
            <path d="M16 3v4M8 3v4M3 11h18" />
          </svg>
          本地仓库
        </button>
        <button
          className={`import-tab ${method === 'github' ? 'active' : ''}`}
          onClick={() => handleMethodChange('github')}
        >
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
          </svg>
          GitHub 仓库
        </button>
      </div>

      {/* Local Import Panel */}
      <div className={`import-panel ${method === 'local' ? 'active' : ''}`}>
        <div className="card">
          <h3 className="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 7a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
              <path d="M16 3v4M8 3v4M3 11h18" />
            </svg>
            选择本地仓库
          </h3>

          <div className="field">
            <label className="field-label">仓库路径</label>
            <div className="input-with-btn">
              <input
                className={`input input-mono ${error && method === 'local' ? 'input-error' : ''}`}
                type="text"
                placeholder="例如：D:\projects\my-repo"
                value={localPath}
                onChange={(e) => {
                  setLocalPath(e.target.value)
                  setPreview(null)
                  setError(null)
                }}
                onKeyDown={(e) => { if (e.key === 'Enter') handleValidate() }}
              />
              <button className="btn btn-secondary" onClick={() => handleFolderBrowse('local')} type="button" title="选择文件夹">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 14, height: 14 }}>
                  <path d="M3 7a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                  <path d="M16 3v4M8 3v4M3 11h18" />
                </svg>
                浏览
              </button>
              <button className="btn btn-primary" onClick={handleValidate} disabled={isValidating || !localPath.trim()}>
                {isValidating ? <span className="spinner" style={{ width: 14, height: 14 }} /> : '验证'}
              </button>
            </div>
            <span className="field-hint">
              点击「浏览」使用系统对话框选择文件夹，或直接输入路径
            </span>
          </div>

          {error && method === 'local' && (
            <div className="alert alert-error" style={{ marginTop: 'var(--sp-4)' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 8v4M12 16h.01" />
              </svg>
              {error}
            </div>
          )}
        </div>
      </div>

      {/* GitHub Import Panel */}
      <div className={`import-panel ${method === 'github' ? 'active' : ''}`}>
        <div className="card">
          <h3 className="card-title">
            <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 16, height: 16 }}>
              <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
            </svg>
            导入 GitHub 仓库
          </h3>

          <div className="field">
            <label className="field-label">仓库地址</label>
            <div className="input-with-btn">
              <input
                className={`input ${error && method === 'github' ? 'input-error' : ''}`}
                type="text"
                placeholder="例如：owner/repo 或 https://github.com/owner/repo"
                value={githubUrl}
                onChange={(e) => {
                  setGithubUrl(e.target.value)
                  setPreview(null)
                  setError(null)
                }}
                onKeyDown={(e) => { if (e.key === 'Enter') handleValidate() }}
              />
              <button className="btn btn-secondary" onClick={handleValidate} disabled={isValidating || !githubUrl.trim()}>
                {isValidating ? <span className="spinner" style={{ width: 14, height: 14 }} /> : '验证'}
              </button>
            </div>
            <span className="field-hint">支持 owner/repo 简写或完整 HTTPS URL，私有仓库请输入 Token</span>
          </div>

          <div className="field" style={{ marginTop: 'var(--sp-4)' }}>
            <label className="field-label">GitHub Token（私有仓库必填）</label>
            <input
              className="input input-mono"
              type="password"
              placeholder="ghp_xxxx 或 gho_xxxx"
              value={githubToken}
              onChange={(e) => {
                setGithubToken(e.target.value)
                setError(null)
              }}
            />
            <span className="field-hint">私有仓库需要配置 GitHub Personal Access Token</span>
          </div>

          <div className="field" style={{ marginTop: 'var(--sp-4)' }}>
            <label className="field-label">克隆目标路径</label>
            <div className="input-with-btn">
              <input
                className={`input input-mono ${error && method === 'github' ? 'input-error' : ''}`}
                type="text"
                placeholder="例如：D:\code\cloned-repos"
                value={clonePath}
                onChange={(e) => {
                  setClonePath(e.target.value)
                  setPreview(null)
                  setError(null)
                }}
              />
              <button className="btn btn-secondary" onClick={() => handleFolderBrowse('clone')} type="button" title="选择文件夹">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 14, height: 14 }}>
                  <path d="M3 7a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                  <path d="M16 3v4M8 3v4M3 11h18" />
                </svg>
                浏览
              </button>
            </div>
            <span className="field-hint">选择 GitHub 仓库克隆到本地的目标文件夹</span>
          </div>

          {error && method === 'github' && (
            <div className="alert alert-error" style={{ marginTop: 'var(--sp-4)' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 8v4M12 16h.01" />
              </svg>
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Preview */}
      {preview && (
        <div className="card" style={{ marginTop: 'var(--sp-4)' }}>
          <h3 className="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 12l2 2 4-4" />
              <circle cx="12" cy="12" r="10" />
            </svg>
            仓库信息
          </h3>
          <div className="repo-preview" style={{ background: 'transparent', padding: 0, border: 'none' }}>
            <div className="repo-preview-icon">
              {preview.type === 'local' ? (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 7a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
                  <path d="M3 11h18" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
              )}
            </div>
            <div className="repo-preview-info">
              <div className="repo-preview-name">{preview.name}</div>
              <div className="repo-preview-path">{preview.type === 'local' ? preview.local_path : preview.remote_url}</div>
              {preview.description && (
                <div className="repo-preview-description">{preview.description}</div>
              )}
            </div>
            <span className={`badge ${preview.type === 'local' ? 'badge-neutral' : 'badge-accent'}`}>
              {preview.type === 'local' ? '本地' : 'GitHub'}
            </span>
          </div>

          <div className="import-actions">
            <button className="btn btn-ghost" onClick={() => setPreview(null)}>
              重新选择
            </button>
            <button
              className="btn btn-primary btn-lg"
              onClick={handleConfirm}
              disabled={isImporting}
            >
              {isImporting ? (
                <>
                  <span className="spinner" style={{ width: 15, height: 15 }} />
                  导入中...
                </>
              ) : (
                <>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ width: 15, height: 15 }}>
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                  确认导入，开始上传日志
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {!preview && (
        <div style={{ marginTop: 'var(--sp-4)', display: 'flex', justifyContent: 'flex-end' }}>
          <button
            className="btn btn-primary btn-lg"
            onClick={handleValidate}
            disabled={isValidating || (method === 'local' ? !localPath.trim() : !githubUrl.trim())}
          >
            {isValidating ? (
              <>
                <span className="spinner" style={{ width: 15, height: 15 }} />
                验证中...
              </>
            ) : (
              <>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ width: 15, height: 15 }}>
                  <path d="M9 12l2 2 4-4M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                验证仓库
              </>
            )}
          </button>
        </div>
      )}
    </div>
  )
}
