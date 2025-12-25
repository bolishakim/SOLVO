"""
Seed Data Script

Seeds the database with default roles, workflows, and optionally a test admin user.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker, create_schemas
from app.core.models import (
    Role,
    Workflow,
    DEFAULT_ROLES,
    DEFAULT_WORKFLOWS,
)


async def seed_roles(session: AsyncSession) -> None:
    """Seed default roles if they don't exist, or update existing ones."""
    print("\n--- Seeding Roles ---")

    for role_data in DEFAULT_ROLES:
        # Check if role already exists by role_code (stable identifier)
        result = await session.execute(
            select(Role).where(Role.role_code == role_data["role_code"])
        )
        existing_role = result.scalar_one_or_none()

        if existing_role:
            # Update existing role with new values (e.g., translated names/descriptions)
            updated = False
            if existing_role.role_name != role_data["role_name"]:
                existing_role.role_name = role_data["role_name"]
                updated = True
            if existing_role.description != role_data["description"]:
                existing_role.description = role_data["description"]
                updated = True

            if updated:
                print(f"  [UPDATE] Role '{role_data['role_code']}' updated")
            else:
                print(f"  [SKIP] Role '{role_data['role_code']}' already up to date")
        else:
            role = Role(**role_data)
            session.add(role)
            print(f"  [ADD] Role '{role_data['role_name']}' created")

    await session.commit()
    print("Roles seeding complete!")


async def seed_workflows(session: AsyncSession) -> None:
    """Seed default workflows if they don't exist."""
    print("\n--- Seeding Workflows ---")

    for workflow_data in DEFAULT_WORKFLOWS:
        # Check if workflow already exists
        result = await session.execute(
            select(Workflow).where(Workflow.workflow_code == workflow_data["workflow_code"])
        )
        existing_workflow = result.scalar_one_or_none()

        if existing_workflow:
            print(f"  [SKIP] Workflow '{workflow_data['workflow_code']}' already exists")
        else:
            workflow = Workflow(**workflow_data)
            session.add(workflow)
            print(f"  [ADD] Workflow '{workflow_data['workflow_code']}' created")

    await session.commit()
    print("Workflows seeding complete!")


async def verify_seeded_data(session: AsyncSession) -> None:
    """Verify and display seeded data."""
    print("\n--- Verification ---")

    # Verify roles
    result = await session.execute(select(Role).order_by(Role.role_id))
    roles = result.scalars().all()
    print(f"\nRoles ({len(roles)}):")
    for role in roles:
        print(f"  - {role.role_id}: {role.role_name}")

    # Verify workflows
    result = await session.execute(select(Workflow).order_by(Workflow.workflow_id))
    workflows = result.scalars().all()
    print(f"\nWorkflows ({len(workflows)}):")
    for workflow in workflows:
        print(f"  - {workflow.workflow_id}: {workflow.workflow_code} ({workflow.workflow_name})")


async def main() -> None:
    """Main function to run all seed operations."""
    print("=" * 60)
    print("LANDFILL MANAGEMENT SYSTEM - DATABASE SEEDING")
    print("=" * 60)

    # Ensure schemas exist
    print("\nEnsuring schemas exist...")
    await create_schemas()
    print("Schemas verified!")

    async with async_session_maker() as session:
        try:
            await seed_roles(session)
            await seed_workflows(session)
            await verify_seeded_data(session)

            print("\n" + "=" * 60)
            print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
            print("=" * 60)
        except Exception as e:
            print(f"\n[ERROR] Seeding failed: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
