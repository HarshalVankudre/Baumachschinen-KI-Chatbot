"""
Common type definitions for the Building Machinery AI Chatbot backend.

This module provides shared type definitions and enums used across
the application for consistency and type safety.

Types included:
- User authorization levels
- Account statuses
- Document processing statuses
- Common response types
- Pagination types
"""
from enum import Enum
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime


# =============================================================================
# Enums
# =============================================================================

class AuthorizationLevel(str, Enum):
    """User authorization levels"""
    REGULAR = "regular"
    SUPERUSER = "superuser"
    ADMIN = "admin"


class AccountStatus(str, Enum):
    """User account statuses"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    PENDING_APPROVAL = "pending_approval"
    REJECTED = "rejected"


class DocumentProcessingStatus(str, Enum):
    """Document processing status values"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentProcessingStep(str, Enum):
    """Document processing pipeline steps"""
    EXTRACTING_TEXT = "extracting_text"
    CHUNKING = "chunking"
    GENERATING_EMBEDDINGS = "generating_embeddings"
    STORING_VECTORS = "storing_vectors"


class DocumentCategory(str, Enum):
    """Document categories"""
    MANUALS = "manuals"
    SPECIFICATIONS = "specifications"
    GUIDES = "guides"
    REPORTS = "reports"
    OTHER = "other"


class MessageRole(str, Enum):
    """Chat message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AuditActionType(str, Enum):
    """Audit log action types"""
    # User management
    CREATE_USER = "create_user"
    UPDATE_USER_AUTH = "update_user_authorization"
    UPDATE_USER_STATUS = "update_user_status"
    DELETE_USER = "delete_user"

    # Document management
    UPLOAD_DOCUMENT = "upload_document"
    DELETE_DOCUMENT = "delete_document"

    # Conversation management
    DELETE_CONVERSATION = "delete_conversation"


# =============================================================================
# TypedDict Definitions
# =============================================================================

class UserDict(TypedDict, total=False):
    """Type definition for user document"""
    user_id: str
    username: str
    email: str
    password_hash: str
    authorization_level: str
    account_status: str
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    verification_token: Optional[str]
    verification_token_expires: Optional[datetime]
    password_reset_token: Optional[str]
    password_reset_expires: Optional[datetime]


class DocumentMetadataDict(TypedDict, total=False):
    """Type definition for document metadata"""
    document_id: str
    filename: str
    category: str
    uploader_id: str
    uploader_name: str
    upload_date: datetime
    file_size_bytes: int
    file_extension: str
    processing_status: str
    processing_step: Optional[str]
    processing_progress: Optional[int]
    chunk_count: Optional[int]
    processing_time_seconds: Optional[float]
    error_message: Optional[str]
    deleted: bool
    deleted_at: Optional[datetime]
    deleted_by: Optional[str]


class MessageDict(TypedDict, total=False):
    """Type definition for chat message"""
    message_id: str
    conversation_id: str
    role: str
    content: str
    timestamp: datetime
    edited: bool
    metadata: Optional[Dict[str, Any]]


class ConversationDict(TypedDict, total=False):
    """Type definition for conversation"""
    conversation_id: str
    user_id: str
    title: str
    created_at: datetime
    last_message_at: datetime
    message_count: int
    deleted: bool


class AuditLogDict(TypedDict, total=False):
    """Type definition for audit log entry"""
    log_id: str
    timestamp: datetime
    admin_user_id: str
    admin_username: str
    action_type: str
    target_user_id: Optional[str]
    target_username: Optional[str]
    details: Optional[Dict[str, Any]]


# =============================================================================
# Pagination Types
# =============================================================================

class PaginationParams(TypedDict, total=False):
    """Pagination parameters"""
    page: int
    per_page: int
    sort_by: Optional[str]
    sort_order: Optional[str]


class PaginatedResponse(TypedDict):
    """Generic paginated response structure"""
    items: List[Any]
    total: int
    page: int
    per_page: int
    total_pages: int


# =============================================================================
# API Response Types
# =============================================================================

class SuccessResponse(TypedDict):
    """Standard success response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]]


class ErrorResponse(TypedDict):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]]
    error_code: Optional[str]


class ValidationError(TypedDict):
    """Field validation error"""
    field: str
    message: str
    type: str


