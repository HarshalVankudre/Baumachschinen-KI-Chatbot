/**
 * Application-wide constants for the Building Machinery AI Chatbot frontend.
 *
 * This module centralizes all constant values for easy maintenance and consistency.
 *
 * Categories:
 * - API Configuration
 * - UI Configuration
 * - Timeouts and Delays
 * - File Upload
 * - Pagination
 * - Validation
 */

// =============================================================================
// API Configuration
// =============================================================================

/**
 * API base URL from environment or default to localhost
 */
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * API endpoints
 */
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout',
    REGISTER: '/api/auth/register',
    ME: '/api/auth/me',
    VERIFY_EMAIL: '/api/auth/verify-email',
    RESEND_VERIFICATION: '/api/auth/resend-verification',
    FORGOT_PASSWORD: '/api/auth/forgot-password',
    RESET_PASSWORD: '/api/auth/reset-password',
  },

  // Chat
  CHAT: {
    CONVERSATIONS: '/api/conversations',
    MESSAGES: (conversationId: string) => `/api/conversations/${conversationId}/messages`,
    SEND_MESSAGE: (conversationId: string) => `/api/conversations/${conversationId}/messages`,
    DELETE_CONVERSATION: (conversationId: string) => `/api/conversations/${conversationId}`,
  },

  // Documents
  DOCUMENTS: {
    LIST: '/api/documents',
    UPLOAD: '/api/documents/upload',
    DELETE: (documentId: string) => `/api/documents/${documentId}`,
    STREAM: (documentId: string) => `/api/documents/stream/${documentId}`,
  },

  // Admin
  ADMIN: {
    USERS: '/api/admin/users',
    USER_DETAILS: (userId: string) => `/api/admin/users/${userId}`,
    UPDATE_USER_AUTH: (userId: string) => `/api/admin/users/${userId}/authorization`,
    UPDATE_USER_STATUS: (userId: string) => `/api/admin/users/${userId}/status`,
    DELETE_USER: (userId: string) => `/api/admin/users/${userId}`,
    AUDIT_LOGS: '/api/admin/audit-logs',
    STATISTICS: '/api/admin/statistics',
  },
};

/**
 * API request timeouts (milliseconds)
 */
export const API_TIMEOUTS = {
  DEFAULT: 30000, // 30 seconds
  UPLOAD: 300000, // 5 minutes
  CHAT: 60000, // 1 minute
  SEARCH: 15000, // 15 seconds
};

/**
 * Retry configuration
 */
export const API_RETRY = {
  MAX_ATTEMPTS: 3,
  BACKOFF_FACTOR: 2,
  MAX_DELAY: 30000, // 30 seconds
};

// =============================================================================
// UI Configuration
// =============================================================================

/**
 * Application branding
 */
export const APP_NAME = 'Building Machinery AI';
export const APP_SHORT_NAME = 'BM AI';
export const APP_DESCRIPTION = 'AI-Powered Chatbot for Building Machinery Support';

/**
 * Theme configuration
 */
export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system',
} as const;

/**
 * Breakpoints for responsive design (pixels)
 */
export const BREAKPOINTS = {
  XS: 320,
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  '2XL': 1536,
};

/**
 * Z-index layers
 */
export const Z_INDEX = {
  DROPDOWN: 1000,
  STICKY: 1020,
  FIXED: 1030,
  MODAL_BACKDROP: 1040,
  MODAL: 1050,
  POPOVER: 1060,
  TOOLTIP: 1070,
};

// =============================================================================
// Timeouts and Delays
// =============================================================================

/**
 * Debounce delays (milliseconds)
 */
export const DEBOUNCE_DELAYS = {
  SEARCH: 300,
  INPUT: 500,
  RESIZE: 150,
  SCROLL: 100,
};

/**
 * Animation durations (milliseconds)
 */
export const ANIMATION_DURATIONS = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
};

/**
 * Auto-save intervals (milliseconds)
 */
export const AUTOSAVE_INTERVALS = {
  DRAFT: 30000, // 30 seconds
  PREFERENCES: 5000, // 5 seconds
};

/**
 * Toast/notification durations (milliseconds)
 */
export const TOAST_DURATIONS = {
  SHORT: 2000,
  NORMAL: 4000,
  LONG: 6000,
  PERSISTENT: 0, // Doesn't auto-dismiss
};

/**
 * Polling intervals (milliseconds)
 */
export const POLLING_INTERVALS = {
  FAST: 1000, // 1 second
  NORMAL: 5000, // 5 seconds
  SLOW: 30000, // 30 seconds
};

/**
 * Session and persistence
 */
export const SESSION_CONFIG = {
  PERSIST_DELAY: 100, // Delay before persisting to storage (ms)
  IDLE_TIMEOUT: 1800000, // 30 minutes
  CHECK_INTERVAL: 60000, // Check every minute
};

