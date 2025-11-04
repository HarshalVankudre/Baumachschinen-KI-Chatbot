"""
Test fixtures and configuration for Building Machinery AI Chatbot Backend.

This module provides reusable fixtures for:
- Test database setup and cleanup
- Mock external services (Pinecone, OpenAI, PostgreSQL API, SMTP)
- Test users with different authorization levels
- Test client for API requests
- Sample data generators
"""

import asyncio
import os
from datetime import datetime, timedelta, UTC
from typing import AsyncGenerator, Dict, Generator, Any
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient

# Import app components
from app.main import app
from app.config import Settings, get_settings
from app.core.database import get_database, close_mongo_connection
from app.core.session import create_session_sync as create_session
from app.utils.security import hash_password


# ============================================================================
# Environment Configuration
# ============================================================================

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Override settings for test environment."""
    os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
    os.environ["DATABASE_NAME"] = "test_building_machinery_chatbot"
    os.environ["PINECONE_API_KEY"] = "test-pinecone-key"
    os.environ["PINECONE_INDEX_NAME"] = "test-index"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["POSTGRESQL_API_URL"] = "http://test-postgresql-api.com"
    os.environ["POSTGRESQL_API_KEY_BASIC"] = "test-basic-key"
    os.environ["POSTGRESQL_API_KEY_ELEVATED"] = "test-elevated-key"
    os.environ["POSTGRESQL_API_KEY_ADMIN"] = "test-admin-key"
    os.environ["SMTP_HOST"] = "smtp.test.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USERNAME"] = "test@test.com"
    os.environ["SMTP_PASSWORD"] = "test-password"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-32-chars-long"
    os.environ["ENVIRONMENT"] = "test"

    return get_settings()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db(test_settings: Settings) -> AsyncGenerator[AsyncIOMotorClient, None]:
    """
    Create a test database connection and clean up after tests.

    This fixture:
    1. Connects to test MongoDB instance
    2. Yields the database for tests
    3. Drops all collections after each test (isolation)
    """
    client = AsyncIOMotorClient(test_settings.MONGODB_URI)
    db = client[test_settings.DATABASE_NAME]

    yield db

    # Cleanup: Drop all collections after test
    collection_names = await db.list_collection_names()
    for collection_name in collection_names:
        await db[collection_name].drop()

    client.close()


# ============================================================================
# HTTP Client Fixtures
# ============================================================================



@pytest.fixture
async def client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for testing API endpoints.

    Usage:
        async def test_endpoint(client):
            response = await client.get("/api/health")
            assert response.status_code == 200
    """
    from httpx import ASGITransport
    
    # Patch get_database to return test_db
    with patch("app.core.database.get_database") as mock_get_db:
        mock_get_db.return_value = test_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac


@pytest.fixture
def sync_client() -> Generator[TestClient, None, None]:
    """
    Create synchronous test client for non-async tests.

    Usage:
        def test_endpoint(sync_client):
            response = sync_client.get("/api/health")
            assert response.status_code == 200
    """
    with TestClient(app) as client:
        yield client


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
async def regular_user(test_db) -> Dict[str, Any]:
    """Create a regular user with active status."""
    user_data = {
        "user_id": "test-regular-user-id",
        "username": "regular_user",
        "email": "regular@test.com",
        "password_hash": hash_password("Test123!@#Password"),
        "authorization_level": "regular",
        "account_status": "active",
        "email_verified": True,
        "created_at": datetime.now(UTC),
        "last_login": None,
    }

    await test_db.users.insert_one(user_data)
    return user_data


@pytest.fixture
async def superuser(test_db) -> Dict[str, Any]:
    """Create a superuser with active status."""
    user_data = {
        "user_id": "test-superuser-id",
        "username": "superuser",
        "email": "superuser@test.com",
        "password_hash": hash_password("Test123!@#Password"),
        "authorization_level": "superuser",
        "account_status": "active",
        "email_verified": True,
        "created_at": datetime.now(UTC),
        "last_login": None,
    }

    await test_db.users.insert_one(user_data)
    return user_data


@pytest.fixture
async def admin_user(test_db) -> Dict[str, Any]:
    """Create an admin user with active status."""
    user_data = {
        "user_id": "test-admin-user-id",
        "username": "admin_user",
        "email": "admin@test.com",
        "password_hash": hash_password("Test123!@#Password"),
        "authorization_level": "admin",
        "account_status": "active",
        "email_verified": True,
        "created_at": datetime.now(UTC),
        "last_login": None,
    }

    await test_db.users.insert_one(user_data)
    return user_data


@pytest.fixture
async def pending_user(test_db) -> Dict[str, Any]:
    """Create a pending user awaiting approval."""
    user_data = {
        "user_id": "test-pending-user-id",
        "username": "pending_user",
        "email": "pending@test.com",
        "password_hash": hash_password("Test123!@#Password"),
        "authorization_level": "regular",
        "account_status": "pending_approval",
        "email_verified": True,
        "created_at": datetime.now(UTC),
        "last_login": None,
    }

    await test_db.users.insert_one(user_data)
    return user_data