# =============================================================================
# Processing Types
# =============================================================================

class ProcessingProgress(TypedDict):
    """Document processing progress information"""
    document_id: str
    processing_status: str
    processing_step: Optional[str]
    processing_progress: int
    error_message: Optional[str]
    chunk_count: Optional[int]


class EmbeddingVector(TypedDict):
    """Embedding vector with metadata"""
    id: str
    values: List[float]
    metadata: Dict[str, Any]


# =============================================================================
# Search and Retrieval Types
# =============================================================================

class SearchResult(TypedDict):
    """Vector search result"""
    document_id: str
    filename: str
    category: str
    chunk_index: int
    text_content: str
    relevance_score: float


class RAGContext(TypedDict):
    """RAG (Retrieval-Augmented Generation) context"""
    query: str
    results: List[SearchResult]
    context_text: str
    source_documents: List[str]


# =============================================================================
# Configuration Types
# =============================================================================

class DatabaseConfig(TypedDict, total=False):
    """Database configuration"""
    uri: str
    database_name: str
    min_pool_size: int
    max_pool_size: int


class APIKeyConfig(TypedDict):
    """API key configuration by authorization level"""
    regular: str
    superuser: str
    admin: str


class SMTPConfig(TypedDict):
    """SMTP configuration for emails"""
    host: str
    port: int
    username: str
    password: str
    from_email: str
    from_name: str
    use_tls: bool


# =============================================================================
# Constants
# =============================================================================

# File upload limits
MAX_UPLOAD_SIZE_MB = 100
ALLOWED_FILE_EXTENSIONS = [
    ".pdf", ".docx", ".pptx", ".xlsx",
    ".xls", ".ppt", ".jpg", ".jpeg", ".png", ".gif"
]

# Pagination defaults
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

# Session settings
DEFAULT_SESSION_MAX_AGE = 2592000  # 30 days
SESSION_COOKIE_NAME = "session_id"

# Processing timeouts
DOCUMENT_PROCESSING_TIMEOUT_SECONDS = 3600  # 1 hour
ORPHANED_JOB_TIMEOUT_MINUTES = 30

# Rate limiting (requests per minute)
RATE_LIMIT_CHAT = 30
RATE_LIMIT_UPLOAD = 10
RATE_LIMIT_SEARCH = 60

# Text processing
DEFAULT_CHUNK_SIZE_TOKENS = 500
DEFAULT_CHUNK_OVERLAP_TOKENS = 50
MAX_METADATA_TEXT_LENGTH = 1000

# Vector search
DEFAULT_TOP_K_RESULTS = 5
MAX_TOP_K_RESULTS = 20
MIN_RELEVANCE_SCORE = 0.7

# API timeouts
DEFAULT_API_TIMEOUT_SECONDS = 30
OPENAI_API_TIMEOUT = 60

# Retry configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 2
RETRY_MAX_DELAY_SECONDS = 30


# =============================================================================
# Helper Functions
# =============================================================================

def is_valid_authorization_level(level: str) -> bool:
    """Check if authorization level is valid"""
    try:
        AuthorizationLevel(level)
        return True
    except ValueError:
        return False


def is_valid_account_status(status: str) -> bool:
    """Check if account status is valid"""
    try:
        AccountStatus(status)
        return True
    except ValueError:
        return False


def is_valid_processing_status(status: str) -> bool:
    """Check if processing status is valid"""
    try:
        DocumentProcessingStatus(status)
        return True
    except ValueError:
        return False


def get_authorization_level_hierarchy() -> Dict[str, int]:
    """
    Get authorization level hierarchy for permission checks.

    Returns:
        Dictionary mapping authorization levels to numeric hierarchy
        (higher number = more privileges)
    """
    return {
        AuthorizationLevel.REGULAR: 1,
        AuthorizationLevel.SUPERUSER: 2,
        AuthorizationLevel.ADMIN: 3,
    }


def has_permission(user_level: str, required_level: str) -> bool:
    """
    Check if user has required permission level.

    Args:
        user_level: User's authorization level
        required_level: Required authorization level

    Returns:
        True if user has sufficient permissions
    """
    hierarchy = get_authorization_level_hierarchy()
    user_rank = hierarchy.get(user_level, 0)
    required_rank = hierarchy.get(required_level, 0)
    return user_rank >= required_rank
