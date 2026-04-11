"""Development and integration-test endpoints (not for untrusted production exposure)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.seed_init_data import seed_golf_clubs_if_empty_session
from app.services.factory_service import factory_service

router = APIRouter()


@router.post(
    "/factory-default",
    status_code=status.HTTP_200_OK,
    summary="Delete all players, courses, holes, rounds, and shots",
)
async def factory_default(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """
    Reset the database to an empty domain state.

    Intended for automated tests and local dev. Disable or protect in production deployments.
    """
    await factory_service.clear_all_data(session)
    await session.commit()
    return {"status": "ok"}


@router.post(
    "/seed-golf-clubs",
    status_code=status.HTTP_200_OK,
    summary="Load bundled golf_clubs.json when the table is empty (tests and local dev)",
)
async def seed_golf_clubs(session: AsyncSession = Depends(get_session)) -> dict[str, str | bool]:
    """Same logic as ``python -m app.seed_init_data`` golf-club step; uses the request session."""
    ran = await seed_golf_clubs_if_empty_session(session)
    await session.commit()
    return {"status": "ok", "seeded": ran}
