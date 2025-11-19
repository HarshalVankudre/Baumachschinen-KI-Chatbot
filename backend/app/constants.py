"""
Application-wide constants for the Building Machinery AI Chatbot backend.

This module centralizes all constant values used throughout the application
for easy maintenance and consistency.

Categories:
- API Configuration
- File Upload
- Database
- Processing
- Security
- Performance
"""

# =============================================================================
# API Configuration
# =============================================================================

# API versioning
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# API timeouts (seconds)
DEFAULT_API_TIMEOUT = 30
OPENAI_API_TIMEOUT = 60
PINECONE_API_TIMEOUT = 30

# Rate limiting (requests per minute)
RATE_LIMIT_CHAT = 30
RATE_LIMIT_UPLOAD = 10
RATE_LIMIT_SEARCH = 60
RATE_LIMIT_AUTH = 5
RATE_LIMIT_ADMIN = 100

# =============================================================================
# File Upload Constants
# =============================================================================

# File size limits
MAX_UPLOAD_SIZE_MB = 100
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Allowed file extensions
ALLOWED_FILE_EXTENSIONS = [
    '.pdf',
    '.docx',
    '.pptx',
    '.xlsx',
    '.xls',
    '.ppt',
    '.jpg',
    '.jpeg',
    '.png',
    '.gif'
]

# MIME type mapping
ALLOWED_MIME_TYPES = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.ms-powerpoint': ['.ppt'],
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
}

# Upload directory
UPLOAD_DIR = "temp_uploads"

# =============================================================================
# Database Constants
# =============================================================================

# MongoDB collection names
COLLECTION_USERS = "users"
COLLECTION_CONVERSATIONS = "conversations"
COLLECTION_MESSAGES = "messages"
COLLECTION_DOCUMENTS = "document_metadata"
COLLECTION_AUDIT_LOGS = "audit_logs"
COLLECTION_SESSIONS = "sessions"

# MongoDB connection pool
DEFAULT_MIN_POOL_SIZE = 10
DEFAULT_MAX_POOL_SIZE = 50

# Database operation timeouts (seconds)
DB_QUERY_TIMEOUT = 30
DB_WRITE_TIMEOUT = 10
DB_COUNT_TIMEOUT = 5

# =============================================================================
# Document Processing Constants
# =============================================================================

# Text chunking
DEFAULT_CHUNK_SIZE = 500  # tokens
DEFAULT_CHUNK_OVERLAP = 50  # tokens
MIN_CHUNK_TOKENS = 10

# Sentence splitting
SENTENCE_TERMINATORS = '.!?'
MIN_SENTENCE_LENGTH = 10

# Batch sizes
BATCH_SIZE_EMBEDDINGS = 100  # For OpenAI API
BATCH_SIZE_PINECONE = 100  # For Pinecone upsert

# Processing timeouts
DOCUMENT_PROCESSING_TIMEOUT_SECONDS = 3600  # 1 hour
ORPHANED_JOB_TIMEOUT_MINUTES = 30
HEARTBEAT_INTERVAL_SECONDS = 15

# Metadata limits
MAX_METADATA_TEXT_LENGTH = 1000

# PIL image processing
PIL_MAX_IMAGE_PIXELS = 200_000_000  # 200 megapixels

# Processing statuses
PROCESSING_STATUS_UPLOADING = "uploading"
PROCESSING_STATUS_PROCESSING = "processing"
PROCESSING_STATUS_COMPLETED = "completed"
PROCESSING_STATUS_FAILED = "failed"

# Processing steps
PROCESSING_STEP_EXTRACTING = "extracting_text"
PROCESSING_STEP_CHUNKING = "chunking"
PROCESSING_STEP_EMBEDDING = "generating_embeddings"
PROCESSING_STEP_STORING = "storing_vectors"

# =============================================================================
# Vector Search Constants
# =============================================================================

# Pinecone Namespaces
NAMESPACE_DOCS = "documents"  # Technical documentation, manuals, guides
NAMESPACE_MACHINERY = "machinery"  # Machine specifications, models, properties (842 machines)

# Search parameters
DEFAULT_TOP_K_RESULTS = 5
MAX_TOP_K_RESULTS = 20
MIN_RELEVANCE_SCORE = 0.7