// =============================================================================
// File Upload Configuration
// =============================================================================

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
 * File upload limits
 */
export const UPLOAD_LIMITS = {
  MAX_SIZE_MB: 100,
  MAX_SIZE_BYTES: 100 * 1024 * 1024,
  CHUNK_SIZE: 1024 * 1024, // 1MB chunks for large files
};

/**
 * Document categories
 */
export const DOCUMENT_CATEGORIES = {
  MANUALS: 'manuals',
  SPECIFICATIONS: 'specifications',
  GUIDES: 'guides',
  REPORTS: 'reports',
  OTHER: 'other',
} as const;

/**
 * Document category labels (German)
 */
export const DOCUMENT_CATEGORY_LABELS = {
  manuals: 'Handbücher',
  specifications: 'Spezifikationen',
  guides: 'Anleitungen',
  reports: 'Berichte',
  other: 'Sonstiges',
};

// =============================================================================
// Pagination Configuration
// =============================================================================

/**
 * Default pagination settings
 */
export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_PAGE_SIZE: 50,
  MAX_PAGE_SIZE: 100,
  MIN_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [10, 25, 50, 100],
};

/**
 * Infinite scroll configuration
 */
export const INFINITE_SCROLL = {
  THRESHOLD: 0.8, // Load more when 80% scrolled
  BATCH_SIZE: 20,
};

// =============================================================================
// Validation Rules
// =============================================================================

/**
 * Password requirements
 */
export const PASSWORD_VALIDATION = {
  MIN_LENGTH: 8,
  MAX_LENGTH: 128,
  REQUIRE_UPPERCASE: true,
  REQUIRE_LOWERCASE: true,
  REQUIRE_NUMBER: true,
  REQUIRE_SPECIAL: false,
};

/**
 * Username requirements
 */
export const USERNAME_VALIDATION = {
  MIN_LENGTH: 3,
  MAX_LENGTH: 50,
  PATTERN: /^[a-zA-Z0-9_-]+$/,
  RESERVED_NAMES: ['admin', 'root', 'system', 'api', 'test'],
};

/**
 * Email validation
 */
export const EMAIL_VALIDATION = {
  PATTERN: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
};

/**
 * Message validation
 */
export const MESSAGE_VALIDATION = {
  MIN_LENGTH: 1,
  MAX_LENGTH: 4000,
};

// =============================================================================
// Chat Configuration
// =============================================================================

/**
 * Chat settings
 */
export const CHAT_CONFIG = {
  MAX_CONVERSATION_TITLE_LENGTH: 100,
  DEFAULT_CONVERSATION_TITLE: 'Neue Unterhaltung',
  MAX_MESSAGE_LENGTH: 4000,
  TYPING_INDICATOR_DELAY: 300,
  MESSAGE_BATCH_SIZE: 50,
  AUTO_SCROLL_THRESHOLD: 100, // pixels from bottom
};

/**
 * Streaming configuration
 */
export const STREAMING_CONFIG = {
  ENABLE_STREAMING: true,
  CHUNK_DELAY: 30, // Delay between chunks (ms)
};

// =============================================================================
// SSE Configuration
// =============================================================================

/**
 * Server-Sent Events configuration
 */
export const SSE_CONFIG = {
  MAX_RECONNECT_ATTEMPTS: 5,
  BASE_RECONNECT_DELAY: 1000, // 1 second
  MAX_RECONNECT_DELAY: 30000, // 30 seconds
  HEARTBEAT_INTERVAL: 30000, // 30 seconds
};

// =============================================================================
// Cache Configuration
// =============================================================================

/**
 * React Query cache times (milliseconds)
 */
export const CACHE_TIMES = {
  CONVERSATIONS: 300000, // 5 minutes
  MESSAGES: 60000, // 1 minute
  DOCUMENTS: 60000, // 1 minute
  USERS: 300000, // 5 minutes
  USER_PROFILE: 600000, // 10 minutes
  STATISTICS: 300000, // 5 minutes
};

/**
 * Stale times (how long data is considered fresh)
 */
export const STALE_TIMES = {
  STATIC: Infinity, // Never stale
  LONG: 600000, // 10 minutes
  MEDIUM: 300000, // 5 minutes
  SHORT: 60000, // 1 minute
};

// =============================================================================
// Authorization
// =============================================================================

/**
 * Authorization levels
 */
export const AUTH_LEVELS = {
  REGULAR: 'regular',
  SUPERUSER: 'superuser',
  ADMIN: 'admin',
} as const;

/**
 * Authorization level hierarchy (for permission checks)
 */
export const AUTH_HIERARCHY = {
  regular: 1,
  superuser: 2,
  admin: 3,
};

/**
 * Account statuses
 */