# ============================================================================
# Session/Auth Fixtures
# ============================================================================

@pytest.fixture
async def regular_user_session(test_db, regular_user) -> str:
    """Create a session cookie for regular user."""
    session_data = create_session(
        user_id=regular_user["user_id"],
        username=regular_user["username"],
        authorization_level=regular_user["authorization_level"],
    )

    # Store session in database
    await test_db.users.update_one(
        {"user_id": regular_user["user_id"]},
        {"$set": {"session_token": session_data["session_token"]}}
    )

    return session_data["session_id"]


@pytest.fixture
async def superuser_session(test_db, superuser) -> str:
    """Create a session cookie for superuser."""
    session_data = create_session(
        user_id=superuser["user_id"],
        username=superuser["username"],
        authorization_level=superuser["authorization_level"],
    )

    await test_db.users.update_one(
        {"user_id": superuser["user_id"]},
        {"$set": {"session_token": session_data["session_token"]}}
    )

    return session_data["session_id"]


@pytest.fixture
async def admin_session(test_db, admin_user) -> str:
    """Create a session cookie for admin."""
    session_data = create_session(
        user_id=admin_user["user_id"],
        username=admin_user["username"],
        authorization_level=admin_user["authorization_level"],
    )

    await test_db.users.update_one(
        {"user_id": admin_user["user_id"]},
        {"$set": {"session_token": session_data["session_token"]}}
    )

    return session_data["session_id"]


# ============================================================================
# Mock External Services
# ============================================================================

@pytest.fixture
def mock_pinecone():
    """Mock Pinecone vector database service."""
    with patch("app.services.pinecone_service.get_pinecone_service") as mock_get_service:
        mock_service = MagicMock()
        mock_index = MagicMock()

        # Mock query method
        mock_index.query.return_value = {
            "matches": [
                {
                    "id": "chunk-1",
                    "score": 0.95,
                    "metadata": {
                        "document_id": "doc-1",
                        "filename": "manual.pdf",
                        "text_content": "Sample manual content",
                        "category": "Manuals",
                    }
                }
            ]
        }

        # Mock upsert method
        mock_index.upsert.return_value = {"upserted_count": 1}

        # Mock delete method
        mock_index.delete.return_value = {}

        # Set up the service mock
        mock_service.index = mock_index
        
        # Mock service methods - these call the mocked index
        def mock_query_vectors(vector, top_k=5, filter_dict=None):
            return mock_index.query(
                vector=vector,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=True
            )
        
        def mock_upsert_vectors(vectors):
            return mock_index.upsert(vectors=vectors)
        
        def mock_delete_vectors_by_filter(filter_dict):
            return mock_index.delete(filter=filter_dict)
        
        def mock_delete_vectors_by_ids(ids):
            return mock_index.delete(ids=ids)
        
        mock_service.query_vectors = mock_query_vectors
        mock_service.upsert_vectors = mock_upsert_vectors
        mock_service.delete_vectors_by_filter = mock_delete_vectors_by_filter
        mock_service.delete_vectors_by_ids = mock_delete_vectors_by_ids
        
        mock_get_service.return_value = mock_service
        yield mock_index


@pytest.fixture
def mock_openai():
    """Mock OpenAI API service."""
    with patch("app.services.openai_service.get_openai_service") as mock_get_service:
        mock_service = MagicMock()
        mock_client = AsyncMock()

        # Mock embeddings
        mock_embeddings = AsyncMock()
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock(embedding=[0.1] * 3072)]
        mock_embeddings.create = AsyncMock(return_value=mock_embedding_response)
        mock_client.embeddings = mock_embeddings

        # Mock chat completions
        mock_chat = AsyncMock()
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(
                message=MagicMock(content="This is a test AI response."),
                finish_reason="stop"
            )
        ]
        mock_completion.usage = MagicMock(
            prompt_tokens=50,
            completion_tokens=20,
            total_tokens=70
        )
        mock_chat.completions.create = AsyncMock(return_value=mock_completion)
        mock_client.chat = mock_chat

        # Set up the service mock
        mock_service.client = mock_client
        mock_service.embedding_model = "text-embedding-3-large"
        mock_service.chat_model = "gpt-4o"
        mock_service.max_tokens = 4096
        mock_service.temperature = 0.7
        
        # Mock service methods - these call the mocked client
        async def mock_generate_embedding(text):
            response = await mock_client.embeddings.create(
                model=mock_service.embedding_model,
                input=text
            )
            return response.data[0].embedding
        
        async def mock_generate_embeddings_batch(texts):
            response = await mock_client.embeddings.create(
                model=mock_service.embedding_model,
                input=texts
            )
            return [item.embedding for item in response.data]
        
        async def mock_generate_chat_completion(messages, stream=False, temperature=None, max_tokens=None):
            response = await mock_client.chat.completions.create(
                model=mock_service.chat_model,
                messages=messages,
                stream=stream,
                temperature=temperature or mock_service.temperature,
                max_tokens=max_tokens or mock_service.max_tokens
            )
            if stream:
                async def mock_stream():
                    yield response
                return mock_stream()
            return {
                "content": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        
        mock_service.generate_embedding = mock_generate_embedding
        mock_service.generate_embeddings_batch = mock_generate_embeddings_batch
        mock_service.generate_chat_completion = mock_generate_chat_completion
        
        mock_get_service.return_value = mock_service
        yield mock_client


@pytest.fixture
def mock_postgresql_api():
    """Mock PostgreSQL REST API - patches the service instance's client."""
    with patch("app.services.postgresql_service.get_postgresql_service") as mock_get_service:
        # Create mock service
        mock_service = MagicMock()
        mock_client = AsyncMock()

        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={
            "id": "cat-320",
            "model": "CAT 320",
            "type": "Excavator",
            "specs": {
                "weight_kg": 20000,
                "engine_power_hp": 158,
                "fuel_capacity_l": 400
            }
        })

        mock_client.get.return_value = mock_response
        mock_client.post.return_value = mock_response

        # Set up the mock service
        mock_service.client = mock_client
        mock_service._get_api_key = MagicMock(return_value="test-basic-key")
        mock_service._get_headers = MagicMock(return_value={"X-API-Key": "test-basic-key", "Content-Type": "application/json"})
        
        # Mock the service methods to use the mock client and capture headers
        async def mock_get_machinery_by_id(machinery_id, authorization_level):
            headers = mock_service._get_headers(authorization_level)
            response = await mock_client.get(f"/machinery/{machinery_id}", headers=headers)
            if response.status_code == 200:
                return await response.json()
            return None
        
        async def mock_search_machinery(query=None, filters=None, authorization_level="regular", limit=10, offset=0):
            headers = mock_service._get_headers(authorization_level)
            response = await mock_client.post("/machinery/search", json=filters or {}, headers=headers)
            return {"data": [await response.json()]}

        mock_service.get_machinery_by_id = mock_get_machinery_by_id
        mock_service.search_machinery = mock_search_machinery
        
        mock_get_service.return_value = mock_service
        yield mock_client


