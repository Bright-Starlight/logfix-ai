/**
 * 仓库导入组件测试
 *
 * 测试 RepoImport 组件的验证和导入功能
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'
import RepoImport from '../src/components/RepoImport'

// Mock API module
vi.mock('../src/services/api', () => ({
  repoApi: {
    validate: vi.fn(),
    import: vi.fn(),
    getCurrent: vi.fn(),
  },
}))

import { repoApi } from '../src/services/api'

const mockedRepoApi = repoApi as ReturnType<typeof vi.fn> & {
  validate: ReturnType<typeof vi.fn>
  import: ReturnType<typeof vi.fn>
}

describe('RepoImport Component - T013: Local Repository Validation', () => {
  const mockOnRepoImported = vi.fn()

  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(repoApi.validate).mockReset()
    vi.mocked(repoApi.import).mockReset()
  })

  it('T013: 本地仓库验证 - 验证失败显示错误（路径不存在）', async () => {
    mockedRepoApi.validate.mockResolvedValueOnce({
      success: false,
      data: null,
      error: { code: 'PATH_NOT_ACCESSIBLE', message: '目录不存在' },
    })

    render(<RepoImport onRepoImported={mockOnRepoImported} />)

    // 输入本地路径
    const input = screen.getByPlaceholderText(/例如：D:\\projects\\my-repo/i)
    await userEvent.type(input, 'D:\\nonexistent\\path')

    // 点击底部的"验证仓库"按钮
    const validateBtn = screen.getByRole('button', { name: /验证仓库/i })
    await userEvent.click(validateBtn)

    // 等待错误显示
    await waitFor(() => {
      expect(screen.getByText(/目录不存在/i)).toBeInTheDocument()
    })
  })

  it('T013: 本地仓库验证 - 验证成功显示预览', async () => {
    mockedRepoApi.validate.mockResolvedValueOnce({
      success: true,
      data: {
        id: '1',
        type: 'local',
        local_path: 'D:\\test\\my-repo',
        name: 'my-repo',
        imported_at: '2026-04-12T10:00:00Z',
      },
      error: null,
    })

    render(<RepoImport onRepoImported={mockOnRepoImported} />)

    // 输入本地路径
    const input = screen.getByPlaceholderText(/例如：D:\\projects\\my-repo/i)
    await userEvent.type(input, 'D:\\test\\my-repo')

    // 点击底部的"验证仓库"按钮
    const validateBtn = screen.getByRole('button', { name: /验证仓库/i })
    await userEvent.click(validateBtn)

    // 等待预览显示
    await waitFor(() => {
      expect(screen.getByText('my-repo')).toBeInTheDocument()
    })
  })

  it('T013: 本地仓库验证 - 空路径按钮禁用', async () => {
    render(<RepoImport onRepoImported={mockOnRepoImported} />)

    // 验证按钮应该禁用
    const validateBtn = screen.getByRole('button', { name: /验证仓库/i })
    expect(validateBtn).toBeDisabled()
  })
})

describe('RepoImport Component - T026: GitHub Repository Validation', () => {
  const mockOnRepoImported = vi.fn()

  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(repoApi.validate).mockReset()
    vi.mocked(repoApi.import).mockReset()
  })

  it('T026: GitHub 仓库验证 - 无效 URL 格式显示客户端错误', async () => {
    // 注意：组件在调用 API 前会先验证 URL 格式
    // "invalid-url" 不符合 owner/repo 格式，会被客户端拦截

    render(<RepoImport onRepoImported={mockOnRepoImported} />)

    // 切换到 GitHub Tab
    const githubTab = screen.getByRole('button', { name: /GitHub 仓库/i })
    fireEvent.click(githubTab)

    // 输入无效的 URL（不符合格式要求）
    const input = screen.getByPlaceholderText(/例如：owner\/repo/i)
    await userEvent.type(input, 'invalid-url')

    // 点击验证按钮
    const validateBtn = screen.getByRole('button', { name: /验证仓库/i })
    await userEvent.click(validateBtn)

    // 等待客户端验证错误显示
    await waitFor(() => {
      expect(screen.getByText(/请输入有效的 GitHub 仓库地址/i)).toBeInTheDocument()
    })
  })

  it('T026: GitHub 仓库验证 - 有效格式但仓库不存在', async () => {
    // 符合格式的 owner/repo，但仓库不存在
    mockedRepoApi.validate.mockResolvedValueOnce({
      success: false,
      data: null,
      error: { code: 'GITHUB_REPO_NOT_FOUND', message: '仓库不存在' },
    })

    render(<RepoImport onRepoImported={mockOnRepoImported} />)

    // 切换到 GitHub Tab
    const githubTab = screen.getByRole('button', { name: /GitHub 仓库/i })
    fireEvent.click(githubTab)

    // 输入有效的格式但仓库不存在
    const input = screen.getByPlaceholderText(/例如：owner\/repo/i)
    await userEvent.type(input, 'nonexistentowner/nonexistentrepo')

    // 点击验证按钮
    const validateBtn = screen.getByRole('button', { name: /验证仓库/i })
    await userEvent.click(validateBtn)

    // 等待 API 错误显示
    await waitFor(() => {
      expect(screen.getByText(/仓库不存在/i)).toBeInTheDocument()
    })
  })

  it('T026: GitHub 仓库验证 - 验证成功显示预览', async () => {
    mockedRepoApi.validate.mockResolvedValueOnce({
      success: true,
      data: {
        id: '1',
        type: 'github',
        local_path: '/tmp/test-repo',
        remote_url: 'https://github.com/owner/test-repo',
        name: 'test-repo',
        description: 'A test repository',
        imported_at: '2026-04-12T10:00:00Z',
      },
      error: null,
    })

    render(<RepoImport onRepoImported={mockOnRepoImported} />)

    // 切换到 GitHub Tab
    const githubTab = screen.getByRole('button', { name: /GitHub 仓库/i })
    fireEvent.click(githubTab)

    // 输入有效的 owner/repo
    const input = screen.getByPlaceholderText(/例如：owner\/repo/i)
    await userEvent.type(input, 'owner/test-repo')

    // 点击验证按钮
    const validateBtn = screen.getByRole('button', { name: /验证仓库/i })
    await userEvent.click(validateBtn)

    // 等待预览显示
    await waitFor(() => {
      expect(screen.getByText('test-repo')).toBeInTheDocument()
    })
  })

  it('T026: GitHub 仓库验证 - 支持完整 HTTPS URL', async () => {
    mockedRepoApi.validate.mockResolvedValueOnce({
      success: true,
      data: {
        id: '1',
        type: 'github',
        local_path: '/tmp/test-repo',
        remote_url: 'https://github.com/owner/test-repo',
        name: 'test-repo',
        imported_at: '2026-04-12T10:00:00Z',
      },
      error: null,
    })

    render(<RepoImport onRepoImported={mockOnRepoImported} />)

    // 切换到 GitHub Tab
    const githubTab = screen.getByRole('button', { name: /GitHub 仓库/i })
    fireEvent.click(githubTab)

    // 输入完整的 HTTPS URL
    const input = screen.getByPlaceholderText(/例如：owner\/repo/i)
    await userEvent.type(input, 'https://github.com/owner/test-repo')

    // 点击验证按钮
    const validateBtn = screen.getByRole('button', { name: /验证仓库/i })
    await userEvent.click(validateBtn)

    // 等待预览显示
    await waitFor(() => {
      expect(screen.getByText('test-repo')).toBeInTheDocument()
    })
  })
})

describe('RepoImport Component - T035: Import Flow', () => {
  const mockOnRepoImported = vi.fn()

  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(repoApi.validate).mockReset()
    vi.mocked(repoApi.import).mockReset()
  })

  it('T035: 导入成功 - 调用 onRepoImported 回调', async () => {
    // 先验证成功
    mockedRepoApi.validate.mockResolvedValueOnce({
      success: true,
      data: {
        id: '1',
        type: 'local',
        local_path: 'D:\\test\\my-repo',
        name: 'my-repo',
        imported_at: '2026-04-12T10:00:00Z',
      },
      error: null,
    })

    // 再导入成功
    mockedRepoApi.import.mockResolvedValueOnce({
      success: true,
      data: {
        id: '1',
        type: 'local',
        local_path: 'D:\\test\\my-repo',
        name: 'my-repo',
        imported_at: '2026-04-12T10:00:00Z',
      },
      error: null,
    })

    render(<RepoImport onRepoImported={mockOnRepoImported} />)

    // 输入路径并验证
    const input = screen.getByPlaceholderText(/例如：D:\\projects\\my-repo/i)
    await userEvent.type(input, 'D:\\test\\my-repo')

    const validateBtn = screen.getByRole('button', { name: /验证仓库/i })
    await userEvent.click(validateBtn)

    // 等待预览显示后确认导入
    await waitFor(() => {
      expect(screen.getByText('my-repo')).toBeInTheDocument()
    })

    // 点击确认导入按钮
    const importBtn = screen.getByRole('button', { name: /确认导入/i })
    await userEvent.click(importBtn)

    // 等待 onRepoImported 被调用
    await waitFor(() => {
      expect(mockOnRepoImported).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'local',
          name: 'my-repo',
          local_path: 'D:\\test\\my-repo',
        })
      )
    })
  })

  it('T035: 导入失败 - 显示错误信息且不调用回调', async () => {
    // 验证成功
    mockedRepoApi.validate.mockResolvedValueOnce({
      success: true,
      data: {
        id: '1',
        type: 'local',
        local_path: 'D:\\test\\my-repo',
        name: 'my-repo',
        imported_at: '2026-04-12T10:00:00Z',
      },
      error: null,
    })

    // 导入失败
    mockedRepoApi.import.mockResolvedValueOnce({
      success: false,
      data: null,
      error: { code: 'INTERNAL_ERROR', message: '导入仓库失败' },
    })

    render(<RepoImport onRepoImported={mockOnRepoImported} />)

    // 输入路径并验证
    const input = screen.getByPlaceholderText(/例如：D:\\projects\\my-repo/i)
    await userEvent.type(input, 'D:\\test\\my-repo')

    const validateBtn = screen.getByRole('button', { name: /验证仓库/i })
    await userEvent.click(validateBtn)

    // 等待预览显示
    await waitFor(() => {
      expect(screen.getByText('my-repo')).toBeInTheDocument()
    })

    // 点击确认导入按钮
    const importBtn = screen.getByRole('button', { name: /确认导入/i })
    await userEvent.click(importBtn)

    // 等待错误显示
    await waitFor(() => {
      expect(screen.getByText(/导入仓库失败/i)).toBeInTheDocument()
    })

    // 确保 onRepoImported 没有被调用
    expect(mockOnRepoImported).not.toHaveBeenCalled()
  })
})

describe('RepoImport Component - Tab Switching', () => {
  const mockOnRepoImported = vi.fn()

  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(repoApi.validate).mockReset()
    vi.mocked(repoApi.import).mockReset()
  })

  it('T026: Tab 切换 - 清空之前的状态', async () => {
    // 本地验证成功
    mockedRepoApi.validate.mockResolvedValueOnce({
      success: true,
      data: {
        id: '1',
        type: 'local',
        local_path: 'D:\\test\\my-repo',
        name: 'my-repo',
        imported_at: '2026-04-12T10:00:00Z',
      },
      error: null,
    })

    render(<RepoImport onRepoImported={mockOnRepoImported} />)

    // 输入本地路径并验证
    const localInput = screen.getByPlaceholderText(/例如：D:\\projects\\my-repo/i)
    await userEvent.type(localInput, 'D:\\test\\my-repo')

    const validateBtn = screen.getByRole('button', { name: /验证仓库/i })
    await userEvent.click(validateBtn)

    // 等待预览显示
    await waitFor(() => {
      expect(screen.getByText('my-repo')).toBeInTheDocument()
    })

    // 切换到 GitHub Tab
    const githubTab = screen.getByRole('button', { name: /GitHub 仓库/i })
    fireEvent.click(githubTab)

    // 确认 GitHub 输入框为空
    expect(screen.getByPlaceholderText(/例如：owner\/repo/i)).toHaveValue('')
  })
})
