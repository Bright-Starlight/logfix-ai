export interface UploadResponse {
  file_id: string
  filename: string
  file_size: number
  encoding: string
  preview_lines: number
  upload_id: string
}

export interface FilePreviewResponse {
  file_id: string
  filename: string
  total_lines: number
  preview: string[]
  encoding: string
}

export interface SplitRequest {
  file_id: string
  rule_type: 'regex' | 'fixed_string'
  rule_content: string
}

export interface SplitResponse {
  session_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  estimated_chunks: number
}

export interface SessionStatus {
  session_id: string
  file_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_chunks: number
  processed_chunks: number
  progress_percent: number
  created_at: string
  updated_at: string
}

export interface SplitResult {
  chunk_index: number
  start_line: number
  end_line: number
  content: string
}

export interface ResultsResponse {
  session_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_chunks: number
  page: number
  page_size: number
  total_pages: number
  results: SplitResult[]
}

export interface RegexValidationRequest {
  pattern: string
}

export interface RegexValidationResponse {
  valid: boolean
  sample_matches: number
}

export interface ApiError {
  code: string
  message: string
}

export interface ApiResponse<T> {
  success: boolean
  data: T | null
  error: ApiError | null
}
