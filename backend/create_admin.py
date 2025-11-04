"""
Create Initial Admin User

This script creates the first admin account that can approve other users.
Run this once to bootstrap the admin system.
"""
import asyncio
from datetime import datetime, UTC
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.utils.security import hash_password, generate_token

settings = get_settings()


async def create_admin_user():
    """Create initial admin user."""
    # Admin credentials
    admin_username = "admin"
    admin_email = "admin@buildingmachinery.ai"
    admin_password = "AdminPassword123!"  # Change this after first login!

    print("Creating initial admin account...")
    print(f"Username: {admin_username}")
    print(f"Email: {admin_email}")
    print(f"Password: {admin_password}")
    print("\nIMPORTANT: Change this password after logging in!")
    print("-" * 60)

    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_database]

    try:
        # Check if admin already exists
        existing_admin = await db.users.find_one({"username": admin_username.lower()})
        if existing_admin:
            print(f"\nAdmin user '{admin_username}' already exists!")
            return

        # Generate user ID and hash password
        user_id = generate_token()
        password_hash = hash_password(admin_password)

        # Create admin user document
        admin_user = {
            "user_id": user_id,
            "username": admin_username.lower(),
            "email": admin_email.lower(),
            "password_hash": password_hash,
            "authorization_level": "admin",
            "account_status": "active",
            "email_verified": True,
            "email_verification_token": None,
            "email_verification_expires": None,
            "created_at": datetime.now(UTC),
            "last_login": None,
            "approved_by": None,
            "approved_at": None,
            "rejected_by": None,
            "rejected_at": None,
            "settings": {}
        }

        # Insert into database
        result = await db.users.insert_one(admin_user)
        print(f"\n[SUCCESS] Admin user created successfully!")
        print(f"User ID: {user_id}")
        print(f"MongoDB ID: {result.inserted_id}")
        print("\nYou can now log in with these credentials.")

    except Exception as e:
        print(f"\n[ERROR] Error creating admin user: {str(e)}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(create_admin_user())