# Embedding dimensions
OPENAI_EMBEDDING_DIMENSION = 1536  # text-embedding-3-large
OPENAI_EMBEDDING_SMALL_DIMENSION = 1536  # text-embedding-3-small

# =============================================================================
# Session and Authentication
# =============================================================================

# Session settings
SESSION_COOKIE_NAME = "session_id"
DEFAULT_SESSION_MAX_AGE = 2592000  # 30 days in seconds
REMEMBER_ME_MAX_AGE = 2592000  # 30 days

# Token expiration (seconds)
VERIFICATION_TOKEN_EXPIRY = 86400  # 24 hours
PASSWORD_RESET_TOKEN_EXPIRY = 3600  # 1 hour
ACCESS_TOKEN_EXPIRY = 3600  # 1 hour
REFRESH_TOKEN_EXPIRY = 604800  # 7 days

# Password requirements
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Username requirements
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 50

# =============================================================================
# User Authorization
# =============================================================================

# Authorization levels (in hierarchical order)
AUTH_LEVEL_REGULAR = "regular"
AUTH_LEVEL_SUPERUSER = "superuser"
AUTH_LEVEL_ADMIN = "admin"

AUTHORIZATION_HIERARCHY = {
    AUTH_LEVEL_REGULAR: 1,
    AUTH_LEVEL_SUPERUSER: 2,
    AUTH_LEVEL_ADMIN: 3,
}

# Account statuses
ACCOUNT_STATUS_ACTIVE = "active"
ACCOUNT_STATUS_SUSPENDED = "suspended"
ACCOUNT_STATUS_PENDING_VERIFICATION = "pending_verification"
ACCOUNT_STATUS_PENDING_APPROVAL = "pending_approval"
ACCOUNT_STATUS_REJECTED = "rejected"

# =============================================================================
# Chat and AI Configuration
# =============================================================================

# OpenAI models
DEFAULT_CHAT_MODEL = "gpt-4-turbo-preview"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"
FALLBACK_CHAT_MODEL = "gpt-3.5-turbo"

# Chat parameters
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7
MAX_CONVERSATION_HISTORY = 20  # messages

# Response formatting
MAX_RESPONSE_LENGTH = 8000  # characters
TRUNCATE_RESPONSE_SUFFIX = "... [Response truncated]"

# =============================================================================
# Pagination Constants
# =============================================================================

# Default pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 10

# Document listing
DEFAULT_DOCUMENT_LIMIT = 50
MAX_DOCUMENT_LIMIT = 100

# User listing
DEFAULT_USER_LIMIT = 50
MAX_USER_LIMIT = 100

# Message listing
DEFAULT_MESSAGE_LIMIT = 50
MAX_MESSAGE_LIMIT = 200

# =============================================================================
# Performance and Retry Configuration
# =============================================================================

# Retry settings
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff multiplier
RETRY_MAX_DELAY_SECONDS = 30

# Query performance monitoring
SLOW_QUERY_THRESHOLD_SECONDS = 2.0
CRITICAL_QUERY_THRESHOLD_SECONDS = 5.0

# Connection pool settings
MAX_CONCURRENT_CONNECTIONS = 100

# =============================================================================
# Logging and Monitoring
# =============================================================================

# Log levels
LOG_LEVEL_PRODUCTION = "INFO"
LOG_LEVEL_DEVELOPMENT = "DEBUG"
LOG_LEVEL_TEST = "WARNING"

# Sentry configuration
SENTRY_TRACES_SAMPLE_RATE_PRODUCTION = 0.1
SENTRY_TRACES_SAMPLE_RATE_DEVELOPMENT = 1.0

# Performance monitoring
ENABLE_PERFORMANCE_LOGGING = True
ENABLE_REQUEST_LOGGING = True

# =============================================================================
# Email Configuration
# =============================================================================

# Email templates
EMAIL_VERIFICATION_SUBJECT = "Verify Your Email - Building Machinery AI"
EMAIL_PASSWORD_RESET_SUBJECT = "Reset Your Password - Building Machinery AI"
EMAIL_WELCOME_SUBJECT = "Welcome to Building Machinery AI"
EMAIL_ACCOUNT_APPROVED_SUBJECT = "Your Account Has Been Approved"

