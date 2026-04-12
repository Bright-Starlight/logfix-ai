import axios from 'axios'
import type {
  ApiResponse,
  UploadResponse,
  FilePreviewResponse,
  FileListItem,
  SessionListItem,
  SplitRequest,
  SplitResponse,
  SessionStatus,
  ResultsResponse,
  RegexValidationRequest,
  RegexValidationResponse,
  // 002-short-name-structured 新增
  ClassifyRequest,
  ClassifyResponse,
  LogListResponse,
  LogDetailResponse,
  StatsResponse,
  ParseRuleResponse,
  CreateParseRuleRequest,
  UpdateParseRuleRequest,
  IgnoreRuleResponse,
  CreateIgnoreRuleRequest,
  // 003-log-analysis-pipeline 新增
  ClassificationStartRequest,
  ClassificationStartResponse,
  ClassificationProgressResponse,
  ClassificationResultResponse,
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

export const getFileList = async (): Promise<ApiResponse<{ files: FileListItem[] }>> => {
  const response = await api.get<ApiResponse<{ files: FileListItem[] }>>('/files')
  return response.data
}

export const getSessionList = async (): Promise<ApiResponse<{ sessions: SessionListItem[] }>> => {
  const response = await api.get<ApiResponse<{ sessions: SessionListItem[] }>>('/sessions')
  return response.data
}

// ============ 002-short-name-structured 新增 API ============

export const classifyLogs = async (
  request: ClassifyRequest
): Promise<ApiResponse<ClassifyResponse>> => {
  const response = await api.post<ApiResponse<ClassifyResponse>>('/classify', request)
  return response.data
}

export const getLogsList = async (
  page: number = 1,
  pageSize: number = 50,
  filters?: {
    category?: string
    level?: string
    keyword?: string
    start_date?: string
    end_date?: string
  }
): Promise<ApiResponse<LogListResponse>> => {
  const response = await api.get<ApiResponse<LogListResponse>>('/logs', {
    params: { page, page_size: pageSize, ...filters },
  })
  return response.data
}

export const getLogDetail = async (
  logId: string
): Promise<ApiResponse<LogDetailResponse>> => {
  const response = await api.get<ApiResponse<LogDetailResponse>>(`/logs/${logId}`)
  return response.data
}

export const getStats = async (
  startDate?: string,
  endDate?: string
): Promise<ApiResponse<StatsResponse>> => {
  const response = await api.get<ApiResponse<StatsResponse>>('/stats', {
    params: { start_date: startDate, end_date: endDate },
  })
  return response.data
}

export const getRules = async (): Promise<ApiResponse<{ rules: ParseRuleResponse[] }>> => {
  const response = await api.get<ApiResponse<{ rules: ParseRuleResponse[] }>>('/rules')
  return response.data
}

export const createRule = async (
  request: CreateParseRuleRequest
): Promise<ApiResponse<ParseRuleResponse>> => {
  const response = await api.post<ApiResponse<ParseRuleResponse>>('/rules', request)
  return response.data
}

export const updateRule = async (
  ruleId: string,
  request: UpdateParseRuleRequest
): Promise<ApiResponse<ParseRuleResponse>> => {
  const response = await api.put<ApiResponse<ParseRuleResponse>>(`/rules/${ruleId}`, request)
  return response.data
}

export const deleteRule = async (ruleId: string): Promise<ApiResponse<null>> => {
  const response = await api.delete<ApiResponse<null>>(`/rules/${ruleId}`)
  return response.data
}

export const getIgnoreRules = async (): Promise<ApiResponse<{ rules: IgnoreRuleResponse[] }>> => {
  const response = await api.get<ApiResponse<{ rules: IgnoreRuleResponse[] }>>('/ignore-rules')
  return response.data
}

export const createIgnoreRule = async (
  request: CreateIgnoreRuleRequest
): Promise<ApiResponse<IgnoreRuleResponse>> => {
  const response = await api.post<ApiResponse<IgnoreRuleResponse>>('/ignore-rules', request)
  return response.data
}

export const deleteIgnoreRule = async (ruleId: string): Promise<ApiResponse<null>> => {
  const response = await api.delete<ApiResponse<null>>(`/ignore-rules/${ruleId}`)
  return response.data
}

// ============ 003-log-analysis-pipeline 新增 API ============

export const startClassification = async (
  request: ClassificationStartRequest
): Promise<ApiResponse<ClassificationStartResponse>> => {
  const response = await api.post<ApiResponse<ClassificationStartResponse>>('/classification/start', request)
  return response.data
}

export const getClassificationProgress = async (
  sessionId: string
): Promise<ApiResponse<ClassificationProgressResponse>> => {
  const response = await api.get<ApiResponse<ClassificationProgressResponse>>(`/classification/${sessionId}/progress`)
  return response.data
}

export const getClassificationResult = async (
  sessionId: string
): Promise<ApiResponse<ClassificationResultResponse>> => {
  const response = await api.get<ApiResponse<ClassificationResultResponse>>(`/classification/${sessionId}/result`)
  return response.data
}

export default api
