import axios from 'axios'
import type {
  ApiResponse,
  UploadResponse,
  FilePreviewResponse,
  SplitRequest,
  SplitResponse,
  SessionStatus,
  ResultsResponse,
  RegexValidationRequest,
  RegexValidationResponse,
} from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.error?.message || error.message || '网络请求失败'
    return Promise.reject(new Error(message))
  }
)

export const uploadFile = async (
  file: File,
  chunkIndex?: number,
  totalChunks?: number,
  uploadId?: string
): Promise<ApiResponse<UploadResponse>> => {
  const formData = new FormData()
  formData.append('file', file)

  if (chunkIndex !== undefined) {
    formData.append('chunk_index', String(chunkIndex))
  }
  if (totalChunks !== undefined) {
    formData.append('total_chunks', String(totalChunks))
  }
  if (uploadId) {
    formData.append('upload_id', uploadId)
  }

  const response = await api.post<ApiResponse<UploadResponse>>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export const getFilePreview = async (
  fileId: string,
  lines: number = 100
): Promise<ApiResponse<FilePreviewResponse>> => {
  const response = await api.get<ApiResponse<FilePreviewResponse>>(`/files/${fileId}`, {
    params: { lines },
  })
  return response.data
}

export const validateRegex = async (
  pattern: string
): Promise<ApiResponse<RegexValidationResponse>> => {
  const response = await api.post<ApiResponse<RegexValidationResponse>>('/validate/regex', {
    pattern,
  } as RegexValidationRequest)
  return response.data
}

export const executeSplit = async (
  request: SplitRequest
): Promise<ApiResponse<SplitResponse>> => {
  const response = await api.post<ApiResponse<SplitResponse>>('/split', request)
  return response.data
}

export const getSessionStatus = async (
  sessionId: string
): Promise<ApiResponse<SessionStatus>> => {
  const response = await api.get<ApiResponse<SessionStatus>>(`/sessions/${sessionId}`)
  return response.data
}

export const getSplitResults = async (
  sessionId: string,
  page: number = 1,
  pageSize: number = 100
): Promise<ApiResponse<ResultsResponse>> => {
  const response = await api.get<ApiResponse<ResultsResponse>>(`/results/${sessionId}`, {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const getChunkDetail = async (
  sessionId: string,
  chunkIndex: number
): Promise<ApiResponse<{ content: string; line_count: number }>> => {
  const response = await api.get<ApiResponse<{ content: string; line_count: number }>>(
    `/results/${sessionId}/chunks/${chunkIndex}`
  )
  return response.data
}

export default api
