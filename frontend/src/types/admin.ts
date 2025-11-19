/**
 * Admin-specific type definitions for the Building Machinery AI Chatbot frontend.
 *
 * This module provides type definitions for admin panel components including:
 * - User management types
 * - Document management types
 * - Audit log types
 * - Admin-specific API responses
 */

import type { User, Document, PaginatedResponse } from './index';

// =============================================================================
// User Management Types
// =============================================================================

/**
 * User management filter parameters
 */
export interface UserFilterParams {
  search?: string;
  status?: string;
  authorization_level?: string;
  page?: number;
  per_page?: number;
}

/**
 * User update payloads
 */
export interface UpdateUserAuthorizationPayload {
  userId: string;
  level: 'regular' | 'superuser' | 'admin';
}

export interface UpdateUserStatusPayload {
  userId: string;
  status: 'active' | 'suspended';
}

/**
 * Extended user information for admin panel
 */
export interface AdminUserDetails extends User {
  created_at: string;
  last_login?: string;
  email_verified: boolean;
  total_conversations?: number;
  total_messages?: number;
}

/**
 * User statistics for dashboard
 */
export interface UserStatistics {
  total_users: number;
  active_users: number;
  suspended_users: number;
  pending_users: number;
  new_users_this_month: number;
  users_by_level: {
    regular: number;
    superuser: number;
    admin: number;
  };
}

// =============================================================================
// Document Management Types
// =============================================================================

/**
 * Document filter parameters
 */
export interface DocumentFilterParams {
  category?: string;
  search?: string;
  uploaded_by?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

/**
 * Document upload progress
 */
export interface DocumentUploadProgress {
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  step?: string;
  message?: string;
}

/**
 * Extended document information
 */
export interface AdminDocumentDetails extends Document {
  processing_time_seconds?: number;
  vector_count?: number;
  last_accessed?: string;
}

/**
 * Document statistics
 */
export interface DocumentStatistics {
  total_documents: number;
  total_size_mb: number;
  documents_by_category: Record<string, number>;
  documents_by_status: {
    completed: number;
    processing: number;
    failed: number;
  };
  average_processing_time_seconds: number;
  documents_uploaded_this_month: number;
}

/**
 * Document processing event (SSE)
 */
export interface DocumentProcessingEvent {
  type?: 'connected' | 'done' | 'error' | 'progress';
  document_id?: string;
  processing_status?: 'uploading' | 'processing' | 'completed' | 'failed';
  processing_step?: string;
  processing_progress?: number;
  chunk_count?: number;
  error_message?: string;
  message?: string;
}

// =============================================================================
// Audit Log Types
// =============================================================================

/**
 * Audit log entry
 */
export interface AuditLog {
  log_id: string;
  timestamp: string;
  admin_user_id: string;
  admin_username: string;
  action_type: AuditActionType;
  target_user_id?: string;
  target_username?: string;
  details?: Record<string, any>;
}

/**
 * Audit log action types
 */
export type AuditActionType =
  | 'create_user'
  | 'update_user_authorization'
  | 'update_user_status'
  | 'delete_user'
  | 'upload_document'
  | 'delete_document'
  | 'delete_conversation';

/**
 * Audit log filter parameters
 */
export interface AuditLogFilterParams {
  action_type?: AuditActionType;
  admin_user_id?: string;
  target_user_id?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  per_page?: number;
}

// =============================================================================
// Dashboard Types
// =============================================================================

/**
 * Admin dashboard summary
 */
export interface AdminDashboardSummary {
  user_stats: UserStatistics;
  document_stats: DocumentStatistics;
  system_health: SystemHealth;
  recent_activity: RecentActivity[];
}

/**
 * System health indicators
 */
export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down';
  database_status: 'connected' | 'disconnected';
  vector_db_status: 'connected' | 'disconnected';
  openai_status: 'available' | 'unavailable';
  last_check: string;
  uptime_seconds: number;
}

/**
 * Recent activity item
 */
export interface RecentActivity {
  id: string;
  type: 'user_login' | 'document_upload' | 'admin_action';
  user: string;
  action: string;
  timestamp: string;
  details?: string;
}

// =============================================================================
// Component State Types
// =============================================================================

/**
 * Dialog state for user authorization change
 */
export interface ChangeAuthDialogState {
  open: boolean;
  user: User | null;
  newLevel: 'regular' | 'superuser' | 'admin' | null;
}

/**
 * Dialog state for user suspension
 */
export interface SuspendDialogState {
  open: boolean;
  user: User | null;
  action: 'suspend' | 'activate' | null;
}

/**
 * Document upload form state
 */
export interface DocumentUploadFormState {
  selectedFile: File | null;
  category: string;
  uploadProgress: number;
  isUploading: boolean;
  error: string | null;
}

/**
 * Table sort state
 */
export interface TableSortState {
  column: string;
  direction: 'asc' | 'desc';
}

