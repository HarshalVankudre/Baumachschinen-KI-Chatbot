"""
MongoDB Schema Validation for Users Collection (DB-003)
Defines required fields, data types, and constraints
"""

from datetime import datetime

# Users Collection Schema Validation
USERS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "user_id",
            "username",
            "email",
            "password_hash",
            "authorization_level",
            "account_status",
            "email_verified",
            "created_at"
        ],
        "properties": {
            "_id": {
                "bsonType": "objectId"
            },
            "user_id": {
                "bsonType": "string",
                "description": "UUID string (unique identifier)",
                "pattern": "^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
            },
            "username": {
                "bsonType": "string",
                "description": "Unique username (3-30 characters)",
                "minLength": 3,
                "maxLength": 30
            },
            "email": {
                "bsonType": "string",
                "description": "Valid email address",
                "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
            },
            "password_hash": {
                "bsonType": "string",
                "description": "Argon2 password hash",
                "minLength": 1
            },
            "authorization_level": {
                "enum": ["regular", "superuser", "admin"],
                "description": "User access level"
            },
            "account_status": {
                "enum": [
                    "pending_verification",
                    "pending_approval",
                    "active",
                    "rejected",
                    "suspended"
                ],
                "description": "Account activation status"
            },
            "email_verified": {
                "bsonType": "bool",
                "description": "Email verification status"
            },
            "email_verification_token": {
                "bsonType": ["string", "null"],
                "description": "UUID token for email verification"
            },
            "email_verification_expires": {
                "bsonType": ["date", "null"],
                "description": "Email verification token expiration"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Account creation timestamp"
            },
            "updated_at": {
                "bsonType": ["date", "null"],
                "description": "Last update timestamp"
            },
            "last_login": {
                "bsonType": ["date", "null"],
                "description": "Last login timestamp"
            },
            "approved_by": {
                "bsonType": ["string", "null"],
                "description": "Admin user_id who approved account"
            },
            "approved_at": {
                "bsonType": ["date", "null"],
                "description": "Approval timestamp"
            },
            "ui_language": {
                "bsonType": "string",
                "description": "UI language preference",
                "pattern": "^[a-z]{2}$"
            },
            "preferences": {
                "bsonType": "object",
                "description": "User preferences",
                "properties": {
                    "theme": {
                        "bsonType": ["string", "null"],
                        "description": "UI theme preference"
                    },
                    "notifications_enabled": {
                        "bsonType": "bool",
                        "description": "Notifications enabled"
                    }
                }
            }
        }
    }
}


def get_users_collection_options():
    """
    Get collection options for users collection

    Returns:
        Dictionary of collection options
    """
    return {
        "validator": USERS_SCHEMA,
        "validationLevel": "strict",
        "validationAction": "error"
    }


def get_default_user_document(
    user_id: str,
    username: str,
    email: str,
    password_hash: str
) -> dict:
    """
    Create a default user document with required fields

    Args:
        user_id: UUID string
        username: Username
        email: Email address
        password_hash: Argon2 hash

    Returns:
        User document dictionary
    """
    return {
        "user_id": user_id,
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "authorization_level": "regular",
        "account_status": "pending_verification",
        "email_verified": False,
        "email_verification_token": None,
        "email_verification_expires": None,
        "created_at": datetime.utcnow(),
        "updated_at": None,
        "last_login": None,
        "approved_by": None,
        "approved_at": None,
        "ui_language": "en",
        "preferences": {
            "theme": None,
            "notifications_enabled": True
        }
    }