export const ACCOUNT_STATUSES = {
  ACTIVE: 'active',
  SUSPENDED: 'suspended',
  PENDING_VERIFICATION: 'pending_verification',
  PENDING_APPROVAL: 'pending_approval',
  REJECTED: 'rejected',
} as const;

// =============================================================================
// Status Translations (German)
// =============================================================================

/**
 * Account status labels
 */
export const STATUS_LABELS = {
  active: 'Aktiv',
  suspended: 'Gesperrt',
  pending_verification: 'E-Mail-Verifizierung ausstehend',
  pending_approval: 'Genehmigung ausstehend',
  rejected: 'Abgelehnt',
};

/**
 * Processing status labels
 */
export const PROCESSING_STATUS_LABELS = {
  uploading: 'Wird hochgeladen',
  processing: 'Wird verarbeitet',
  completed: 'Abgeschlossen',
  failed: 'Fehlgeschlagen',
};

/**
 * Authorization level labels
 */
export const AUTH_LEVEL_LABELS = {
  regular: 'Normaler Benutzer',
  superuser: 'Superuser',
  admin: 'Admin',
};

// =============================================================================
// Error Messages
// =============================================================================

/**
 * Error message templates
 */
export const ERROR_MESSAGES = {
  NETWORK: 'Netzwerkfehler. Bitte überprüfen Sie Ihre Internetverbindung.',
  TIMEOUT: 'Anfrage-Timeout. Bitte versuchen Sie es erneut.',
  UNAUTHORIZED: 'Nicht autorisiert. Bitte melden Sie sich an.',
  FORBIDDEN: 'Zugriff verweigert. Unzureichende Berechtigungen.',
  NOT_FOUND: 'Ressource nicht gefunden.',
  SERVER_ERROR: 'Serverfehler. Bitte versuchen Sie es später erneut.',
  VALIDATION: 'Validierungsfehler. Bitte überprüfen Sie Ihre Eingaben.',
  FILE_TOO_LARGE: `Datei zu groß. Maximale Größe: ${UPLOAD_LIMITS.MAX_SIZE_MB}MB`,
  INVALID_FILE_TYPE: 'Ungültiger Dateityp.',
  UPLOAD_FAILED: 'Upload fehlgeschlagen. Bitte versuchen Sie es erneut.',
};

/**
 * Success message templates
 */
export const SUCCESS_MESSAGES = {
  LOGIN: 'Erfolgreich angemeldet.',
  LOGOUT: 'Erfolgreich abgemeldet.',
  REGISTER: 'Registrierung erfolgreich.',
  DOCUMENT_UPLOADED: 'Dokument erfolgreich hochgeladen.',
  DOCUMENT_DELETED: 'Dokument erfolgreich gelöscht.',
  USER_UPDATED: 'Benutzer erfolgreich aktualisiert.',
  PASSWORD_CHANGED: 'Passwort erfolgreich geändert.',
  EMAIL_VERIFIED: 'E-Mail erfolgreich verifiziert.',
};

// =============================================================================
// Local Storage Keys
// =============================================================================

/**
 * Keys for local storage
 */
export const STORAGE_KEYS = {
  AUTH_STATE: 'auth-storage',
  THEME: 'theme-preference',
  LANGUAGE: 'language-preference',
  SIDEBAR_STATE: 'sidebar-collapsed',
  RECENT_SEARCHES: 'recent-searches',
  DRAFT_MESSAGES: 'draft-messages',
};

// =============================================================================
// Feature Flags
// =============================================================================

/**
 * Feature flags for enabling/disabling features
 */
export const FEATURES = {
  ENABLE_REGISTRATION: true,
  ENABLE_EMAIL_VERIFICATION: true,
  ENABLE_ADMIN_APPROVAL: false,
  ENABLE_DARK_MODE: true,
  ENABLE_MULTILINGUAL: false,
  ENABLE_DOCUMENT_UPLOAD: true,
  ENABLE_SSE_UPDATES: true,
  ENABLE_STREAMING_RESPONSES: true,
};

// =============================================================================
// Development Configuration
// =============================================================================

/**
 * Development mode flag
 */
export const IS_DEVELOPMENT = import.meta.env.DEV;

/**
 * Debug logging flag
 */
export const ENABLE_DEBUG_LOGS = IS_DEVELOPMENT;

/**
 * Mock data flag (for testing without backend)
 */
export const USE_MOCK_DATA = false;

// =============================================================================
// Type Exports
// =============================================================================

export type Theme = typeof THEMES[keyof typeof THEMES];
export type AuthLevel = typeof AUTH_LEVELS[keyof typeof AUTH_LEVELS];
export type AccountStatus = typeof ACCOUNT_STATUSES[keyof typeof ACCOUNT_STATUSES];
export type DocumentCategory = typeof DOCUMENT_CATEGORIES[keyof typeof DOCUMENT_CATEGORIES];
