"""
User Service

Business logic for user operations.
"""

from datetime import datetime

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import User, Role, UserRole
from app.shared.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)


class UserService:
    """Service class for user operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ═══════════════════════════════════════════════════════════
    # READ OPERATIONS
    # ═══════════════════════════════════════════════════════════

    async def get_by_id(self, user_id: int) -> User | None:
        """
        Get user by ID.

        Args:
            user_id: User ID (integer)

        Returns:
            User if found, None otherwise
        """
        query = (
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """
        Get user by email address.

        Args:
            email: Email address

        Returns:
            User if found, None otherwise
        """
        query = (
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.email == email.lower())
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            User if found, None otherwise
        """
        query = (
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.username == username.lower())
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username_or_email(self, identifier: str) -> User | None:
        """
        Get user by username or email.

        Args:
            identifier: Username or email

        Returns:
            User if found, None otherwise
        """
        identifier_lower = identifier.lower()
        query = (
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(
                or_(
                    User.username == identifier_lower,
                    User.email == identifier_lower,
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists with given email."""
        query = select(User.user_id).where(User.email == email.lower())
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists with given username."""
        query = select(User.user_id).where(User.username == username.lower())
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    # ═══════════════════════════════════════════════════════════
    # CREATE OPERATIONS
    # ═══════════════════════════════════════════════════════════

    async def create(
        self,
        username: str,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        phone_number: str | None = None,
    ) -> User:
        """
        Create a new user.

        Args:
            username: Unique username
            email: Unique email address
            password_hash: Hashed password
            first_name: First name
            last_name: Last name
            phone_number: Optional phone number

        Returns:
            Created User object

        Raises:
            AlreadyExistsException: If username or email already exists
        """
        # Check for existing username
        if await self.exists_by_username(username):
            raise AlreadyExistsException(
                message="Username already taken",
                details={"field": "username"},
            )

        # Check for existing email
        if await self.exists_by_email(email):
            raise AlreadyExistsException(
                message="Email already registered",
                details={"field": "email"},
            )

        # Create user
        user = User(
            username=username.lower(),
            email=email.lower(),
            password_hash=password_hash,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            phone_number=phone_number,
            is_active=True,
            is_verified=False,  # Require email verification
            two_factor_enabled=False,
        )

        self.db.add(user)
        await self.db.flush()

        # Assign default role (Standard User)
        await self._assign_default_role(user.user_id)

        await self.db.commit()
        await self.db.refresh(user)

        # Reload with roles
        return await self.get_by_id(user.user_id)

    async def _assign_default_role(self, user_id: int) -> None:
        """Assign the default 'Standard User' role to a new user."""
        # Get Standard User role
        query = select(Role).where(Role.role_code == "standard_user")
        result = await self.db.execute(query)
        role = result.scalar_one_or_none()

        if role:
            user_role = UserRole(
                user_id=user_id,
                role_id=role.role_id,
            )
            self.db.add(user_role)

    # ═══════════════════════════════════════════════════════════
    # UPDATE OPERATIONS
    # ═══════════════════════════════════════════════════════════

    async def update(
        self,
        user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        phone_number: str | None = None,
    ) -> User:
        """
        Update user profile.

        Args:
            user_id: User ID (integer)
            first_name: New first name (optional)
            last_name: New last name (optional)
            phone_number: New phone number (optional)

        Returns:
            Updated User object

        Raises:
            NotFoundException: If user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundException(message="User not found")

        if first_name is not None:
            user.first_name = first_name.strip()
        if last_name is not None:
            user.last_name = last_name.strip()
        if phone_number is not None:
            user.phone_number = phone_number

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password(self, user_id: int, new_password_hash: str) -> None:
        """
        Update user password.

        Args:
            user_id: User ID (integer)
            new_password_hash: New hashed password

        Raises:
            NotFoundException: If user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundException(message="User not found")

        user.password_hash = new_password_hash
        await self.db.commit()

    async def update_last_login(self, user_id: int) -> None:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID (integer)
        """
        query = select(User).where(User.user_id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if user:
            user.last_login_at = datetime.utcnow()
            await self.db.commit()

    async def set_active_status(self, user_id: int, is_active: bool) -> User:
        """
        Set user active status.

        Args:
            user_id: User ID (integer)
            is_active: Active status

        Returns:
            Updated User object

        Raises:
            NotFoundException: If user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundException(message="User not found")

        user.is_active = is_active
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def set_verified(self, user_id: int, is_verified: bool = True) -> None:
        """
        Set user verification status.

        Args:
            user_id: User ID (integer)
            is_verified: Verification status
        """
        user = await self.get_by_id(user_id)
        if user:
            user.is_verified = is_verified
            await self.db.commit()

    # ═══════════════════════════════════════════════════════════
    # ROLE OPERATIONS
    # ═══════════════════════════════════════════════════════════

    def get_user_roles(self, user: User) -> list[str]:
        """
        Get list of role names for a user.

        Args:
            user: User object with loaded roles

        Returns:
            List of role names
        """
        return [ur.role.role_name for ur in user.user_roles if ur.role]

    def get_user_role_codes(self, user: User) -> list[str]:
        """
        Get list of role codes for a user.

        Args:
            user: User object with loaded roles

        Returns:
            List of role codes
        """
        return [ur.role.role_code for ur in user.user_roles if ur.role]

    def has_role(self, user: User, role_code: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            user: User object with loaded roles
            role_code: Role code to check

        Returns:
            True if user has the role
        """
        return role_code in self.get_user_role_codes(user)

    def is_admin(self, user: User) -> bool:
        """Check if user has admin role."""
        return self.has_role(user, "admin")