/**
 * Pagination state
 */
export interface PaginationState {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

// =============================================================================
// API Response Types
// =============================================================================

/**
 * User list API response
 */
export type UserListResponse = PaginatedResponse<User>;

/**
 * Document list API response
 */
export type DocumentListResponse = PaginatedResponse<Document>;

/**
 * Audit log list API response
 */
export type AuditLogListResponse = PaginatedResponse<AuditLog>;

/**
 * Generic action response
 */
export interface ActionResponse {
  success: boolean;
  message: string;
  data?: any;
}

/**
 * Document upload response
 */
export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  status: string;
  chunk_count?: number;
  error_message?: string;
  message: string;
}

/**
 * Document delete response
 */
export interface DocumentDeleteResponse {
  success: boolean;
  message: string;
  document_id: string;
}

/**
 * User authorization update response
 */
export interface UserAuthUpdateResponse {
  success: boolean;
  message: string;
  user_id: string;
  new_level: string;
}

/**
 * User status update response
 */
export interface UserStatusUpdateResponse {
  success: boolean;
  message: string;
  user_id: string;
  new_status: string;
}

// =============================================================================
// Form Types
// =============================================================================

/**
 * User filter form values
 */
export interface UserFilterFormValues {
  search: string;
  statusFilter: string;
  levelFilter: string;
}

/**
 * Document filter form values
 */
export interface DocumentFilterFormValues {
  search: string;
  categoryFilter: string;
  uploaderFilter: string;
  dateRange: {
    start: Date | null;
    end: Date | null;
  };
}

/**
 * Audit log filter form values
 */
export interface AuditLogFilterFormValues {
  actionTypeFilter: string;
  adminUserFilter: string;
  dateRange: {
    start: Date | null;
    end: Date | null;
  };
}

// =============================================================================
// Utility Types
// =============================================================================

/**
 * Authorization level with display info
 */
export interface AuthorizationLevelOption {
  value: 'regular' | 'superuser' | 'admin';
  label: string;
  description: string;
  color: string;
}

/**
 * Account status with display info
 */
export interface AccountStatusOption {
  value: string;
  label: string;
  description: string;
  color: string;
}

/**
 * Document category with display info
 */
export interface DocumentCategoryOption {
  value: string;
  label: string;
  description: string;
  icon?: string;
}

/**
 * Processing status with display info
 */
export interface ProcessingStatusInfo {
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  label: string;
  color: string;
  icon: 'loading' | 'check' | 'error';
}

// =============================================================================
// Data Upload Types
// =============================================================================

/**
 * Upload type for data ingestion
 */
export type UploadType = 'documents' | 'machinery';

/**
 * Processing stage information
 */
export interface ProcessingStage {
  key: string;
  label: string;
  icon: string;
}

/**
 * Machinery upload response
 */
export interface MachineryUploadResponse {
  success: boolean;
  message: string;
  machines_added: number;
  relationships_created: number;
  embeddings_generated?: number;
  processing_time_seconds?: number;
}

// =============================================================================
// Constants
// =============================================================================

/**
 * Authorization level options for dropdowns
 */
export const AUTHORIZATION_LEVEL_OPTIONS: AuthorizationLevelOption[] = [
  {
    value: 'regular',
    label: 'Normaler Benutzer',
    description: 'Standard-Benutzer mit eingeschränkten Berechtigungen',
    color: 'blue',
  },
  {
    value: 'superuser',
    label: 'Superuser',
    description: 'Erweiterte Berechtigungen für Dokumentverwaltung',
    color: 'purple',
  },
  {
    value: 'admin',
    label: 'Admin',
    description: 'Vollständiger Zugriff auf alle Funktionen',
    color: 'orange',
  },
];

/**
 * Document category options
 */
export const DOCUMENT_CATEGORY_OPTIONS: DocumentCategoryOption[] = [
  { value: 'manuals', label: 'Handbücher', description: 'Bedienungsanleitungen' },
  { value: 'specifications', label: 'Spezifikationen', description: 'Technische Daten' },
  { value: 'guides', label: 'Anleitungen', description: 'Schritt-für-Schritt-Anleitungen' },
  { value: 'reports', label: 'Berichte', description: 'Analyseberichte und Dokumentation' },
  { value: 'other', label: 'Sonstiges', description: 'Andere Dokumente' },
];

/**
 * Allowed file extensions
 */
export const ALLOWED_FILE_EXTENSIONS = [
  '.pdf',
  '.docx',
  '.pptx',
  '.xlsx',
  '.xls',
  '.ppt',
  '.jpg',
  '.jpeg',
  '.png',
  '.gif',
];

/**
 * Maximum upload size in MB
 */
export const MAX_UPLOAD_SIZE_MB = 100;

/**
 * Default pagination settings
 */
export const DEFAULT_PAGE_SIZE = 50;
export const MAX_PAGE_SIZE = 100;
