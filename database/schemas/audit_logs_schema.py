"""
MongoDB Schema Validation for Audit Logs Collection (DB-007)
Defines immutable audit trail of admin actions
"""

from datetime import datetime
from typing import Optional, Dict, Any

# Audit Logs Collection Schema Validation
AUDIT_LOGS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "log_id",
            "timestamp",
            "admin_user_id",
            "admin_username",
            "action_type",
            "ip_address"
        ],
        "properties": {
            "_id": {
                "bsonType": "objectId"
            },
            "log_id": {
                "bsonType": "string",
                "description": "UUID string (unique identifier)",
                "pattern": "^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
            },
            "timestamp": {
                "bsonType": "date",
                "description": "Action timestamp"
            },
            "admin_user_id": {
                "bsonType": "string",
                "description": "Admin who performed action"
            },
            "admin_username": {
                "bsonType": "string",
                "description": "Admin username (denormalized)"
            },
            "action_type": {
                "enum": [
                    "approve_user",
                    "reject_user",
                    "change_authorization",
                    "delete_user",
                    "delete_document",
                    "system_config_change"
                ],
                "description": "Type of action performed"
            },
            "target_user_id": {
                "bsonType": ["string", "null"],
                "description": "User ID affected by action"
            },
            "target_username": {
                "bsonType": ["string", "null"],
                "description": "Username affected (denormalized)"
            },
            "target_document_id": {
                "bsonType": ["string", "null"],
                "description": "Document ID for document deletions"
            },
            "details": {
                "bsonType": "object",
                "description": "Action details",
                "properties": {
                    "previous_state": {
                        "bsonType": ["object", "null"],
                        "description": "State before action"
                    },
                    "new_state": {
                        "bsonType": ["object", "null"],
                        "description": "State after action"
                    },
                    "reason": {
                        "bsonType": ["string", "null"],
                        "description": "Reason for action"
                    },
                    "additional_info": {
                        "bsonType": ["object", "null"],
                        "description": "Additional information"
                    }
                }
            },
            "ip_address": {
                "bsonType": "string",
                "description": "Admin's IP address"
            },
            "user_agent": {
                "bsonType": ["string", "null"],
                "description": "Admin's browser/client"
            }
        }
    }
}


def get_audit_logs_collection_options():
    """
    Get collection options for audit logs collection

    Returns:
        Dictionary of collection options
    """
    return {
        "validator": AUDIT_LOGS_SCHEMA,
        "validationLevel": "strict",
        "validationAction": "error"
    }


def create_audit_log_document(
    log_id: str,
    admin_user_id: str,
    admin_username: str,
    action_type: str,
    ip_address: str,
    target_user_id: Optional[str] = None,
    target_username: Optional[str] = None,
    target_document_id: Optional[str] = None,
    previous_state: Optional[Dict[str, Any]] = None,
    new_state: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None,
    user_agent: Optional[str] = None
) -> dict:
    """
    Create an audit log document

    Args:
        log_id: UUID string
        admin_user_id: Admin's user ID
        admin_username: Admin's username
        action_type: Type of action
        ip_address: Admin's IP address
        target_user_id: Affected user ID
        target_username: Affected username
        target_document_id: Affected document ID
        previous_state: State before action
        new_state: State after action
        reason: Reason for action
        additional_info: Additional information
        user_agent: Browser/client info

    Returns:
        Audit log document dictionary
    """
    return {
        "log_id": log_id,
        "timestamp": datetime.utcnow(),
        "admin_user_id": admin_user_id,
        "admin_username": admin_username,
        "action_type": action_type,
        "target_user_id": target_user_id,
        "target_username": target_username,
        "target_document_id": target_document_id,
        "details": {
            "previous_state": previous_state,
            "new_state": new_state,
            "reason": reason,
            "additional_info": additional_info
        },
        "ip_address": ip_address,
        "user_agent": user_agent
    }
