from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GolfClub
from app.schemas.golf_club import GolfClubCreate, GolfClubUpdate


class GolfClubService:
    async def list(self, session: AsyncSession) -> list[GolfClub]:
        r = await session.execute(select(GolfClub).order_by(GolfClub.id))
        return list(r.scalars().all())

    async def get(self, session: AsyncSession, club_id: int) -> GolfClub | None:
        return await session.get(GolfClub, club_id)

    async def create(self, session: AsyncSession, data: GolfClubCreate) -> GolfClub:
        c = GolfClub(
            catalog_id=data.catalog_id,
            name=data.name,
            club_type=data.club_type,
            loft_deg=data.loft_deg,
            difficulty=data.difficulty,
            max_distance_m=data.max_distance_m,
            avg_distance_m=data.avg_distance_m,
            player_levels=data.player_levels,
        )
        session.add(c)
        await session.flush()
        await session.refresh(c)
        return c

    async def update(
        self, session: AsyncSession, club_id: int, data: GolfClubUpdate
    ) -> GolfClub | None:
        c = await self.get(session, club_id)
        if not c:
            return None
        if data.name is not None:
            c.name = data.name
        if data.club_type is not None:
            c.club_type = data.club_type
        if data.loft_deg is not None:
            c.loft_deg = data.loft_deg
        if data.difficulty is not None:
            c.difficulty = data.difficulty
        if data.max_distance_m is not None:
            c.max_distance_m = data.max_distance_m
        if data.avg_distance_m is not None:
            c.avg_distance_m = data.avg_distance_m
        if data.player_levels is not None:
            c.player_levels = data.player_levels
        await session.flush()
        await session.refresh(c)
        return c


golf_club_service = GolfClubService()