# Email settings
EMAIL_SENDER_NAME = "Building Machinery AI Support"
DEFAULT_SMTP_PORT = 587
DEFAULT_SMTP_USE_TLS = True

# =============================================================================
# Document Categories
# =============================================================================

CATEGORY_MANUALS = "manuals"
CATEGORY_SPECIFICATIONS = "specifications"
CATEGORY_GUIDES = "guides"
CATEGORY_REPORTS = "reports"
CATEGORY_OTHER = "other"

DOCUMENT_CATEGORIES = [
    CATEGORY_MANUALS,
    CATEGORY_SPECIFICATIONS,
    CATEGORY_GUIDES,
    CATEGORY_REPORTS,
    CATEGORY_OTHER,
]

CATEGORY_LABELS = {
    CATEGORY_MANUALS: "Handbücher",
    CATEGORY_SPECIFICATIONS: "Spezifikationen",
    CATEGORY_GUIDES: "Anleitungen",
    CATEGORY_REPORTS: "Berichte",
    CATEGORY_OTHER: "Sonstiges",
}

# =============================================================================
# Audit Log Action Types
# =============================================================================

ACTION_CREATE_USER = "create_user"
ACTION_UPDATE_USER_AUTH = "update_user_authorization"
ACTION_UPDATE_USER_STATUS = "update_user_status"
ACTION_DELETE_USER = "delete_user"
ACTION_UPLOAD_DOCUMENT = "upload_document"
ACTION_DELETE_DOCUMENT = "delete_document"
ACTION_DELETE_CONVERSATION = "delete_conversation"

AUDIT_ACTIONS = [
    ACTION_CREATE_USER,
    ACTION_UPDATE_USER_AUTH,
    ACTION_UPDATE_USER_STATUS,
    ACTION_DELETE_USER,
    ACTION_UPLOAD_DOCUMENT,
    ACTION_DELETE_DOCUMENT,
    ACTION_DELETE_CONVERSATION,
]

# =============================================================================
# CORS Configuration
# =============================================================================

# Default allowed origins for development
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# =============================================================================
# Error Messages
# =============================================================================

ERROR_UNAUTHORIZED = "Unauthorized access"
ERROR_FORBIDDEN = "Insufficient permissions"
ERROR_NOT_FOUND = "Resource not found"
ERROR_BAD_REQUEST = "Invalid request"
ERROR_INTERNAL_SERVER = "Internal server error"
ERROR_SERVICE_UNAVAILABLE = "Service temporarily unavailable"

ERROR_INVALID_CREDENTIALS = "Invalid username or password"
ERROR_ACCOUNT_SUSPENDED = "Your account has been suspended"
ERROR_EMAIL_NOT_VERIFIED = "Please verify your email address"
ERROR_ACCOUNT_PENDING = "Your account is pending approval"

ERROR_FILE_TOO_LARGE = f"File size exceeds maximum of {MAX_UPLOAD_SIZE_MB}MB"
ERROR_INVALID_FILE_TYPE = "File type not allowed"
ERROR_UPLOAD_FAILED = "File upload failed"

ERROR_PROCESSING_FAILED = "Document processing failed"
ERROR_EMBEDDING_FAILED = "Failed to generate embeddings"
ERROR_VECTOR_STORAGE_FAILED = "Failed to store vectors"

# =============================================================================
# Success Messages
# =============================================================================

SUCCESS_LOGIN = "Login successful"
SUCCESS_LOGOUT = "Logout successful"
SUCCESS_REGISTER = "Registration successful"
SUCCESS_EMAIL_VERIFIED = "Email verified successfully"
SUCCESS_PASSWORD_RESET = "Password reset successful"

SUCCESS_DOCUMENT_UPLOADED = "Document uploaded successfully"
SUCCESS_DOCUMENT_DELETED = "Document deleted successfully"
SUCCESS_DOCUMENT_PROCESSED = "Document processed successfully"

SUCCESS_USER_UPDATED = "User updated successfully"
SUCCESS_USER_DELETED = "User deleted successfully"

# =============================================================================
# HTTP Status Codes
# =============================================================================

HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_429_TOO_MANY_REQUESTS = 429
HTTP_500_INTERNAL_SERVER_ERROR = 500
HTTP_503_SERVICE_UNAVAILABLE = 503
HTTP_504_GATEWAY_TIMEOUT = 504

# =============================================================================
# Validation Patterns
# =============================================================================

# Regex patterns
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
USERNAME_PATTERN = r'^[a-zA-Z0-9_-]{3,50}$'

# =============================================================================
# Feature Flags
# =============================================================================

ENABLE_EMAIL_VERIFICATION = True
ENABLE_ADMIN_APPROVAL = False
ENABLE_RATE_LIMITING = True
ENABLE_AUDIT_LOGGING = True
ENABLE_DOCUMENT_PROCESSING = True
ENABLE_SSE_UPDATES = True

# =============================================================================
# Environment-specific Settings
# =============================================================================

ENVIRONMENTS = {
    'development': {
        'log_level': LOG_LEVEL_DEVELOPMENT,
        'enable_docs': True,
        'enable_debug': True,
    },
    'staging': {
        'log_level': LOG_LEVEL_PRODUCTION,
        'enable_docs': True,
        'enable_debug': False,
    },
    'production': {
        'log_level': LOG_LEVEL_PRODUCTION,
        'enable_docs': False,
        'enable_debug': False,
    },
    'test': {
        'log_level': LOG_LEVEL_TEST,
        'enable_docs': False,
        'enable_debug': False,
    },
}

# =============================================================================
# E-Code Property Constants (406 Total Properties)
# =============================================================================

