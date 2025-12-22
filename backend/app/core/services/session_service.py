"""
Session Service

Business logic for session management.
"""

from datetime import datetime, timedelta

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.models import UserSession
from app.shared.exceptions import NotFoundException
from app.shared.security import generate_session_token


class SessionService:
    """Service class for session management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ═══════════════════════════════════════════════════════════
    # CREATE OPERATIONS
    # ═══════════════════════════════════════════════════════════

    async def create_session(
        self,
        user_id: int,
        refresh_token_jti: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserSession:
        """
        Create a new session for a user.

        Args:
            user_id: User ID
            refresh_token_jti: The JTI (unique ID) of the refresh token
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            Created UserSession object
        """
        # Generate a unique session token
        session_token = generate_session_token()

        # Calculate expiration (same as refresh token)
        expires_at = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            refresh_token=refresh_token_jti,
            ip_address=ip_address,
            user_agent=self._truncate_user_agent(user_agent),
            expires_at=expires_at,
            is_revoked=False,
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    def _truncate_user_agent(self, user_agent: str | None) -> str | None:
        """Truncate user agent to fit in database column."""
        if user_agent and len(user_agent) > 500:
            return user_agent[:497] + "..."
        return user_agent

    # ═══════════════════════════════════════════════════════════
    # READ OPERATIONS
    # ═══════════════════════════════════════════════════════════

    async def get_by_id(self, session_id: int) -> UserSession | None:
        """
        Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            UserSession if found, None otherwise
        """
        query = select(UserSession).where(UserSession.session_id == session_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_token(self, session_token: str) -> UserSession | None:
        """
        Get session by session token.

        Args:
            session_token: Unique session token

        Returns:
            UserSession if found, None otherwise
        """
        query = select(UserSession).where(UserSession.session_token == session_token)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_refresh_token(self, refresh_token_jti: str) -> UserSession | None:
        """
        Get session by refresh token JTI.

        Args:
            refresh_token_jti: Refresh token JTI

        Returns:
            UserSession if found, None otherwise
        """
        query = select(UserSession).where(UserSession.refresh_token == refresh_token_jti)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_sessions(
        self,
        user_id: int,
        include_expired: bool = False,
    ) -> list[UserSession]:
        """
        Get all sessions for a user.

        Args:
            user_id: User ID
            include_expired: Include expired/revoked sessions

        Returns:
            List of UserSession objects
        """
        query = select(UserSession).where(UserSession.user_id == user_id)

        if not include_expired:
            query = query.where(
                and_(
                    UserSession.is_revoked == False,
                    UserSession.expires_at > datetime.utcnow(),
                )
            )

        query = query.order_by(UserSession.last_activity_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_session_count(self, user_id: int) -> int:
        """
        Get count of active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            Number of active sessions
        """
        sessions = await self.get_user_sessions(user_id, include_expired=False)
        return len(sessions)

    # ═══════════════════════════════════════════════════════════
    # VALIDATION OPERATIONS
    # ═══════════════════════════════════════════════════════════

    async def validate_session(self, refresh_token_jti: str) -> UserSession | None:
        """
        Validate a session by refresh token JTI.

        Args:
            refresh_token_jti: Refresh token JTI

        Returns:
            Valid UserSession if found and valid, None otherwise
        """
        session = await self.get_by_refresh_token(refresh_token_jti)

        if session is None:
            return None

        if not session.is_valid:
            return None

        return session

    async def update_activity(self, session_id: int) -> None:
        """
        Update the last activity timestamp for a session.

        Args:
            session_id: Session ID
        """
        session = await self.get_by_id(session_id)
        if session:
            session.last_activity_at = datetime.utcnow()
            await self.db.commit()

    # ═══════════════════════════════════════════════════════════
    # REVOCATION OPERATIONS
    # ═══════════════════════════════════════════════════════════

    async def revoke_session(self, session_id: int, user_id: int) -> bool:
        """
        Revoke a specific session.

        Args:
            session_id: Session ID to revoke
            user_id: User ID (for authorization check)

        Returns:
            True if session was revoked, False if not found

        Raises:
            NotFoundException: If session not found or doesn't belong to user
        """
        session = await self.get_by_id(session_id)

        if session is None:
            raise NotFoundException(message="Session not found")

        if session.user_id != user_id:
            raise NotFoundException(message="Session not found")

        if session.is_revoked:
            return False  # Already revoked

        session.is_revoked = True
        session.revoked_at = datetime.utcnow()
        await self.db.commit()

        return True

    async def revoke_session_by_refresh_token(self, refresh_token_jti: str) -> bool:
        """
        Revoke a session by refresh token JTI.

        Args:
            refresh_token_jti: Refresh token JTI

        Returns:
            True if session was revoked, False if not found
        """
        session = await self.get_by_refresh_token(refresh_token_jti)

        if session is None:
            return False

        if session.is_revoked:
            return False

        session.is_revoked = True
        session.revoked_at = datetime.utcnow()
        await self.db.commit()

        return True

    async def revoke_all_sessions(
        self,
        user_id: int,
        except_session_id: int | None = None,
    ) -> int:
        """
        Revoke all sessions for a user.

        Args:
            user_id: User ID
            except_session_id: Optional session ID to exclude (current session)

        Returns:
            Number of sessions revoked
        """
        sessions = await self.get_user_sessions(user_id, include_expired=False)
        revoked_count = 0

        for session in sessions:
            if except_session_id and session.session_id == except_session_id:
                continue

            if not session.is_revoked:
                session.is_revoked = True
                session.revoked_at = datetime.utcnow()
                revoked_count += 1

        await self.db.commit()
        return revoked_count

    # ═══════════════════════════════════════════════════════════
    # CLEANUP OPERATIONS
    # ═══════════════════════════════════════════════════════════

    async def cleanup_expired_sessions(self, older_than_days: int = 30) -> int:
        """
        Delete expired and revoked sessions older than specified days.

        Args:
            older_than_days: Delete sessions older than this many days

        Returns:
            Number of sessions deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

        # Delete old expired or revoked sessions
        query = delete(UserSession).where(
            and_(
                UserSession.expires_at < cutoff_date,
            )
        )

        result = await self.db.execute(query)
        await self.db.commit()

        return result.rowcount
