<div align="center">

# Building Machinery AI Chatbot

### Enterprise-Grade AI Support System for Building Machinery

[![FastAPI](https://img.shields.io/badge/FastAPI-0.121.1-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.1.1-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9.3-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Weaviate](https://img.shields.io/badge/Weaviate-1.27.5-00C853?style=for-the-badge&logo=weaviate&logoColor=white)](https://weaviate.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**An intelligent, RAG-powered chatbot system designed specifically for building machinery support and technical documentation.**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Documentation](#-documentation) • [Contributing](#-contributing)

---

</div>

## Overview

The **Building Machinery AI Chatbot** (Baumaschinen-KI) is a production-ready, enterprise-grade conversational AI system that revolutionizes technical support for building machinery. It combines advanced Retrieval-Augmented Generation (RAG) with sophisticated document processing, multi-tenancy, and comprehensive analytics to deliver accurate, context-aware responses to technical queries.

### Why This Project Stands Out

- **Advanced RAG Pipeline**: Hybrid search (vector + BM25), Cohere reranking, context compression, and quality validation
- **Intelligent Document Processing**: Automated OCR and table extraction powered by Aryn/Sycamore and Docling
- **Enterprise Security**: Role-based access control, JWT authentication, email verification, and admin approval workflows
- **Production Excellence**: Rate limiting, caching (70-80% cost reduction), circuit breakers, and comprehensive monitoring
- **Multi-Tenancy**: Isolated data per user using Weaviate's native multi-tenancy features
- **Real-Time Streaming**: Server-Sent Events (SSE) for responsive chat experiences
- **Analytics & Observability**: Prometheus metrics, Grafana dashboards, Sentry error tracking, and usage analytics

---

## Table of Contents

- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Development](#-development)
  - [Backend Development](#backend-development)
  - [Frontend Development](#frontend-development)
  - [Testing](#testing)
- [Deployment](#-deployment)
- [Monitoring & Observability](#-monitoring--observability)
- [Advanced Features](#-advanced-features)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

---

## Features

### Core Capabilities

#### Conversational AI
- **Intelligent Chat Interface**: Real-time streaming responses with markdown rendering and syntax highlighting
- **Conversation Management**: Create, update, delete, and export conversations
- **Context-Aware Responses**: Maintains conversation history with automatic summarization
- **Multi-Turn Dialogue**: Remembers context across conversation turns
- **User Feedback**: Thumbs up/down with optional comments for continuous improvement

#### Document Intelligence
- **Multi-Format Support**: PDF, DOCX, PPTX, XLSX, and image files (JPG, PNG)
- **Automated Processing**:
  - **Aryn/Sycamore**: Cloud-based OCR, table extraction, and image processing
  - **Docling**: Local fallback with EasyOCR and PyTorch-based models
- **Semantic Chunking**: Intelligent text splitting that preserves document structure
- **Vision Extraction**: Automatic image analysis and description using GPT-4 Vision
- **Metadata Enrichment**: Extracts properties, relationships, and structured data

#### Advanced RAG Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 3: Advanced RAG                    │
├─────────────────────────────────────────────────────────────┤
│  Query → Hybrid Search → Reranking → Compression → LLM     │
│         (Vector + BM25)   (Cohere)   (Context)   (GPT-4)   │
└─────────────────────────────────────────────────────────────┘
```

- **Hybrid Retrieval**: Combines vector similarity (OpenAI embeddings) with BM25 keyword search
  - Adjustable alpha parameter: 0.0 (pure keyword) to 1.0 (pure vector)
  - Default: 0.75 for optimal balance
- **Cohere Reranking**: Semantic reranking of top-k results for improved relevance
- **Context Compression**: Reduces token usage while preserving key information
- **Quality Validation**: Validates answer quality and flags low-confidence responses
- **Source Attribution**: Every response includes document sources with page numbers

### User Management

#### Authentication & Authorization
- **Secure Authentication**: Argon2 password hashing, JWT-based sessions
- **Email Verification**: Double opt-in registration flow with verification tokens
- **Password Recovery**: Secure reset flow with time-limited tokens and rate limiting
- **Role-Based Access Control (RBAC)**:
  - **Regular**: Chat access, view own conversations
  - **Superuser**: Document upload and management
  - **Admin**: User approval, system configuration, analytics dashboard

#### Admin Capabilities
- **User Approval Workflow**: Review and approve/reject new user registrations
- **Document Management**: Upload, process, and monitor document ingestion status
- **System Analytics**: Track usage patterns, popular queries, and user engagement
- **Audit Logging**: Comprehensive logs of all administrative actions

### Production Features

#### Performance & Reliability
- **Intelligent Caching**:
  - Embedding cache (24h TTL): Reduces OpenAI costs by 70-80%
  - Retrieval cache (1h TTL): Speeds up repeated queries
  - Response cache (30min TTL): Instant responses for common questions
- **Resilience Patterns**:
  - Exponential backoff with jitter for API retries
  - Circuit breakers to prevent cascade failures
  - Graceful degradation when external services are down
- **Rate Limiting**:
  - Anonymous users: 10/hour, 100/day
  - Regular users: 100/hour, 1000/day
  - Per-user tracking with Redis-like in-memory store

#### Monitoring & Observability
- **Prometheus Metrics**:
  - Request rates, latencies, and error rates
  - Weaviate query performance
  - Cache hit/miss ratios
  - Token usage and API costs
- **Grafana Dashboards**:
  - Weaviate vector database overview
  - System health and resource utilization
  - User activity and engagement metrics
- **Sentry Integration**: Real-time error tracking and alerting
- **Structured Logging**: JSON-formatted logs with trace IDs for debugging

#### Data Isolation & Security
- **Multi-Tenancy**: Weaviate's native multi-tenancy ensures complete data isolation per user
- **Encryption**: TLS/HTTPS for all communications
- **Secret Management**: Environment-based configuration with `.env` files
- **CORS Protection**: Configurable allowed origins
- **Input Validation**: Pydantic models for all API inputs

---

## Technology Stack

### Backend (FastAPI + Python)

<div align="center">

| Category | Technologies |
|----------|-------------|
| **Framework** | ![FastAPI](https://img.shields.io/badge/FastAPI-0.121.1-009688?logo=fastapi&logoColor=white) ![Uvicorn](https://img.shields.io/badge/Uvicorn-0.38.0-499848?logo=uvicorn&logoColor=white) |
| **Language** | ![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white) |
| **Database** | ![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white) ![Motor](https://img.shields.io/badge/Motor-3.7.1-47A248) |
| **Vector DB** | ![Weaviate](https://img.shields.io/badge/Weaviate-1.27.5-00C853?logo=weaviate&logoColor=white) |
| **AI/ML** | ![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white) ![Cohere](https://img.shields.io/badge/Cohere-5.20.0-00B4D8) ![Pydantic AI](https://img.shields.io/badge/Pydantic_AI-1.14.1-E92063) |
| **Document Processing** | ![Docling](https://img.shields.io/badge/Docling-2.61.2-FF6B6B) ![Sycamore](https://img.shields.io/badge/Sycamore-0.1.33-4ECDC4) ![EasyOCR](https://img.shields.io/badge/EasyOCR-1.7.2-FFD93D) ![PyTorch](https://img.shields.io/badge/PyTorch-2.9.0-EE4C2C?logo=pytorch&logoColor=white) |
| **Security** | ![Argon2](https://img.shields.io/badge/Argon2-25.1.0-00897B) ![Python Jose](https://img.shields.io/badge/Python_Jose-3.5.0-00897B) |
| **Monitoring** | ![Prometheus](https://img.shields.io/badge/Prometheus-Client-E6522C?logo=prometheus&logoColor=white) ![Sentry](https://img.shields.io/badge/Sentry-2.44.0-362D59?logo=sentry&logoColor=white) |

</div>

### Frontend (React + TypeScript)

<div align="center">

| Category | Technologies |
|----------|-------------|
| **Framework** | ![React](https://img.shields.io/badge/React-19.1.1-61DAFB?logo=react&logoColor=black) ![Vite](https://img.shields.io/badge/Vite-7.1.7-646CFF?logo=vite&logoColor=white) |
| **Language** | ![TypeScript](https://img.shields.io/badge/TypeScript-5.9.3-3178C6?logo=typescript&logoColor=white) |
| **Routing** | ![React Router](https://img.shields.io/badge/React_Router-6.30.1-CA4245?logo=react-router&logoColor=white) |
| **State Management** | ![Zustand](https://img.shields.io/badge/Zustand-4.5.7-543E56) ![React Query](https://img.shields.io/badge/React_Query-5.90.6-FF4154?logo=react-query&logoColor=white) |
| **UI Components** | ![Radix UI](https://img.shields.io/badge/Radix_UI-Latest-161618?logo=radix-ui&logoColor=white) ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4.18-06B6D4?logo=tailwind-css&logoColor=white) |
| **Markdown** | ![React Markdown](https://img.shields.io/badge/React_Markdown-9.1.0-000000?logo=markdown&logoColor=white) ![Remark GFM](https://img.shields.io/badge/Remark_GFM-4.0.1-000000) |
| **Testing** | ![Jest](https://img.shields.io/badge/Jest-30.2.0-C21325?logo=jest&logoColor=white) ![Playwright](https://img.shields.io/badge/Playwright-1.56.1-2EAD33?logo=playwright&logoColor=white) |
| **Build Tools** | ![ESLint](https://img.shields.io/badge/ESLint-8.57.1-4B32C3?logo=eslint&logoColor=white) ![Prettier](https://img.shields.io/badge/Prettier-3.6.2-F7B93E?logo=prettier&logoColor=black) |

</div>

### Infrastructure & DevOps

<div align="center">

| Category | Technologies |
|----------|-------------|
| **Containerization** | ![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white) |
| **Web Server** | ![Nginx](https://img.shields.io/badge/Nginx-1.27-009639?logo=nginx&logoColor=white) |
| **Monitoring** | ![Grafana](https://img.shields.io/badge/Grafana-Latest-F46800?logo=grafana&logoColor=white) ![Prometheus](https://img.shields.io/badge/Prometheus-Latest-E6522C?logo=prometheus&logoColor=white) |
| **Email** | ![SMTP](https://img.shields.io/badge/SMTP-Office365-0078D4?logo=microsoft-outlook&logoColor=white) |
| **CI/CD** | ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Ready-2088FF?logo=github-actions&logoColor=white) |

</div>

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Client (Browser)                               │
│                     React + TypeScript + Vite                           │
└────────────────────────────┬────────────────────────────────────────────┘
                             │ HTTPS/WSS
                             ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       Nginx (Reverse Proxy)                             │
│                   Static Files + API Proxy                              │
└────────────┬────────────────────────────────────────────┬───────────────┘
             │                                            │
             ↓ /api/*                                     ↓ /metrics
┌────────────────────────────────────┐      ┌────────────────────────────┐
│     FastAPI Backend (Python)       │      │  Prometheus + Grafana      │
│  ┌──────────────────────────────┐  │      │    Monitoring Stack        │
│  │   API Endpoints              │  │      └────────────────────────────┘
│  │  • /auth (JWT + Sessions)    │  │
│  │  • /chat (SSE Streaming)     │  │
│  │  • /documents (Upload/Mgmt)  │  │
│  │  • /admin (User Approval)    │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │   Services Layer             │  │
│  │  • AI Agent (Pydantic AI)    │  │
│  │  • Hybrid Retrieval          │  │
│  │  • Document Processor        │  │
│  │  • Email Service             │  │
│  └──────────────────────────────┘  │
└────────┬────────────┬───────────┬──┘
         │            │           │
         ↓            ↓           ↓
┌─────────────┐  ┌────────────┐  ┌──────────────────┐
│  MongoDB    │  │  Weaviate  │  │  External APIs   │
│   Atlas     │  │  Vector DB │  │  • OpenAI        │
│             │  │            │  │  • Cohere        │
│ • Users     │  │ • Vectors  │  │  • Aryn          │
│ • Sessions  │  │ • Chunks   │  │  • Sentry        │
│ • Convos    │  │ • Multi-   │  └──────────────────┘
│ • Docs      │  │   Tenancy  │
│ • Analytics │  │ • Hybrid   │
└─────────────┘  │   Search   │
                 └────────────┘
```

### RAG Pipeline Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         User Query: "How do I..."                        │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │  Query Preprocessing   │
                    │  • Normalize umlauts   │
                    │  • Extract entities    │
                    └────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │   Generate Embedding   │
                    │  text-embedding-3-     │
                    │      large (3072d)     │
                    └────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │   Hybrid Retrieval     │
                    │ ┌────────────────────┐ │
                    │ │ Vector Search      │ │
                    │ │ (Cosine Similarity)│ │
                    │ └────────────────────┘ │
                    │          ∪             │
                    │ ┌────────────────────┐ │
                    │ │ BM25 Keyword       │ │
                    │ │ Search (Sparse)    │ │
                    │ └────────────────────┘ │
                    │  α=0.75 (configurable) │
                    └────────────┬───────────┘
                                 │
                                 ↓ Top 20 chunks
                    ┌────────────────────────┐
                    │  Cohere Reranking      │
                    │  • Semantic relevance  │
                    │  • Cross-encoder model │
                    └────────────┬───────────┘
                                 │
                                 ↓ Top 10 chunks
                    ┌────────────────────────┐
                    │  Context Compression   │
                    │  • Remove redundancy   │
                    │  • Target: 3500 tokens │
                    └────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │   Prompt Construction  │
                    │  • System instructions │
                    │  • Compressed context  │
                    │  • Conversation history│
                    │  • User query          │
                    └────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │   LLM Generation       │
                    │   (GPT-4o-mini)        │
                    │   Streaming Response   │
                    └────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │  Quality Validation    │
                    │  • Confidence check    │
                    │  • Source verification │
                    └────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │   Response to User     │
                    │  + Source citations    │
                    └────────────────────────┘
```

### Document Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      User Uploads Document                              │
│                  (PDF, DOCX, PPTX, XLSX, Images)                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │   File Validation      │
                    │  • Size check          │
                    │  • Extension check     │
                    │  • Virus scan (TODO)   │
                    └────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │  Upload to MongoDB     │
                    │  (GridFS for >16MB)    │
                    └────────────┬───────────┘
                                 │
                                 ↓
                ┌────────────────┴────────────────┐
                │                                 │
                ↓ Aryn API Key?                  ↓ No Aryn Key
    ┌───────────────────────┐       ┌───────────────────────┐
    │  Aryn/Sycamore        │       │  Docling (Local)      │
    │  Cloud Processing     │       │  Processing           │
    │  • OCR (automatic)    │       │  • EasyOCR            │
    │  • Tables (automatic) │       │  • Layout detection   │
    │  • Images (automatic) │       │  • Table extraction   │
    │  • Fast & accurate    │       │  • Image analysis     │
    └───────────┬───────────┘       └───────────┬───────────┘
                │                               │
                └───────────────┬───────────────┘
                                │
                                ↓
                    ┌────────────────────────┐
                    │   Text Extraction      │
                    │  • Markdown format     │
                    │  • Structure preserved │
                    │  • Metadata enriched   │
                    └────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │   Semantic Chunking    │
                    │  • ~500-1000 tokens    │
                    │  • Overlap: 100 tokens │
                    │  • Context preserved   │
                    └────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │  Generate Embeddings   │
                    │  (OpenAI text-embed-3) │
                    │  3072 dimensions       │
                    └────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │  Store in Weaviate     │
                    │  • User tenant         │
                    │  • Vector + BM25 index │
                    │  • Metadata attached   │
                    └────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │  Update Document       │
                    │  Metadata in MongoDB   │
                    │  Status: "completed"   │
                    └────────────────────────┘
```

### Data Models

<details>
<summary><b>Click to expand data models</b></summary>

#### User Model (MongoDB)
```python
{
  "user_id": "uuid",
  "username": "string (unique, lowercase)",
  "email": "email (unique)",
  "password_hash": "argon2 hash",
  "authorization_level": "regular | superuser | admin",
  "account_status": "pending_verification | active | suspended",
  "email_verified": boolean,
  "email_verification_token": "string?",
  "created_at": "datetime",
  "last_login": "datetime?",
  "approved_by": "user_id?",
  "approved_at": "datetime?",
  "settings": {}
}
```

#### Conversation Model (MongoDB)
```python
{
  "conversation_id": "uuid",
  "user_id": "uuid",
  "title": "string",
  "messages": [
    {
      "message_id": "uuid",
      "role": "user | assistant | system",
      "content": "string",
      "timestamp": "datetime",
      "metadata": {
        "sources": [...],
        "tokens": int,
        "latency_ms": int,
        "model": "string"
      }
    }
  ],
  "message_count": int,
  "created_at": "datetime",
  "updated_at": "datetime",
  "last_message_at": "datetime"
}
```

#### Document Chunk (Weaviate)
```json
{
  "class": "DocumentChunk",
  "properties": {
    "document_id": "uuid",
    "chunk_id": "uuid",
    "content": "text",
    "chunk_index": int,
    "page_number": int,
    "document_title": "string",
    "document_type": "string",
    "metadata": {},
    "embedding": [3072 floats]
  },
  "tenant": "user_id"
}
```

</details>

---

## Quick Start

### Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Python** 3.11+ (for local backend development)
- **Node.js** 18+ and **npm** (for local frontend development)
- **Git** for version control

<details>
<summary><b>Optional: For local development without Docker</b></summary>

- **MongoDB** 6.0+ (or MongoDB Atlas account)
- **Weaviate** 1.27+ (or use Docker)
- **OpenAI API Key** (required)
- **Cohere API Key** (optional, for reranking)
- **Aryn API Key** (optional, for advanced document processing)

</details>

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/building-machinery-chatbot.git
cd building-machinery-chatbot
```

2. **Set up environment variables**

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Application
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-min-32-chars-long-change-this
API_INTERNAL_KEY=your-internal-api-key-change-this

# Server
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=https://yourdomain.com,http://localhost:3000

# MongoDB Atlas (or local)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=building_machinery_chatbot

# OpenAI (Required)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Cohere (Optional, for reranking)
COHERE_API_KEY=your-cohere-api-key

# Aryn/Sycamore (Optional, for advanced document processing)
ARYN_API_KEY=your-aryn-api-key
USE_SYCAMORE_PROCESSOR=true
SYCAMORE_EXTRACT_TABLES=true
SYCAMORE_USE_OCR=true
SYCAMORE_EXTRACT_IMAGES=true

# Weaviate (configured via docker-compose.yml)
WEAVIATE_HOST=weaviate
WEAVIATE_PORT=8080
ENABLE_WEAVIATE_MULTITENANCY=true
ENABLE_WEAVIATE_COMPRESSION=true

# Email (SMTP)
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@domain.com
SMTP_PASSWORD=your-email-password
SMTP_FROM_EMAIL=noreply@yourdomain.com

# Frontend
FRONTEND_URL=https://yourdomain.com
VITE_API_URL=https://yourdomain.com/api

# Optional: Sentry (Error Tracking)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Optional: Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=change-this-password
```

> **Security Warning**: Never commit your `.env` file to version control. Keep all API keys and secrets secure.

### Configuration

<details>
<summary><b>Detailed Configuration Options</b></summary>

#### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Environment mode | `development` | Yes |
| `SECRET_KEY` | Session signing key (32+ chars) | - | Yes |
| `API_INTERNAL_KEY` | Internal API key | - | Yes |
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` | Yes |
| `OPENAI_API_KEY` | OpenAI API key | - | Yes |
| `COHERE_API_KEY` | Cohere API key | - | No |
| `ARYN_API_KEY` | Aryn API key | - | No |
| `SMTP_HOST` | SMTP server host | - | Yes |
| `SMTP_USERNAME` | SMTP username | - | Yes |
| `SMTP_PASSWORD` | SMTP password | - | Yes |

#### Feature Flags

```bash
# Advanced RAG
ENABLE_ADVANCED_RAG=true
ENABLE_RERANKING=true
ENABLE_CONTEXT_COMPRESSION=true
ENABLE_QUALITY_VALIDATION=true

# Conversational Intelligence
ENABLE_CONVERSATION_MEMORY=true
ENABLE_ANALYTICS_TRACKING=true
ENABLE_FEEDBACK_COLLECTION=true

# Production Excellence
ENABLE_CACHING=true
ENABLE_RESILIENCE=true
ENABLE_RATE_LIMITING=true
```

</details>

### Running the Application

#### Option 1: Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Weaviate**: http://localhost:8080
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

#### Option 2: Local Development

<details>
<summary><b>Backend Setup</b></summary>

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

</details>

<details>
<summary><b>Frontend Setup</b></summary>

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at http://localhost:5173

</details>

#### First-Time Setup

1. **Access the application** at http://localhost or http://localhost:5173
2. **Register a new account** (will require email verification)
3. **Check your email** for the verification link
4. **Wait for admin approval** (or directly update MongoDB for testing)
5. **Log in and start chatting!**

For development, you can manually approve users in MongoDB:

```javascript
db.users.updateOne(
  { email: "your-email@example.com" },
  {
    $set: {
      email_verified: true,
      account_status: "active",
      authorization_level: "admin"
    }
  }
)
```

---

## Project Structure

```
building-machinery-chatbot/
├── backend/                      # FastAPI Python backend
│   ├── app/
│   │   ├── api/                  # API endpoints
│   │   │   └── v1/
│   │   │       ├── endpoints/    # Route handlers
│   │   │       │   ├── auth.py   # Authentication endpoints
│   │   │       │   ├── chat.py   # Chat endpoints (SSE)
│   │   │       │   ├── documents.py  # Document management
│   │   │       │   ├── admin.py  # Admin dashboard
│   │   │       │   ├── health.py # Health checks
│   │   │       │   └── weaviate_admin.py  # Weaviate ops
│   │   │       └── dependencies.py  # Dependency injection
│   │   ├── core/                 # Core functionality
│   │   │   ├── database.py       # MongoDB connection
│   │   │   ├── logging_config.py # Logging setup
│   │   │   └── session.py        # Session management
│   │   ├── models/               # Pydantic models
│   │   │   ├── user.py           # User & session models
│   │   │   ├── conversation.py   # Conversation models
│   │   │   ├── document.py       # Document models
│   │   │   └── audit_log.py      # Audit log models
│   │   ├── schemas/              # API schemas
│   │   │   ├── auth.py           # Auth request/response
│   │   │   ├── chat.py           # Chat request/response
│   │   │   ├── document.py       # Document schemas
│   │   │   └── admin.py          # Admin schemas
│   │   ├── services/             # Business logic
│   │   │   ├── ai_agent.py       # Pydantic AI agent
│   │   │   ├── hybrid_retrieval_orchestrator.py  # RAG pipeline
│   │   │   ├── weaviate_service.py  # Vector DB operations
│   │   │   ├── document_processor.py  # Document ingestion
│   │   │   ├── aryn_processor.py # Aryn/Sycamore integration
│   │   │   ├── openai_service.py # OpenAI API client
│   │   │   ├── email_service.py  # Email sending
│   │   │   └── ...
│   │   ├── utils/                # Utilities
│   │   │   ├── security.py       # Token generation
│   │   │   ├── password.py       # Password hashing
│   │   │   ├── monitoring.py     # Metrics
│   │   │   └── logging.py        # Logging helpers
│   │   ├── middleware/           # Middleware
│   │   │   └── rate_limiter.py   # Rate limiting
│   │   ├── config.py             # Configuration
│   │   ├── constants.py          # Constants
│   │   └── main.py               # Application entry point
│   ├── tests/                    # Backend tests
│   ├── Dockerfile                # Backend Docker image
│   ├── pyproject.toml            # Python dependencies
│   └── requirements.txt          # Frozen dependencies
│
├── frontend/                     # React TypeScript frontend
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── chat/             # Chat-specific components
│   │   │   │   ├── ConversationSidebar.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── MessageInput.tsx
│   │   │   │   ├── MessageFeedback.tsx
│   │   │   │   └── MarkdownRenderer.tsx
│   │   │   ├── layout/           # Layout components
│   │   │   │   └── Header.tsx
│   │   │   ├── shared/           # Shared components
│   │   │   │   ├── LoadingSpinner.tsx
│   │   │   │   ├── EmptyState.tsx
│   │   │   │   └── DataTable.tsx
│   │   │   ├── ui/               # shadcn/ui components
│   │   │   └── admin/            # Admin components
│   │   ├── pages/                # Page components
│   │   │   ├── ChatPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── AdminPage.tsx
│   │   │   ├── DocumentsPage.tsx
│   │   │   └── ProfilePage.tsx
│   │   ├── services/             # API services
│   │   │   ├── api.ts            # Axios client
│   │   │   ├── authService.ts    # Auth API calls
│   │   │   ├── chatService.ts    # Chat API calls
│   │   │   └── adminService.ts   # Admin API calls
│   │   ├── store/                # Zustand stores
│   │   │   ├── authStore.ts      # Auth state
│   │   │   ├── chatStore.ts      # Chat state
│   │   │   └── uiStore.ts        # UI state
│   │   ├── hooks/                # Custom hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useChat.ts
│   │   │   └── useToast.ts
│   │   ├── types/                # TypeScript types
│   │   │   └── index.ts
│   │   ├── utils/                # Utilities
│   │   │   └── translations.ts
│   │   ├── App.tsx               # Main app component
│   │   ├── main.tsx              # Entry point
│   │   └── index.css             # Global styles
│   ├── public/                   # Static assets
│   ├── tests/                    # Frontend tests
│   ├── Dockerfile                # Frontend Docker image
│   ├── nginx.conf                # Nginx configuration
│   ├── vite.config.ts            # Vite configuration
│   ├── tailwind.config.js        # Tailwind configuration
│   ├── tsconfig.json             # TypeScript configuration
│   └── package.json              # Node dependencies
│
├── monitoring/                   # Monitoring configuration
│   ├── prometheus.yml            # Prometheus config
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/      # Prometheus datasource
│       │   └── dashboards/       # Dashboard provisioning
│       └── dashboards/           # Grafana dashboards
│           └── weaviate-overview.json
│
├── docker-compose.yml            # Docker Compose orchestration
├── .env.example                  # Example environment variables
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
└── LICENSE                       # MIT License
```

---

## API Documentation

### Interactive API Documentation

Once the backend is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Key Endpoints

#### Authentication (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/register` | Register new user | No |
| `POST` | `/login` | Login user | No |
| `POST` | `/logout` | Logout user | Yes |
| `GET` | `/me` | Get current user | Yes |
| `GET` | `/verify-email` | Verify email token | No |
| `POST` | `/forgot-password` | Request password reset | No |
| `POST` | `/reset-password/:token` | Reset password | No |

#### Chat (`/api/chat`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/conversations` | Create conversation | Yes |
| `GET` | `/conversations` | List conversations | Yes |
| `GET` | `/conversations/:id` | Get conversation | Yes |
| `PUT` | `/conversations/:id` | Update conversation | Yes |
| `DELETE` | `/conversations/:id` | Delete conversation | Yes |
| `POST` | `/conversations/:id/messages` | Send message (SSE) | Yes |
| `GET` | `/conversations/:id/export` | Export conversation | Yes |

#### Documents (`/api/documents`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/upload` | Upload document | Superuser/Admin |
| `GET` | `/` | List documents | Superuser/Admin |
| `GET` | `/:id` | Get document metadata | Superuser/Admin |
| `DELETE` | `/:id` | Delete document | Admin |
| `GET` | `/:id/status` | Get processing status | Superuser/Admin |

#### Admin (`/api/admin`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/pending-users` | List pending approvals | Admin |
| `POST` | `/approve-user` | Approve user | Admin |
| `POST` | `/reject-user` | Reject user | Admin |
| `GET` | `/users` | List all users | Admin |
| `GET` | `/analytics` | Get system analytics | Admin |

### WebSocket/SSE Streaming

Chat messages are streamed using Server-Sent Events (SSE) for real-time responses:

```typescript
// Frontend example
const eventSource = chatService.sendMessage(conversationId, message);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'content') {
    // Append streaming content
    appendToMessage(data.content);
  } else if (data.type === 'sources') {
    // Display sources
    setSources(data.sources);
  } else if (data.type === 'done') {
    // Stream complete
    eventSource.close();
  }
};
```

---

## Development

### Backend Development

#### Setup Development Environment

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies including dev tools
pip install -r requirements.txt
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

#### Code Quality Tools

```bash
# Format code with Black
black app/

# Lint with Ruff
ruff check app/

# Type checking with MyPy
mypy app/

# Run all checks
black app/ && ruff check app/ && mypy app/
```

#### Project Configuration

- **Black**: 88 character line length, Python 3.11 target
- **Ruff**: Fast Python linter (replaces Flake8, isort, etc.)
- **MyPy**: Static type checking with strict settings

### Frontend Development

#### Setup Development Environment

```bash
cd frontend

# Install dependencies
npm install

# Start development server with hot reload
npm run dev
```

#### Available Scripts

```bash
# Development
npm run dev              # Start dev server (port 5173)
npm run build            # Build for production
npm run preview          # Preview production build

# Code Quality
npm run lint             # ESLint linting
npm run lint:fix         # Auto-fix linting issues

# Testing
npm run test             # Run Jest unit tests
npm run test:watch       # Watch mode
npm run test:coverage    # Generate coverage report
npm run test:e2e         # Run Playwright E2E tests
npm run test:e2e:ui      # E2E tests with UI
npm run test:e2e:debug   # Debug E2E tests
```

#### Project Configuration

- **Vite**: Fast build tool with HMR
- **TypeScript**: Strict mode enabled
- **ESLint**: React and TypeScript plugins
- **Prettier**: Code formatting (integrated with ESLint)
- **Tailwind CSS**: Utility-first CSS framework

### Testing

#### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v

# Run parallel tests
pytest -n auto
```

#### Frontend Tests

```bash
cd frontend

# Unit tests (Jest + React Testing Library)
npm run test

# E2E tests (Playwright)
npm run test:e2e

# Generate coverage
npm run test:coverage
```

#### Test Coverage

Current coverage targets:
- **Backend**: 80%+ coverage goal
- **Frontend**: 70%+ coverage goal

View coverage reports:
- Backend: `backend/htmlcov/index.html`
- Frontend: `frontend/coverage/index.html`

### Adding New Features

<details>
<summary><b>Backend: Adding a New Endpoint</b></summary>

1. **Create schema** in `app/schemas/`
2. **Create model** (if needed) in `app/models/`
3. **Create service logic** in `app/services/`
4. **Create endpoint** in `app/api/v1/endpoints/`
5. **Add to router** in `app/api/v1/__init__.py`
6. **Write tests** in `tests/`
7. **Update API docs** (automatic via FastAPI)

Example:
```python
# app/api/v1/endpoints/example.py
from fastapi import APIRouter, Depends
from app.api.v1.dependencies import get_current_user
from app.models.user import UserModel

router = APIRouter(prefix="/example", tags=["Example"])

@router.get("/")
async def get_example(user: UserModel = Depends(get_current_user)):
    return {"message": "Hello, World!"}
```

</details>

<details>
<summary><b>Frontend: Adding a New Page</b></summary>

1. **Create page component** in `src/pages/`
2. **Create services** (if needed) in `src/services/`
3. **Add route** in `src/App.tsx`
4. **Create types** (if needed) in `src/types/`
5. **Add to navigation** in `src/components/layout/Header.tsx`
6. **Write tests** in `src/pages/__tests__/`

Example:
```tsx
// src/pages/ExamplePage.tsx
import { Header } from '@/components/layout/Header';

export default function ExamplePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold">Example Page</h1>
      </main>
    </div>
  );
}
```

</details>

---

## Deployment

### Docker Production Deployment

#### Prerequisites
- Docker and Docker Compose installed
- Domain name configured
- SSL certificates (Let's Encrypt recommended)
- Environment variables configured in `.env`

#### Build and Deploy

```bash
# Build production images
docker-compose build --no-cache

# Start services
docker-compose up -d

# Verify health
docker-compose ps
docker-compose logs backend
docker-compose logs frontend

# Monitor resource usage
docker stats
```

#### Environment-Specific Configurations

<details>
<summary><b>Production Configuration</b></summary>

```bash
# .env for production
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com
FRONTEND_URL=https://yourdomain.com

# Disable debug features
FASTAPI_DEBUG=false

# Enable production monitoring
SENTRY_DSN=https://your-sentry-dsn
PROMETHEUS_MONITORING_ENABLED=true

# Set production-grade secrets
SECRET_KEY=$(openssl rand -hex 32)
API_INTERNAL_KEY=$(openssl rand -hex 16)
```

</details>

<details>
<summary><b>Staging Configuration</b></summary>

```bash
# .env for staging
ENVIRONMENT=staging
ALLOWED_ORIGINS=https://staging.yourdomain.com
FRONTEND_URL=https://staging.yourdomain.com

# Enable API docs for testing
FASTAPI_DOCS_ENABLED=true
```

</details>

### Cloud Deployment Options

#### DigitalOcean

The project is pre-configured for DigitalOcean with:
- Docker Compose orchestration
- Nginx reverse proxy
- Let's Encrypt SSL automation
- Cloudflare tunnel support

Docker images can be pushed to DigitalOcean Container Registry:

```bash
# Tag images
docker tag backend registry.digitalocean.com/your-registry/backend:latest
docker tag frontend registry.digitalocean.com/your-registry/frontend:latest

# Push images
docker push registry.digitalocean.com/your-registry/backend:latest
docker push registry.digitalocean.com/your-registry/frontend:latest
```

#### AWS, GCP, Azure

The containerized architecture supports deployment to any cloud provider:

- **AWS**: ECS, EKS, or App Runner
- **GCP**: Cloud Run, GKE, or Compute Engine
- **Azure**: Container Instances, AKS, or App Service

### Scaling Considerations

#### Horizontal Scaling

- **Backend**: Stateless design allows easy horizontal scaling
- **Frontend**: Static files served via CDN
- **Weaviate**: Supports clustering for high availability
- **MongoDB**: Use Atlas clusters with auto-scaling

#### Performance Optimization

```yaml
# docker-compose.yml resource limits
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 6G  # OCR processing needs memory
        reservations:
          memory: 2G
      replicas: 3  # Scale horizontally
```

#### Load Balancing

Use Nginx or cloud load balancers for distributing traffic:

```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

---

## Monitoring & Observability

### Prometheus Metrics

Access Prometheus at http://localhost:9090

**Available Metrics:**

```promql
# Request metrics
http_requests_total{method="POST", endpoint="/api/chat/messages"}
http_request_duration_seconds

# Weaviate metrics
weaviate_query_duration_seconds
weaviate_objects_total
weaviate_vector_index_size_bytes

# Application metrics
chat_messages_total
document_processing_duration_seconds
openai_api_calls_total
openai_token_usage_total
cache_hit_rate
```

### Grafana Dashboards

Access Grafana at http://localhost:3001 (default: admin/admin)

**Pre-configured Dashboards:**

1. **Weaviate Overview**
   - Query performance
   - Index size and growth
   - Multi-tenancy statistics
   - Resource utilization

2. **Application Metrics** (custom dashboard)
   - Request rates and latencies
   - Error rates by endpoint
   - Token usage and costs
   - Cache performance

3. **System Health**
   - Container resource usage
   - Database connections
   - API response times

### Logging

**Structured JSON Logging:**

```python
# Backend logs (app/core/logging_config.py)
{
  "timestamp": "2025-11-19T10:30:00Z",
  "level": "INFO",
  "logger": "app.services.ai_agent",
  "message": "Generated response",
  "extra": {
    "user_id": "uuid",
    "conversation_id": "uuid",
    "tokens": 1234,
    "latency_ms": 2500,
    "model": "gpt-4o-mini"
  }
}
```

**Log Aggregation:**

```bash
# View logs with Docker
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f weaviate

# Filter by service
docker-compose logs backend | grep ERROR
```

### Sentry Error Tracking

Configure Sentry for production error tracking:

```python
# Automatic error capture
sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.environment,
    traces_sample_rate=0.1,  # 10% performance monitoring
)
```

View errors, performance issues, and user feedback at https://sentry.io

### Health Checks

**Endpoints:**
- Backend: http://localhost:8000/api/health
- Weaviate: http://localhost:8080/v1/.well-known/ready
- Frontend: http://localhost/health

**Health Check Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T10:30:00Z",
  "services": {
    "mongodb": "connected",
    "weaviate": "ready",
    "openai": "operational"
  },
  "version": "1.0.0"
}
```

---

## Advanced Features

### Custom RAG Configuration

Tune the RAG pipeline for your use case:

```python
# In .env or config
DEFAULT_HYBRID_ALPHA=0.75  # 0.0=pure keyword, 1.0=pure vector
RERANKING_TOP_K=10         # Results after reranking
COMPRESSION_TARGET_TOKENS=3500  # Context compression target
```

**Alpha Parameter Guide:**
- `0.0`: Pure BM25 keyword search (best for exact matches, codes)
- `0.5`: Balanced hybrid search
- `0.75`: Vector-heavy (default, best for semantic questions)
- `1.0`: Pure vector search (best for conceptual queries)

### Multi-Tenancy & Data Isolation

Weaviate multi-tenancy ensures complete data isolation:

```python
# Each user gets their own tenant
tenant = user.user_id

# All queries are scoped to tenant
results = weaviate_client.query.get(
    "DocumentChunk",
    ["content", "document_title"]
).with_tenant(tenant).with_near_vector({"vector": embedding}).do()
```

**Benefits:**
- Complete data isolation per user
- No cross-tenant data leaks
- Efficient resource sharing
- Easy user data deletion (GDPR compliance)

### Conversation Memory

Automatic conversation summarization for long chats:

```python
# Summarizes every N messages (default: 10)
MEMORY_SUMMARIZATION_INTERVAL=10

# Maximum tokens in summary
MEMORY_MAX_SUMMARY_TOKENS=500

# Summary included in context
MEMORY_MAX_CONTEXT_TOKENS=500
```

**How it works:**
1. Every 10 messages, summarize conversation so far
2. Summary stored in conversation metadata
3. Summary included in future prompts for context
4. Reduces token usage while maintaining context

### Analytics & Insights

Track usage patterns and user engagement:

```python
# Enable analytics
ENABLE_ANALYTICS_TRACKING=true
ANALYTICS_BATCH_SIZE=100

# Query analytics endpoint (admin only)
GET /api/admin/analytics
```

**Available Metrics:**
- Total queries per day/week/month
- Average response time
- Most common queries
- User engagement (messages per user)
- Document usage (most referenced docs)
- Feedback ratings distribution

### Feedback Loop

Collect user feedback for model improvement:

```typescript
// Frontend: Thumbs up/down with optional comment
POST /api/chat/feedback
{
  "message_id": "uuid",
  "feedback": "positive" | "negative",
  "comment": "Helpful explanation!"
}
```

**Use Cases:**
- Identify low-quality responses
- Track user satisfaction
- Improve prompts and RAG pipeline
- Fine-tune models (future feature)

---

## Security

### Authentication Flow

```
1. User registers → Email verification sent
2. User clicks verification link → Email verified
3. Admin reviews → Approves/rejects account
4. User logs in → Session created (JWT)
5. Session cookie set (HttpOnly, Secure)
6. Subsequent requests → Session validated
```

### Password Security

- **Hashing**: Argon2id (winner of Password Hashing Competition)
- **Salt**: Automatic per-password random salt
- **Pepper**: Application-wide secret key
- **Work Factor**: Tuned for 2-second hash time

### Session Management

- **Storage**: MongoDB sessions collection
- **Expiration**: 30 days (configurable)
- **Refresh**: Automatic on activity
- **Invalidation**: Logout deletes session
- **Cookie**: HttpOnly, Secure, SameSite=Lax

### API Security

- **CORS**: Configurable allowed origins
- **Rate Limiting**: Per-user and per-IP limits
- **Input Validation**: Pydantic models for all inputs
- **SQL Injection**: N/A (NoSQL database)
- **XSS Protection**: React auto-escaping + CSP headers
- **CSRF**: SameSite cookies + token validation

### Data Privacy

- **GDPR Compliance**: User data deletion via admin panel
- **Multi-Tenancy**: Complete data isolation
- **Encryption**: TLS/HTTPS for all communications
- **Secrets**: Environment variables, never in code
- **Audit Logs**: All admin actions logged

### Security Best Practices

1. **Change Default Credentials**
   ```bash
   # Generate secure secrets
   openssl rand -hex 32  # For SECRET_KEY
   openssl rand -hex 16  # For API_INTERNAL_KEY
   ```

2. **Enable HTTPS in Production**
   - Use Let's Encrypt for free SSL certificates
   - Configure Nginx with TLS 1.3
   - Enable HSTS headers

3. **Restrict Admin Access**
   - Use strong passwords for admin accounts
   - Enable 2FA (future feature)
   - Monitor admin actions via audit logs

4. **Regular Updates**
   - Keep dependencies updated
   - Monitor security advisories
   - Apply patches promptly

---

## Contributing

We welcome contributions from the community! Whether it's bug fixes, new features, documentation improvements, or feedback, your input is valuable.

### How to Contribute

1. **Fork the repository**

```bash
git fork https://github.com/yourusername/building-machinery-chatbot.git
```

2. **Create a feature branch**

```bash
git checkout -b feature/your-feature-name
```

3. **Make your changes**

- Follow existing code style and conventions
- Write tests for new features
- Update documentation as needed
- Ensure all tests pass

4. **Commit your changes**

```bash
git commit -m "Add: Brief description of your changes"
```

Follow conventional commit format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

5. **Push to your fork**

```bash
git push origin feature/your-feature-name
```

6. **Create a Pull Request**

- Provide a clear description of your changes
- Reference any related issues
- Ensure CI checks pass
- Request review from maintainers

### Development Guidelines

#### Code Style

**Backend (Python):**
- Follow PEP 8 style guide
- Use Black for formatting (88 char line length)
- Use Ruff for linting
- Type hints for all function signatures
- Docstrings for all public functions

**Frontend (TypeScript):**
- Follow Airbnb style guide
- Use Prettier for formatting
- ESLint for linting
- TypeScript strict mode
- Props interfaces for all components

#### Testing Requirements

- Write unit tests for new functions
- Write integration tests for new endpoints
- Maintain or improve code coverage
- Ensure all tests pass before submitting PR

#### Documentation

- Update README.md for new features
- Add JSDoc/docstrings for new functions
- Update API documentation
- Include usage examples

### Reporting Issues

**Bug Reports:**
- Use the issue template
- Include reproduction steps
- Provide error messages and logs
- Specify environment (OS, versions, etc.)

**Feature Requests:**
- Describe the use case
- Explain the expected behavior
- Consider alternative solutions
- Discuss implementation approach

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Focus on the best outcome for the project

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Building Machinery AI Chatbot Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Support

### Getting Help

- **Documentation**: Read this README and code comments
- **API Docs**: http://localhost:8000/api/docs
- **Issues**: [GitHub Issues](https://github.com/yourusername/building-machinery-chatbot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/building-machinery-chatbot/discussions)

### FAQ

<details>
<summary><b>Why is document processing taking so long?</b></summary>

Document processing time depends on:
- **File size**: Larger files take longer
- **OCR requirements**: Images and scanned PDFs need OCR
- **Processor**: Aryn is faster than local Docling
- **Resources**: Ensure adequate memory (6GB for backend)

Typical processing times:
- Small PDF (10 pages, no OCR): 10-30 seconds
- Large PDF (100 pages, with OCR): 2-5 minutes
- Images: 30-60 seconds per image

</details>

<details>
<summary><b>How do I improve response quality?</b></summary>

1. **Upload relevant documents**: More context = better answers
2. **Tune hybrid search alpha**: Adjust between keyword and vector search
3. **Enable reranking**: Cohere reranking improves relevance
4. **Provide feedback**: Thumbs up/down helps identify issues
5. **Refine prompts**: Edit system prompt in `ai_agent.py`

</details>

<details>
<summary><b>How much does it cost to run?</b></summary>

**Monthly Costs (estimated for 1000 users, 10k queries/month):**

- **OpenAI Embeddings**: $20-40 (text-embedding-3-large)
- **OpenAI Chat**: $50-150 (gpt-4o-mini)
- **Cohere Reranking**: $10-30 (optional)
- **MongoDB Atlas**: $0-57 (free tier to M10)
- **Infrastructure**: $50-200 (cloud hosting)
- **Total**: $130-477/month

**Cost Reduction:**
- Enable caching (70-80% cost reduction)
- Use cheaper models (gpt-3.5-turbo)
- Optimize retrieval (fewer chunks)

</details>

<details>
<summary><b>Can I use a different LLM?</b></summary>

Yes! The project uses Pydantic AI which supports:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- Groq (Llama, Mixtral)
- Ollama (local models)

Modify `app/services/ai_agent.py` to change the model.

</details>

<details>
<summary><b>How do I backup my data?</b></summary>

**MongoDB:**
```bash
# Backup
mongodump --uri="your-mongodb-uri" --out=/backup

# Restore
mongorestore --uri="your-mongodb-uri" /backup
```

**Weaviate:**
```bash
# Backup volumes
docker-compose stop weaviate
docker run --rm -v baumaschinen-weaviate-data:/data -v $(pwd):/backup ubuntu tar czf /backup/weaviate-backup.tar.gz /data
docker-compose start weaviate
```

</details>

### Community & Contact

- **GitHub**: [@yourusername](https://github.com/yourusername)
- **Email**: support@yourdomain.com
- **Discord**: [Join our community](https://discord.gg/yourinvite) (if applicable)
- **Twitter**: [@yourhandle](https://twitter.com/yourhandle) (if applicable)

---

## Acknowledgments

This project builds upon the excellent work of many open-source projects and communities:

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[React](https://reactjs.org/)** - UI library
- **[Weaviate](https://weaviate.io/)** - Vector database
- **[OpenAI](https://openai.com/)** - LLM and embeddings
- **[Docling](https://github.com/DS4SD/docling)** - Document processing
- **[Pydantic AI](https://ai.pydantic.dev/)** - AI agent framework
- **[shadcn/ui](https://ui.shadcn.com/)** - React component library
- **[Tailwind CSS](https://tailwindcss.com/)** - CSS framework

Special thanks to all contributors and the open-source community!

---

<div align="center">

**Built with by [Harshal Vankudre]**

If you find this project useful, please consider giving it a star on GitHub!

[![GitHub stars](https://img.shields.io/github/stars/yourusername/building-machinery-chatbot?style=social)](https://github.com/yourusername/building-machinery-chatbot/stargazers)

</div>
