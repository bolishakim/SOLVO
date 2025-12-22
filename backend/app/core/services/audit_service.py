"""
Audit Service

Business logic for audit logging operations.
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import User
from app.core.models.audit_log import AuditLog, ActionType, EntityType
from app.core.schemas.audit import AuditLogFilter, AuditLogResponse


class AuditService:
    """Service class for audit logging operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ═══════════════════════════════════════════════════════════
    # LOGGING METHODS
    # ═══════════════════════════════════════════════════════════

    async def log_action(
        self,
        action_type: ActionType | str,
        user_id: int | None = None,
        entity_type: EntityType | str | None = None,
        entity_id: str | int | None = None,
        workflow_schema: str | None = None,
        changes: dict | None = None,
        description: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        """
        Log an action to the audit trail.

        Args:
            action_type: Type of action (use ActionType enum)
            user_id: ID of user performing action
            entity_type: Type of entity affected (use EntityType enum)
            entity_id: ID of affected entity
            workflow_schema: Schema where action occurred (None for core_app)
            changes: Dict with 'old' and 'new' values
            description: Human-readable description
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request ID for tracing

        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog.create_log(
            action_type=action_type,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            workflow_schema=workflow_schema,
            changes=changes,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

        self.db.add(audit_log)
        await self.db.flush()

        return audit_log

    async def log_login(
        self,
        user_id: int,
        success: bool = True,
        ip_address: str | None = None,
        user_agent: str | None = None,
        failure_reason: str | None = None,
    ) -> AuditLog:
        """Log a login attempt."""
        action_type = ActionType.LOGIN if success else ActionType.LOGIN_FAILED
        description = "User logged in successfully" if success else f"Login failed: {failure_reason or 'Invalid credentials'}"

        return await self.log_action(
            action_type=action_type,
            user_id=user_id if success else None,
            entity_type=EntityType.USER,
            entity_id=user_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            changes={"failed_reason": failure_reason} if not success else None,
        )

    async def log_logout(
        self,
        user_id: int,
        session_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a logout action."""
        return await self.log_action(
            action_type=ActionType.LOGOUT,
            user_id=user_id,
            entity_type=EntityType.SESSION,
            entity_id=session_id,
            description="User logged out",
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_registration(
        self,
        user_id: int,
        username: str,
        email: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a new user registration."""
        return await self.log_action(
            action_type=ActionType.REGISTER,
            user_id=user_id,
            entity_type=EntityType.USER,
            entity_id=user_id,
            description=f"New user registered: {username}",
            ip_address=ip_address,
            user_agent=user_agent,
            changes={"new": {"username": username, "email": email}},
        )

    async def log_password_change(
        self,
        user_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a password change."""
        return await self.log_action(
            action_type=ActionType.PASSWORD_CHANGE,
            user_id=user_id,
            entity_type=EntityType.USER,
            entity_id=user_id,
            description="User changed password",
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_user_update(
        self,
        user_id: int,
        updated_by: int,
        old_values: dict,
        new_values: dict,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a user profile update."""
        return await self.log_action(
            action_type=ActionType.UPDATE,
            user_id=updated_by,
            entity_type=EntityType.USER,
            entity_id=user_id,
            description=f"User profile updated",
            ip_address=ip_address,
            user_agent=user_agent,
            changes={"old": old_values, "new": new_values},
        )

    async def log_user_deactivate(
        self,
        user_id: int,
        deactivated_by: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a user deactivation."""
        return await self.log_action(
            action_type=ActionType.DELETE,
            user_id=deactivated_by,
            entity_type=EntityType.USER,
            entity_id=user_id,
            description=f"User account deactivated",
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_role_assign(
        self,
        user_id: int,
        role_id: int,
        role_name: str,
        assigned_by: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a role assignment."""
        return await self.log_action(
            action_type=ActionType.ROLE_ASSIGN,
            user_id=assigned_by,
            entity_type=EntityType.ROLE,
            entity_id=role_id,
            description=f"Role '{role_name}' assigned to user {user_id}",
            ip_address=ip_address,
            user_agent=user_agent,
            changes={"new": {"user_id": user_id, "role_id": role_id, "role_name": role_name}},
        )

    async def log_role_remove(
        self,
        user_id: int,
        role_id: int,
        role_name: str,
        removed_by: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a role removal."""
        return await self.log_action(
            action_type=ActionType.ROLE_REMOVE,
            user_id=removed_by,
            entity_type=EntityType.ROLE,
            entity_id=role_id,
            description=f"Role '{role_name}' removed from user {user_id}",
            ip_address=ip_address,
            user_agent=user_agent,
            changes={"old": {"user_id": user_id, "role_id": role_id, "role_name": role_name}},
        )

    async def log_session_revoke(
        self,
        user_id: int,
        session_id: int,
        revoked_by: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log a session revocation."""
        return await self.log_action(
            action_type=ActionType.SESSION_REVOKE,
            user_id=revoked_by,
            entity_type=EntityType.SESSION,
            entity_id=session_id,
            description=f"Session revoked for user {user_id}",
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_all_sessions_revoke(
        self,
        user_id: int,
        revoked_by: int,
        count: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log revocation of all sessions."""
        return await self.log_action(
            action_type=ActionType.SESSION_REVOKE_ALL,
            user_id=revoked_by,
            entity_type=EntityType.SESSION,
            entity_id=user_id,
            description=f"All sessions revoked for user {user_id} ({count} sessions)",
            ip_address=ip_address,
            user_agent=user_agent,
            changes={"sessions_revoked": count},
        )

    async def log_2fa_enable(
        self,
        user_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log 2FA enablement."""
        return await self.log_action(
            action_type=ActionType.TWO_FACTOR_ENABLE,
            user_id=user_id,
            entity_type=EntityType.TWO_FACTOR,
            entity_id=user_id,
            description="Two-factor authentication enabled",
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_2fa_disable(
        self,
        user_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log 2FA disablement."""
        return await self.log_action(
            action_type=ActionType.TWO_FACTOR_DISABLE,
            user_id=user_id,
            entity_type=EntityType.TWO_FACTOR,
            entity_id=user_id,
            description="Two-factor authentication disabled",
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_2fa_verify(
        self,
        user_id: int,
        method: str = "totp",  # "totp" or "backup_code"
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Log 2FA verification during login."""
        return await self.log_action(
            action_type=ActionType.TWO_FACTOR_VERIFY,
            user_id=user_id,
            entity_type=EntityType.TWO_FACTOR,
            entity_id=user_id,
            description=f"Two-factor authentication verified using {method}",
            ip_address=ip_address,
            user_agent=user_agent,
            changes={"method": method},
        )

    # ═══════════════════════════════════════════════════════════
    # QUERY METHODS
    # ═══════════════════════════════════════════════════════════

    async def get_audit_log(self, log_id: int) -> AuditLog | None:
        """Get a specific audit log by ID."""
        result = await self.db.execute(
            select(AuditLog).where(AuditLog.log_id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_audit_logs(
        self,
        filters: AuditLogFilter | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """
        Get audit logs with optional filters and pagination.

        Args:
            filters: Optional filter criteria
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (logs, total_count)
        """
        # Build base query
        query = select(AuditLog).order_by(AuditLog.created_at.desc())

        # Apply filters
        if filters:
            conditions = []

            if filters.user_id is not None:
                conditions.append(AuditLog.user_id == filters.user_id)

            if filters.action_type:
                conditions.append(AuditLog.action_type == filters.action_type)

            if filters.entity_type:
                conditions.append(AuditLog.entity_type == filters.entity_type)

            if filters.entity_id:
                conditions.append(AuditLog.entity_id == filters.entity_id)

            if filters.workflow_schema:
                if filters.workflow_schema.lower() == "core_app":
                    conditions.append(AuditLog.workflow_schema.is_(None))
                else:
                    conditions.append(AuditLog.workflow_schema == filters.workflow_schema)

            if filters.from_date:
                conditions.append(AuditLog.created_at >= filters.from_date)

            if filters.to_date:
                conditions.append(AuditLog.created_at <= filters.to_date)

            if filters.ip_address:
                conditions.append(AuditLog.ip_address == filters.ip_address)

            if conditions:
                query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        return logs, total

    async def get_user_audit_history(
        self,
        user_id: int,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Get audit history for a specific user (as performer)."""
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_entity_audit_history(
        self,
        entity_type: EntityType | str,
        entity_id: str | int,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Get audit history for a specific entity."""
        entity_type_str = entity_type.value if isinstance(entity_type, EntityType) else entity_type
        entity_id_str = str(entity_id)

        result = await self.db.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.entity_type == entity_type_str,
                    AuditLog.entity_id == entity_id_str,
                )
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # ═══════════════════════════════════════════════════════════
    # STATISTICS METHODS
    # ═══════════════════════════════════════════════════════════

    async def get_stats(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict:
        """
        Get audit log statistics.

        Args:
            from_date: Start date for stats
            to_date: End date for stats

        Returns:
            Dictionary with various statistics
        """
        # Build base conditions
        conditions = []
        if from_date:
            conditions.append(AuditLog.created_at >= from_date)
        if to_date:
            conditions.append(AuditLog.created_at <= to_date)

        # Total count
        total_query = select(func.count()).select_from(AuditLog)
        if conditions:
            total_query = total_query.where(and_(*conditions))
        total_result = await self.db.execute(total_query)
        total_count = total_result.scalar() or 0

        # Count by action type
        action_count_query = (
            select(AuditLog.action_type, func.count().label("count"))
            .group_by(AuditLog.action_type)
            .order_by(func.count().desc())
        )
        if conditions:
            action_count_query = action_count_query.where(and_(*conditions))
        action_result = await self.db.execute(action_count_query)
        by_action_type = {row.action_type: row.count for row in action_result}

        # Count by entity type
        entity_count_query = (
            select(AuditLog.entity_type, func.count().label("count"))
            .where(AuditLog.entity_type.isnot(None))
            .group_by(AuditLog.entity_type)
            .order_by(func.count().desc())
        )
        if conditions:
            entity_count_query = entity_count_query.where(and_(*conditions))
        entity_result = await self.db.execute(entity_count_query)
        by_entity_type = {row.entity_type: row.count for row in entity_result}

        # Recent activity (last 24 hours)
        day_ago = datetime.utcnow() - timedelta(days=1)
        recent_query = (
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.created_at >= day_ago)
        )
        recent_result = await self.db.execute(recent_query)
        recent_count = recent_result.scalar() or 0

        # Failed logins (last 24 hours)
        failed_login_query = (
            select(func.count())
            .select_from(AuditLog)
            .where(
                and_(
                    AuditLog.action_type == ActionType.LOGIN_FAILED.value,
                    AuditLog.created_at >= day_ago,
                )
            )
        )
        failed_login_result = await self.db.execute(failed_login_query)
        failed_logins_24h = failed_login_result.scalar() or 0

        return {
            "total_logs": total_count,
            "by_action_type": by_action_type,
            "by_entity_type": by_entity_type,
            "recent_24h": recent_count,
            "failed_logins_24h": failed_logins_24h,
        }

    async def get_login_history(
        self,
        user_id: int | None = None,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Get login/logout history."""
        query = (
            select(AuditLog)
            .where(
                AuditLog.action_type.in_([
                    ActionType.LOGIN.value,
                    ActionType.LOGOUT.value,
                    ActionType.LOGIN_FAILED.value,
                ])
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )

        if user_id:
            query = query.where(
                or_(
                    AuditLog.user_id == user_id,
                    AuditLog.entity_id == str(user_id),
                )
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ═══════════════════════════════════════════════════════════
    # ENRICHMENT METHODS
    # ═══════════════════════════════════════════════════════════

    async def enrich_log_with_username(self, log: AuditLog) -> dict:
        """
        Enrich an audit log with username for display.

        Returns a dictionary representation with username included.
        """
        username = None
        if log.user_id:
            user_result = await self.db.execute(
                select(User.username).where(User.user_id == log.user_id)
            )
            username = user_result.scalar_one_or_none()

        return {
            "log_id": log.log_id,
            "user_id": log.user_id,
            "username": username,
            "workflow_schema": log.workflow_schema,
            "action_type": log.action_type,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "changes": log.changes,
            "description": log.description,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "request_id": log.request_id,
            "created_at": log.created_at,
        }

    async def enrich_logs_with_usernames(self, logs: list[AuditLog]) -> list[dict]:
        """Enrich multiple audit logs with usernames."""
        if not logs:
            return []

        # Get unique user IDs
        user_ids = {log.user_id for log in logs if log.user_id}

        # Fetch usernames in bulk
        usernames = {}
        if user_ids:
            result = await self.db.execute(
                select(User.user_id, User.username).where(User.user_id.in_(user_ids))
            )
            usernames = {row.user_id: row.username for row in result}

        # Build enriched logs
        return [
            {
                "log_id": log.log_id,
                "user_id": log.user_id,
                "username": usernames.get(log.user_id),
                "workflow_schema": log.workflow_schema,
                "action_type": log.action_type,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "changes": log.changes,
                "description": log.description,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "request_id": log.request_id,
                "created_at": log.created_at,
            }
            for log in logs
        ]

    # ═══════════════════════════════════════════════════════════
    # CLEANUP METHODS
    # ═══════════════════════════════════════════════════════════

    async def cleanup_old_logs(self, days: int = 365) -> int:
        """
        Delete audit logs older than specified days.

        Args:
            days: Number of days to keep logs

        Returns:
            Number of deleted logs
        """
        from sqlalchemy import delete

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Count before delete
        count_query = (
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.created_at < cutoff_date)
        )
        count_result = await self.db.execute(count_query)
        count = count_result.scalar() or 0

        if count > 0:
            delete_query = delete(AuditLog).where(AuditLog.created_at < cutoff_date)
            await self.db.execute(delete_query)

        return count
