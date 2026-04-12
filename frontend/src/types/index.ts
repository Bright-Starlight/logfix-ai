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

export interface FileListItem {
  id: string
  filename: string
  file_size: number
  encoding: string
  created_at: string
}

export interface SessionListItem {
  id: string
  file_id: string
  rule_type: string
  rule_content: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_chunks: number
  processed_chunks: number
  has_classification: boolean
  created_at: string
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

// ============ 002-short-name-structured 新增类型 ============

export interface LogEntryResponse {
  id: string
  original_message?: string
  normalized_message: string
  stack_trace?: string
  category?: string
  error_type?: string
  extracted_params?: Record<string, unknown>
  log_level?: string
  occurrence_count: number
  first_seen_at?: string
  last_seen_at?: string
}

export interface ClassifyRequest {
  logs: string[]
  mode: 'rule_engine' | 'ai'
  file_id?: string
}

export interface ClassifyResponse {
  processed: number
  new_entries: number
  duplicates: number
  entries: LogEntryResponse[]
}

export interface LogListItemResponse {
  id: string
  normalized_message: string
  stack_trace?: string
  category?: string
  error_type?: string
  log_level?: string
  occurrence_count: number
  first_seen_at?: string
  last_seen_at?: string
}

export interface LogListResponse {
  total: number
  page: number
  page_size: number
  total_pages: number
  entries: LogListItemResponse[]
}

export interface LogDetailResponse {
  id: string
  original_message?: string
  normalized_message: string
  stack_trace?: string
  category?: string
  category_id?: string
  error_type?: string
  extracted_params?: Record<string, unknown>
  log_level?: string
  occurrence_count: number
  first_seen_at?: string
  last_seen_at?: string
}

export interface CategoryStatsResponse {
  name: string
  count: number
  percentage: number
}

export interface DailyTrendResponse {
  date: string
  count: number
}

export interface StatsResponse {
  total_entries: number
  unique_errors: number
  categories: CategoryStatsResponse[]
  daily_trend: DailyTrendResponse[]
}

export interface ParseRuleResponse {
  id: string
  name: string
  rule_type: 'regex' | 'code'
  pattern?: string
  code?: string
  priority: number
  enabled: boolean
  is_system: boolean
}

export interface ParseRuleListResponse {
  rules: ParseRuleResponse[]
}

export interface CreateParseRuleRequest {
  name: string
  rule_type: 'regex' | 'code'
  pattern?: string
  code?: string
  group_index?: number
  priority?: number
  enabled?: boolean
}

export interface UpdateParseRuleRequest {
  name?: string
  pattern?: string
  code?: string
  priority?: number
  enabled?: boolean
}

export interface IgnoreRuleResponse {
  id: string
  name: string
  match_type: 'contains' | 'regex' | 'exact'
  pattern: string
  description?: string
  enabled: boolean
}

export interface IgnoreRuleListResponse {
  rules: IgnoreRuleResponse[]
}

export interface CreateIgnoreRuleRequest {
  name: string
  match_type: 'contains' | 'regex' | 'exact'
  pattern: string
  description?: string
  enabled?: boolean
}

// ============ 004-ai-tool-call-streaming SSE 类型 ============

export interface SSEProgressEvent {
  processed: number
  total: number
  percentage: number
}

export interface SSEResultEvent {
  index: number
  category: string
  error_type?: string
  normalized_message: string
  extracted_params: Record<string, unknown>
}

export interface SSEErrorEvent {
  code: string
  message: string
  index?: number
  processed_at_cancel?: number
  batch?: number
}

export interface SSEDoneEvent {
  total_processed: number
  success_count: number
  error_count: number
}

export interface ClassificationStartRequest {
  split_session_id: string
  mode: ClassificationMode
}

// ============ 004-ai-tool-call-streaming 新增类型 ============

export type ClassificationMode = 'rule_engine' | 'ai'

export interface ClassificationStartResponse {
  session_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
}

export interface ClassificationProgressResponse {
  session_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_items: number
  processed_items: number
  current_phase: string
  estimated_remaining_seconds?: number
  progress_percent: number
}

export interface ClassificationResultResponse {
  session_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_items: number
  processed_items: number
  new_entries: number
  duplicates: number
  ignored: number
  completed_at?: string
}

// 用于 ProgressBar 组件的状态类型
export interface ClassificationProgressState {
  status: 'pending' | 'processing' | 'completed' | 'failed'
  totalItems: number
  processedItems: number
  currentPhase: string
  estimatedRemainingSeconds?: number
  progressPercent: number
  error?: string
  result?: {
    new_entries: number
    duplicates: number
    ignored: number
  }
}
