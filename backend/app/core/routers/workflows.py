"""
Workflows Router

API endpoints for workflow management.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.models import Workflow
from app.core.dependencies import get_current_active_user, ActiveUser
from app.shared.responses import success_response


router = APIRouter()


# ═══════════════════════════════════════════════════════════
# LIST WORKFLOWS
# ═══════════════════════════════════════════════════════════


@router.get(
    "",
    summary="List all workflows",
    response_description="List of available workflows",
)
async def list_workflows(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: ActiveUser,
    active_only: bool = True,
) -> dict[str, Any]:
    """
    Get a list of all available workflows.

    **Query Parameters:**
    - **active_only**: If true (default), only return active workflows

    **Returns:**
    - List of workflows with their details
    """
    query = select(Workflow).order_by(Workflow.workflow_name)

    if active_only:
        query = query.where(Workflow.is_active == True)

    result = await db.execute(query)
    workflows = result.scalars().all()

    return success_response(
        data=[
            {
                "workflow_id": w.workflow_id,
                "workflow_name": w.workflow_name,
                "workflow_code": w.workflow_code,
                "description": w.description,
                "is_active": w.is_active,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            }
            for w in workflows
        ],
        message=f"Found {len(workflows)} workflow(s)",
    )


@router.get(
    "/{workflow_code}",
    summary="Get workflow by code",
    response_description="Workflow details",
)
async def get_workflow(
    workflow_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: ActiveUser,
) -> dict[str, Any]:
    """
    Get details of a specific workflow by its code.

    **Path Parameters:**
    - **workflow_code**: The unique workflow code (e.g., 'landfill_mgmt')

    **Returns:**
    - Workflow details
    """
    result = await db.execute(
        select(Workflow).where(Workflow.workflow_code == workflow_code)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        from app.shared.exceptions import NotFoundException
        raise NotFoundException(entity="Workflow", identifier=workflow_code)

    return success_response(
        data={
            "workflow_id": workflow.workflow_id,
            "workflow_name": workflow.workflow_name,
            "workflow_code": workflow.workflow_code,
            "description": workflow.description,
            "is_active": workflow.is_active,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
        },
        message="Workflow retrieved successfully",
    )
