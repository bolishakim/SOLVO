"""
Role Service

Business logic for role management operations.
"""

from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import User, Role, UserRole
from app.shared.exceptions import (
    NotFoundException,
    AlreadyExistsException,
    ValidationException,
)


class RoleService:
    """Service class for role management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ═══════════════════════════════════════════════════════════
    # ROLE QUERIES
    # ═══════════════════════════════════════════════════════════

    async def get_all_roles(self) -> list[Role]:
        """
        Get all available roles.

        Returns:
            List of Role objects
        """
        query = select(Role).order_by(Role.role_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_role_by_id(self, role_id: int) -> Role | None:
        """
        Get role by ID.

        Args:
            role_id: Role ID

        Returns:
            Role if found, None otherwise
        """
        query = select(Role).where(Role.role_id == role_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_role_by_code(self, role_code: str) -> Role | None:
        """
        Get role by code.

        Args:
            role_code: Role code (e.g., 'admin', 'standard_user')

        Returns:
            Role if found, None otherwise
        """
        query = select(Role).where(Role.role_code == role_code)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ═══════════════════════════════════════════════════════════
    # USER ROLE QUERIES
    # ═══════════════════════════════════════════════════════════

    async def get_user_roles(self, user_id: int) -> list[Role]:
        """
        Get all roles assigned to a user.

        Args:
            user_id: User ID

        Returns:
            List of Role objects
        """
        query = (
            select(Role)
            .join(UserRole, UserRole.role_id == Role.role_id)
            .where(UserRole.user_id == user_id)
            .order_by(Role.role_id)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_role_codes(self, user_id: int) -> list[str]:
        """
        Get list of role codes for a user.

        Args:
            user_id: User ID

        Returns:
            List of role codes
        """
        roles = await self.get_user_roles(user_id)
        return [role.role_code for role in roles]

    async def has_role(self, user_id: int, role_code: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            user_id: User ID
            role_code: Role code to check

        Returns:
            True if user has the role
        """
        query = (
            select(func.count())
            .select_from(UserRole)
            .join(Role, Role.role_id == UserRole.role_id)
            .where(UserRole.user_id == user_id, Role.role_code == role_code)
        )
        result = await self.db.execute(query)
        return result.scalar() > 0

    async def is_admin(self, user_id: int) -> bool:
        """Check if user has admin role."""
        return await self.has_role(user_id, "admin")

    # ═══════════════════════════════════════════════════════════
    # ROLE ASSIGNMENT
    # ═══════════════════════════════════════════════════════════

    async def assign_role(
        self,
        user_id: int,
        role_id: int,
        assigned_by: int | None = None,
    ) -> UserRole:
        """
        Assign a role to a user.

        Args:
            user_id: User ID to assign role to
            role_id: Role ID to assign
            assigned_by: User ID of admin assigning the role

        Returns:
            UserRole association object

        Raises:
            NotFoundException: If user or role not found
            AlreadyExistsException: If user already has the role
        """
        # Verify role exists
        role = await self.get_role_by_id(role_id)
        if not role:
            raise NotFoundException(message="Role not found")

        # Check if already assigned
        existing = await self._get_user_role(user_id, role_id)
        if existing:
            raise AlreadyExistsException(
                message=f"User already has role '{role.role_name}'"
            )

        # Create assignment
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
        )

        self.db.add(user_role)
        await self.db.commit()
        await self.db.refresh(user_role)

        return user_role

    async def assign_role_by_code(
        self,
        user_id: int,
        role_code: str,
        assigned_by: int | None = None,
    ) -> UserRole:
        """
        Assign a role to a user by role code.

        Args:
            user_id: User ID to assign role to
            role_code: Role code to assign
            assigned_by: User ID of admin assigning the role

        Returns:
            UserRole association object

        Raises:
            NotFoundException: If role not found
            AlreadyExistsException: If user already has the role
        """
        role = await self.get_role_by_code(role_code)
        if not role:
            raise NotFoundException(message=f"Role '{role_code}' not found")

        return await self.assign_role(user_id, role.role_id, assigned_by)

    async def remove_role(
        self,
        user_id: int,
        role_id: int,
    ) -> bool:
        """
        Remove a role from a user.

        Args:
            user_id: User ID
            role_id: Role ID to remove

        Returns:
            True if role was removed

        Raises:
            NotFoundException: If user doesn't have the role
            ValidationException: If trying to remove last role
        """
        # Get the assignment
        user_role = await self._get_user_role(user_id, role_id)
        if not user_role:
            raise NotFoundException(message="User does not have this role")

        # Check if this is the last role
        role_count = await self._count_user_roles(user_id)
        if role_count <= 1:
            raise ValidationException(
                message="Cannot remove last role. User must have at least one role."
            )

        # Remove the role
        await self.db.delete(user_role)
        await self.db.commit()

        return True

    async def remove_role_by_code(
        self,
        user_id: int,
        role_code: str,
    ) -> bool:
        """
        Remove a role from a user by role code.

        Args:
            user_id: User ID
            role_code: Role code to remove

        Returns:
            True if role was removed

        Raises:
            NotFoundException: If role not found or user doesn't have it
            ValidationException: If trying to remove last role
        """
        role = await self.get_role_by_code(role_code)
        if not role:
            raise NotFoundException(message=f"Role '{role_code}' not found")

        return await self.remove_role(user_id, role.role_id)

    async def set_user_roles(
        self,
        user_id: int,
        role_ids: list[int],
        assigned_by: int | None = None,
    ) -> list[Role]:
        """
        Set the complete list of roles for a user.

        This replaces all existing roles with the new list.

        Args:
            user_id: User ID
            role_ids: List of role IDs to assign
            assigned_by: User ID of admin making the change

        Returns:
            List of assigned Role objects

        Raises:
            ValidationException: If no roles provided or invalid role IDs
            NotFoundException: If any role not found
        """
        if not role_ids:
            raise ValidationException(
                message="User must have at least one role"
            )

        # Verify all roles exist
        roles = []
        for role_id in role_ids:
            role = await self.get_role_by_id(role_id)
            if not role:
                raise NotFoundException(message=f"Role with ID {role_id} not found")
            roles.append(role)

        # Remove all existing roles
        await self._remove_all_user_roles(user_id)

        # Assign new roles
        for role in roles:
            user_role = UserRole(
                user_id=user_id,
                role_id=role.role_id,
                assigned_by=assigned_by,
            )
            self.db.add(user_role)

        await self.db.commit()

        return roles

    # ═══════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════

    async def get_role_user_count(self, role_id: int) -> int:
        """
        Get the number of users with a specific role.

        Args:
            role_id: Role ID

        Returns:
            Number of users with the role
        """
        query = (
            select(func.count())
            .select_from(UserRole)
            .where(UserRole.role_id == role_id)
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_users_with_role(
        self,
        role_code: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[User]:
        """
        Get all users with a specific role.

        Args:
            role_code: Role code
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of User objects
        """
        query = (
            select(User)
            .join(UserRole, UserRole.user_id == User.user_id)
            .join(Role, Role.role_id == UserRole.role_id)
            .where(Role.role_code == role_code)
            .order_by(User.username)
            .offset(offset)
        )

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ═══════════════════════════════════════════════════════════
    # PRIVATE METHODS
    # ═══════════════════════════════════════════════════════════

    async def _get_user_role(self, user_id: int, role_id: int) -> UserRole | None:
        """Get a specific user-role assignment."""
        query = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _count_user_roles(self, user_id: int) -> int:
        """Count the number of roles a user has."""
        query = (
            select(func.count())
            .select_from(UserRole)
            .where(UserRole.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _remove_all_user_roles(self, user_id: int) -> None:
        """Remove all roles from a user."""
        query = select(UserRole).where(UserRole.user_id == user_id)
        result = await self.db.execute(query)
        user_roles = result.scalars().all()

        for user_role in user_roles:
            await self.db.delete(user_role)
