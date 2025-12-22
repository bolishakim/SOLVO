"""
Pagination Utilities

Provides pagination helpers for database queries and API responses.
"""

from typing import Any, Generic, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


# ═══════════════════════════════════════════════════════════
# PAGINATION PARAMETERS
# ═══════════════════════════════════════════════════════════

class PaginationParams(BaseModel):
    """
    Pagination parameters from query string.

    Usage:
        @app.get("/items")
        async def get_items(pagination: PaginationParams = Depends()):
            ...
    """
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        """Return limit (alias for per_page)."""
        return self.per_page


def get_pagination_params(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
) -> PaginationParams:
    """
    FastAPI dependency for pagination parameters.

    Usage:
        @app.get("/items")
        async def get_items(pagination: PaginationParams = Depends(get_pagination_params)):
            ...
    """
    return PaginationParams(page=page, per_page=per_page)


# ═══════════════════════════════════════════════════════════
# PAGINATED RESULT
# ═══════════════════════════════════════════════════════════

class PaginatedResult(BaseModel, Generic[T]):
    """
    Container for paginated query results.

    Attributes:
        items: List of items for current page
        total: Total number of items across all pages
        page: Current page number
        per_page: Items per page
        total_pages: Total number of pages
    """
    items: Sequence[T]
    total: int
    page: int
    per_page: int

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.per_page <= 0:
            return 0
        return (self.total + self.per_page - 1) // self.per_page

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1

    def to_response(self, message: str | None = None) -> dict[str, Any]:
        """
        Convert to standardized API response format.

        Returns:
            Dictionary matching the paginated response structure
        """
        response = {
            "success": True,
            "data": list(self.items),
            "pagination": {
                "page": self.page,
                "per_page": self.per_page,
                "total_items": self.total,
                "total_pages": self.total_pages,
            },
        }
        if message:
            response["message"] = message
        return response

    class Config:
        arbitrary_types_allowed = True


# ═══════════════════════════════════════════════════════════
# PAGINATION HELPERS
# ═══════════════════════════════════════════════════════════

async def paginate_query(
    session: AsyncSession,
    query: Select,
    pagination: PaginationParams,
) -> PaginatedResult:
    """
    Execute a paginated query and return results with metadata.

    Args:
        session: SQLAlchemy async session
        query: SQLAlchemy select query
        pagination: Pagination parameters

    Returns:
        PaginatedResult with items and pagination metadata

    Example:
        query = select(User).where(User.is_active == True)
        result = await paginate_query(session, query, pagination)
        return result.to_response()
    """
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated items
    paginated_query = query.offset(pagination.offset).limit(pagination.limit)
    result = await session.execute(paginated_query)
    items = result.scalars().all()

    return PaginatedResult(
        items=items,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
    )


async def paginate_list(
    items: list[T],
    pagination: PaginationParams,
) -> PaginatedResult[T]:
    """
    Paginate an in-memory list.

    Args:
        items: Full list of items
        pagination: Pagination parameters

    Returns:
        PaginatedResult with sliced items and pagination metadata

    Example:
        all_items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = await paginate_list(all_items, PaginationParams(page=2, per_page=3))
        # result.items = [4, 5, 6]
    """
    total = len(items)
    start = pagination.offset
    end = start + pagination.limit
    sliced_items = items[start:end]

    return PaginatedResult(
        items=sliced_items,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
    )
