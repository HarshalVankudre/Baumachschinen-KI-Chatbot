// User Authentication
export interface User {
  user_id: string;
  username: string;
  email: string;
  authorization_level: 'regular' | 'superuser' | 'admin';
  account_status?: 'active' | 'suspended' | 'pending_verification' | 'pending_approval' | 'rejected';
  email_verified?: boolean;
  created_at?: string;
  last_login?: string;
}

// Backend returns User directly, not wrapped
export type LoginResponse = User;

// Chat
export interface Message {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  edited?: boolean;
  metadata?: {
    sources?: string[];
    response_time_ms?: number;
    token_count?: number;
  };
}

export interface Conversation {
  conversation_id: string;
  title: string;
  message_count: number;
  last_message_at: string;
  created_at: string;
  messages?: Message[];
}

// Documents
export interface Document {
  document_id: string;
  filename: string;
  category: string;
  upload_date: string;
  uploader_name?: string;
  uploader_id?: string;
  file_size_bytes: number;
  chunk_count?: number;
  processing_status: 'uploading' | 'processing' | 'completed' | 'failed';
  processing_step?: string;
  processing_progress?: number;
  error_message?: string;
}

// Admin
export interface PendingUser {
  user_id: string;
  username: string;
  email: string;
  created_at: string;
  email_verified: boolean;
}

// API Responses
export interface ApiError {
  error: string;
  message?: string;
  details?: any;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Settings
export interface UserSettings {
  language: 'en' | 'es' | 'fr' | 'de';
  email_notifications: boolean;
}

// Data Upload Types
export type UploadType = 'documents' | 'machinery';

export interface ProcessingStage {
  key: string;
  label: string;
  icon: string;
}

export interface MachineryUploadResponse {
  success: boolean;
  message: string;
  machines_added: number;
  relationships_created: number;
  embeddings_generated?: number;
  processing_time_seconds?: number;
}
