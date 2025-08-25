/**
 * TypeScript type definitions for the VILS application
 */

export interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  created_at: string
  updated_at: string
  avatar_url?: string
}

export interface AuthTokens {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token?: string
}

export interface Project {
  id: string
  name: string
  repository_url: string
  repository_type: 'gerrit' | 'repo' | 'codehub' | 'github' | 'gitlab'
  default_branch: string
  created_by: string
  created_at: string
  updated_at: string
  branches_count?: number
  tags_count?: number
}

export interface Branch {
  id: string
  project_id: string
  name: string
  last_commit_hash?: string
  last_sync_at?: string
  tags_count?: number
}

export interface Tag {
  id: string
  project_id: string
  branch_id: string
  name: string
  commit_hash: string
  tag_date?: string
  author_email?: string
  message?: string
  sequence_number?: number
}

export interface LocalizationTask {
  id: string
  user_id: string
  project_id: string
  branch_id: string
  task_name: string
  description?: string
  status: 'active' | 'paused' | 'completed' | 'failed'
  total_tags_in_range?: number
  current_iteration: number
  final_problematic_tag_id?: string
  resolution_notes?: string
  created_at: string
  updated_at: string
  completed_at?: string
  
  // Additional properties for compatibility
  current_candidates?: string[]
  problematic_commit?: string
  total_iterations?: number
  error_message?: string
  good_commit?: string
  bad_commit?: string
  
  // Populated relationships
  project_name?: string
  branch_name?: string
  project?: Project
  user?: User
  good_tag?: Tag
  bad_tag?: Tag
  final_problematic_tag?: Tag
}

export interface TaskIteration {
  id: string
  task_id: string
  iteration_number: number
  search_range_start: number
  search_range_end: number
  candidates_generated: Record<string, any>
  selected_candidates?: Record<string, any>
  created_at: string
  completed_at?: string
}

export interface BinarySearchCandidate {
  position: number
  tag: Tag
  selected: boolean
  result?: 'working' | 'broken' | 'inconclusive'
}

export interface BinarySearchCandidatesResponse {
  iteration_number: number
  current_range: {
    start: number
    end: number
  }
  candidates: BinarySearchCandidate[]
  total_tags: number
  is_complete?: boolean
  problematic_tag?: Tag
}

export interface BuildJob {
  id: string
  task_id: string
  iteration_id: string
  tag_id: string
  external_build_id?: string
  build_service: 'jenkins' | 'github_actions' | 'gitlab_ci'
  build_url?: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  logs_url?: string
  artifacts_url?: string
  started_at?: string
  completed_at?: string
  created_at: string
  tag_name?: string
}

export interface UserFeedback {
  id: string
  task_id: string
  iteration_id: string
  build_job_id: string
  tag_id: string
  feedback_type: 'working' | 'broken' | 'inconclusive'
  notes?: string
  created_by: string
  created_at: string
}

export interface ApiResponse<T> {
  data: T
  message?: string
  status: number
}

export interface PaginationParams {
  skip?: number
  limit?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
  has_next: boolean
  has_prev: boolean
}

// WebSocket message types
export interface WebSocketMessage {
  type: string
  [key: string]: any
}

export interface TaskUpdateMessage extends WebSocketMessage {
  type: 'task_update'
  task_id: string
  update_type: string
  data: Record<string, any>
  timestamp: string
}

export interface BuildUpdateMessage extends WebSocketMessage {
  type: 'build_update'
  build_id: string
  task_id: string
  status: string
  data: Record<string, any>
  timestamp: string
}

export interface ProgressUpdateMessage extends WebSocketMessage {
  type: 'progress_update'
  task_id: string
  progress: Record<string, any>
  timestamp: string
}

// Form types
export interface LoginForm {
  username: string
  password: string
}

export interface RegisterForm {
  email: string
  username: string
  password: string
}

export interface ProjectForm {
  name: string
  repository_url: string
  repository_type: string
  default_branch: string
}

export interface TaskForm {
  project_id: string
  branch_id: string
  task_name: string
  description?: string
  good_tag_name: string
  bad_tag_name: string
}

// UI State types
export interface LoadingState {
  [key: string]: boolean
}

export interface ErrorState {
  [key: string]: string | null
}

export interface NotificationAction {
  label: string
  callback: () => void
  primary?: boolean
}

export interface NotificationState {
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  id: string
  duration?: number
  actions?: NotificationAction[]
  persistent?: boolean
  timestamp?: string
}

// Statistics and dashboard types
export interface DashboardStats {
  active_tasks: number
  completed_today: number
  total_tasks: number
  success_rate: number
}

export interface ActivityItem {
  id: string
  type: string
  title: string
  description: string
  timestamp: string
  metadata?: Record<string, any>
}

// Search and filter types
export interface TaskFilters {
  status?: string
  project_id?: string
  search?: string
}

export interface ProjectFilters {
  search?: string
  repository_type?: string
}

// Export utility types
export type TaskStatus = LocalizationTask['status']
export type BuildStatus = BuildJob['status']
export type FeedbackType = UserFeedback['feedback_type']
export type RepositoryType = Project['repository_type']