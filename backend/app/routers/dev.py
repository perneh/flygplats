"""Development and integration-test endpoints (not for untrusted production exposure)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.seed_init_data import seed_golf_clubs_if_empty_session, seed_init_courses_if_empty_session
from app.services.factory_service import factory_service

router = APIRouter()


@router.post(
    "/factory-default",
    status_code=status.HTTP_200_OK,
    summary="Wipe domain data and reload bundled init_data (courses + golf clubs)",
)
async def factory_default(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """
    Remove all players, rounds, shots, holes, courses, and golf clubs, then insert rows from
    ``init_data/golf_courses_25.json`` and ``init_data/golf_clubs.json`` when those tables are empty
    (they are after the delete). Same catalog as Docker/CLI seed.

    Intended for automated tests and local dev. Disable or protect in production deployments.
    """
    await factory_service.clear_all_data(session)
    await seed_init_courses_if_empty_session(session)
    await seed_golf_clubs_if_empty_session(session)
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