# All 406 E-code Properties
# Format: "E-code - Description [unit]" or "E-code - Description"
ALL_ECODE_PROPERTIES = [
    "Serial Number",
    "Inventory Number",
    "E1010 - 1-Achser",
    "E1020 - 2-Achser",
    "E1030 - 3-Achser",
    "E1040 - 4-Achser",
    "E1050 - ABB - Arbeitsbereichsbegrenzung",
    "E1070 - Abgasstufe EU",
    "E1080 - Abgasstufe USA",
    "E1090 - Absauganlage",
    "E1110 - Allradantrieb",
    "E1120 - Allradlenkung",
    "E1130 - Anzahl Zähne",
    "E1150 - Arbeitsbreite [mm]",
    "E1160 - Arbeitsdruck [bar]",
    "E1170 - Arbeitshöhe [m]",
    "E1180 - Asphaltmanager",
    "E1200 - Aufgabe [mm]",
    "E1210 - Ausladung [m]",
    "E1220 - Ausleger [m]",
    "E1230 - Backenbrecher",
    "E1240 - Ballast [t]",
    "E1250 - Bandbreite [mm]",
    "E1270 - Bio-Hydrauliköl",
    "E1280 - Bodenplatten [mm]",
    "E1320 - Brechkraft [t]",
    "E1330 - Breite [mm]",
    "E1340 - Dachprofilverstellung",
    "E1370 - Dieselmotor",
    "E1380 - Dieselpartikelfilter",
    "E1390 - Distanzkontrolle automatisch",
    "E1400 - drehbar",
    "E1430 - Druck [bar]",
    "E1450 - Durchsatzmenge [t/h]",
    "E1460 - E-Heizung",
    "E1470 - Einbaubreite Grundbohle [m]",
    "E1480 - Einbaubreite max. [m]",
    "E1490 - Einbaubreite mit Verbreiterungen [m]",
    "E1510 - Elektrostarter",
    "E1530 - Fahrgeschwindigkeit [km/h]",
    "E1570 - Förderhöhe [m]",
    "E1580 - Förderkapazität [t/h]",
    "E1590 - Förderlänge [m]",
    "E1610 - Fräsbreite [mm]",
    "E1620 - Fräsmeissel Anzahl",
    "E1630 - Frästiefe [mm]",
    "E1670 - Funkfernsteuerung",
    "E1680 - Gabelaufnahme Beschickerkübel",
    "E1690 - Gas-Heizung",
    "E1720 - geteilte Bandage",
    "E1730 - Gewicht [kg]",
    "E1740 - Grabtiefe [mm]",
    "E1750 - Greiferdreheinrichtung",
    "E1760 - Greiferhydraulik",
    "E1770 - Hakenhöhe [m]",
    "E1780 - Hammerhydraulik",
    "E1840 - hochfahrbare Kabine",
    "E1860 - Höhe [mm]",
    "E1870 - Hubhöhe [mm]",
    "E1880 - Inhalt [m³]",
    "E1890 - Kabine",
    "E1900 - Kantenschneidgerät [Stück]",
    "E1920 - Klappschild",
    "E1930 - Klimaanlage",
    "E1940 - Knicklenkung",
    "E1960 - Körnung [mm]",
    "E1970 - Kreiselbrecher",
    "E1990 - Länge [mm]",
    "E2020 - Leistungsaufnahme [kW]",
    "E2040 - Löffelstiel [mm]",
    "E2100 - mobil - Kette",
    "E2110 - mobil - Rad",
    "E2120 - mobil - semi",
    "E2130 - Monoausleger",
    "E2140 - Motor - Benzin",
    "E2150 - Motor - Diesel",
    "E2170 - Motor - Hersteller",
    "E2180 - Motor - Leistung [kW]",
    "E2190 - Motor [Typ]",
    "E2200 - Muldenerhöhung",
    "E2210 - Muldenheizung",
    "E2220 - Muldenvolumen [m³]",
    "E2230 - Nennspannung [V]",
    "E2250 - Nutzlast [kg]",
    "E2260 - Oszillation",
    "E2280 - Plattformhöhe [mm]",
    "E2300 - Powertilt",
    "E2310 - Prallmühle",
    "E2320 - Pratzenabstützung",
    "E2340 - Rampen - hydraulisch",
    "E2350 - Rampen - mechanisch",
    "E2370 - reversierbar",
    "E2390 - Schaufelvolumen [m³]",
    "E2400 - Scherenhydraulik",
    "E2420 - Schildabstützung",
    "E2430 - Schnellgang",
    "E2440 - Schnellwechsler [Typ]",
    "E2450 - Schnellwechsler Henle",
    "E2460 - Schnellwechsler hydr.",
    "E2470 - Schnellwechsler mech.",
    "E2480 - Schnellwechsler OilQuick",
    "E2490 - Schnittbreite [mm]",
    "E2510 - Schnittlänge [mm]",
    "E2520 - Schnitttiefe [mm]",
    "E2540 - Schutzklasse [IP]",
    "E2550 - Schwenkband",
    "E2560 - Seitenknickausleger",
    "E2610 - Steigfähigkeit ohne Vibration [%]",
    "E2615 - Steigfähigkeit mit Vibration [%]",
    "E2640 - Teleskopausleger",
    "E2650 - Temperaturmessung Asphalt",
    "E2670 - Tiltrotator",
    "E2710 - Tragkraft max. [kg]",
    "E2760 - Truck - Assist",
    "E2770 - Turmsystem [Typ]",
    "E2800 - Verdichtungsmesser",
    "E2810 - Verstellausleger",
    "E2820 - Vor- und Rücklauf",
    "E2830 - Vorlauf",
    "E2840 - Vorrüstung 2D-Steuerung",
    "E2850 - Vorrüstung 3D-Steuerung",
    "E2920 - Wetterschutzdach",
    "E2940 - Zahntyp",
    "E2950 - Zentralschmierung",
    "E2970 - Bohle [Typ]",
    "E2980 - Rotationsgeschwindigkeit [U/min]",
    "E2990 - Durchflussmenge [l/min]",
    "E3000 - Einbaustärke [mm]",
    "E3010 - Zul. Reisskraft [kNm]",
    "E3020 - empf. Baggerklasse [t]",
    "E3030 - VM-38 Schnittstelle",
    "E3040 - Vorrüstung Navitronic",
    "E3050 - Drehmulde",
    "E3060 - Vorrüstung Völkel",
    "E3070 - Einbau von HGT/Schotter?",
    "E3080 - Führerscheinklasse",
    "E3090 - Stützlast [kg]",
    "E3100 - Streben/Stege",
    "E3150 - Reifengröße",
    "E3180 - Splittstreuer",
    "E3190 - Anbauplattenverdichter",
    "E3200 - Batterie [Typ]",
]
