from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Shot
from app.schemas.shot import ShotCreate, ShotUpdate


class ShotService:
    async def list(
        self,
        session: AsyncSession,
        round_id: int | None = None,
        hole_id: int | None = None,
    ) -> list[Shot]:
        q = select(Shot).order_by(Shot.round_id, Shot.hole_id, Shot.shot_at, Shot.id)
        if round_id is not None:
            q = q.where(Shot.round_id == round_id)
        if hole_id is not None:
            q = q.where(Shot.hole_id == hole_id)
        r = await session.execute(q)
        return list(r.scalars().all())

    async def get(self, session: AsyncSession, shot_id: int) -> Shot | None:
        return await session.get(Shot, shot_id)

    async def create(self, session: AsyncSession, data: ShotCreate) -> Shot:
        s = Shot(
            round_id=data.round_id,
            hole_id=data.hole_id,
            x=data.x,
            y=data.y,
            club=data.club,
            distance=data.distance,
        )
        session.add(s)
        await session.flush()
        await session.refresh(s)
        return s

    async def update(
        self, session: AsyncSession, shot_id: int, data: ShotUpdate
    ) -> Shot | None:
        s = await self.get(session, shot_id)
        if not s:
            return None
        for field in ("x", "y", "club", "distance", "shot_at"):
            val = getattr(data, field)
            if val is not None:
                setattr(s, field, val)
        await session.flush()
        await session.refresh(s)
        return s

    async def delete(self, session: AsyncSession, shot_id: int) -> bool:
        s = await self.get(session, shot_id)
        if not s:
            return False
        await session.delete(s)
        return True


shot_service = ShotService()
