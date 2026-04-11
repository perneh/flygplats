"""Test/dev helpers: wipe all domain data in a safe order."""

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Course, GolfClub, Hole, Player, Round, Shot


class FactoryService:
    async def clear_all_data(self, session: AsyncSession) -> None:
        """Remove every row from all tables (shots → rounds → holes → courses → players → golf_clubs)."""
        await session.execute(delete(Shot))
        await session.execute(delete(Round))
        await session.execute(delete(Hole))
        await session.execute(delete(Course))
        await session.execute(delete(Player))
        await session.execute(delete(GolfClub))


factory_service = FactoryService()
