#!/usr/bin/env python3
"""
Create Admin User Script

Creates an admin user for initial system setup.
Can be run from the command line with optional arguments.

Usage:
    python scripts/create_admin.py
    python scripts/create_admin.py --username admin --email admin@example.com

Environment:
    Requires DATABASE_URL to be set (uses .env file by default)
"""

import argparse
import asyncio
import getpass
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker, create_schemas
from app.core.models import Role, User, UserRole, RoleNames
from app.shared.security import hash_password
from app.shared.validators import validate_password, validate_username


async def create_admin(
    username: str,
    email: str,
    password: str,
    first_name: str = "Admin",
    last_name: str = "User",
) -> None:
    """
    Create an admin user with the given credentials.

    Args:
        username: Admin username
        email: Admin email
        password: Admin password
        first_name: First name (default: "Admin")
        last_name: Last name (default: "User")
    """
    # Ensure schemas exist
    await create_schemas()

    async with async_session_maker() as session:
        # Check if username already exists
        result = await session.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none():
            print(f"Error: Username '{username}' already exists.")
            sys.exit(1)

        # Check if email already exists
        result = await session.execute(
            select(User).where(User.email == email.lower())
        )
        if result.scalar_one_or_none():
            print(f"Error: Email '{email}' already exists.")
            sys.exit(1)

        # Get admin role
        result = await session.execute(
            select(Role).where(Role.role_name == RoleNames.ADMIN)
        )
        admin_role = result.scalar_one_or_none()

        if not admin_role:
            print("Error: Admin role not found. Please run migrations first.")
            print("Run: alembic upgrade head")
            sys.exit(1)

        # Create user
        user = User(
            username=username,
            email=email.lower(),
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_verified=True,  # Admin is pre-verified
        )
        session.add(user)
        await session.flush()

        # Assign admin role
        user_role = UserRole(
            user_id=user.user_id,
            role_id=admin_role.role_id,
        )
        session.add(user_role)

        await session.commit()

        print(f"\n✓ Admin user created successfully!")
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        print(f"  Role: Admin")
        print(f"\nYou can now login at /api/v1/auth/login")


def get_password_interactive() -> str:
    """Get password interactively with confirmation."""
    while True:
        password = getpass.getpass("Password: ")

        # Validate password
        valid, error = validate_password(password)
        if not valid:
            print(f"Error: {error}")
            continue

        # Confirm password
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Error: Passwords do not match.")
            continue

        return password


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create an admin user for the Landfill Management System"
    )
    parser.add_argument(
        "--username",
        type=str,
        help="Admin username (will prompt if not provided)",
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Admin email (will prompt if not provided)",
    )
    parser.add_argument(
        "--password",
        type=str,
        help="Admin password (will prompt securely if not provided)",
    )
    parser.add_argument(
        "--first-name",
        type=str,
        default="Admin",
        help="First name (default: Admin)",
    )
    parser.add_argument(
        "--last-name",
        type=str,
        default="User",
        help="Last name (default: User)",
    )

    args = parser.parse_args()

    print("=" * 50)
    print("Landfill Management System - Create Admin User")
    print("=" * 50)
    print()

    # Get username
    username = args.username
    if not username:
        while True:
            username = input("Username: ").strip()
            valid, error = validate_username(username)
            if valid:
                break
            print(f"Error: {error}")

    # Get email
    email = args.email
    if not email:
        while True:
            email = input("Email: ").strip()
            if "@" in email and "." in email:
                break
            print("Error: Please enter a valid email address.")

    # Get password
    password = args.password
    if not password:
        password = get_password_interactive()

    # Get names
    first_name = args.first_name
    last_name = args.last_name

    if not args.first_name and not args.username:
        first_name = input("First name (default: Admin): ").strip() or "Admin"
    if not args.last_name and not args.username:
        last_name = input("Last name (default: User): ").strip() or "User"

    # Confirm
    print()
    print("Creating admin user with:")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Name: {first_name} {last_name}")
    print()

    confirm = input("Proceed? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        sys.exit(0)

    # Create admin
    asyncio.run(create_admin(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    ))


if __name__ == "__main__":
    main()