@pytest.fixture
def mock_smtp():
    """Mock SMTP email service - patches aiosmtplib.send directly."""
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock:
        # Mock successful email send (aiosmtplib.send returns None on success)
        mock.return_value = None
        yield mock


# ============================================================================
# Sample Data Generators
# ============================================================================

@pytest.fixture
def sample_conversation(regular_user) -> Dict[str, Any]:
    """Generate sample conversation data."""
    return {
        "conversation_id": "test-conversation-id",
        "user_id": regular_user["user_id"],
        "title": "Test Conversation",
        "created_at": datetime.now(UTC),
        "last_message_at": datetime.now(UTC),
        "message_count": 2,
        "messages": [
            {
                "message_id": "msg-1",
                "role": "user",
                "content": "What is the fuel capacity of CAT 320?",
                "timestamp": datetime.now(UTC),
            },
            {
                "message_id": "msg-2",
                "role": "assistant",
                "content": "The CAT 320 has a fuel capacity of 400 liters.",
                "timestamp": datetime.now(UTC),
                "metadata": {
                    "sources": ["postgresql"],
                    "tokens_used": 50,
                }
            }
        ]
    }


@pytest.fixture
def sample_document(superuser) -> Dict[str, Any]:
    """Generate sample document metadata."""
    return {
        "document_id": "test-doc-id",
        "filename": "test_manual.pdf",
        "category": "Manuals",
        "uploader_id": superuser["user_id"],
        "uploader_name": superuser["username"],
        "upload_date": datetime.now(UTC),
        "file_size_bytes": 1024000,
        "processing_status": "completed",
        "chunk_count": 10,
        "deleted": False,
    }


@pytest.fixture
def sample_audit_log(admin_user) -> Dict[str, Any]:
    """Generate sample audit log entry."""
    return {
        "log_id": "test-log-id",
        "timestamp": datetime.now(UTC),
        "admin_user_id": admin_user["user_id"],
        "admin_username": admin_user["username"],
        "action_type": "approve_user",
        "target_user_id": "test-target-user-id",
        "target_username": "test_target_user",
        "details": {
            "authorization_level": "regular",
            "previous_state": "pending_approval",
            "new_state": "active",
        }
    }


# ============================================================================
# Utility Functions
# ============================================================================

def create_test_user_data(**overrides) -> Dict[str, Any]:
    """
    Helper function to create test user data with optional overrides.

    Usage:
        user = create_test_user_data(username="custom_user", authorization_level="admin")
    """
    default_data = {
        "user_id": "test-user-id",
        "username": "test_user",
        "email": "test@test.com",
        "password_hash": hash_password("Test123!@#Password"),
        "authorization_level": "regular",
        "account_status": "active",
        "email_verified": True,
        "created_at": datetime.now(UTC),
        "last_login": None,
    }

    default_data.update(overrides)
    return default_data


def create_test_message(**overrides) -> Dict[str, Any]:
    """Helper function to create test message data."""
    default_data = {
        "message_id": "test-msg-id",
        "role": "user",
        "content": "Test message content",
        "timestamp": datetime.now(UTC),
    }

    default_data.update(overrides)
    return default_data


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
