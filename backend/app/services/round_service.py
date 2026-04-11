from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Round
from app.schemas.round import RoundCreate, RoundUpdate


class RoundService:
    async def list(
        self,
        session: AsyncSession,
        player_id: int | None = None,
        course_id: int | None = None,
    ) -> list[Round]:
        q = select(Round).order_by(Round.id)
        if player_id is not None:
            q = q.where(Round.player_id == player_id)
        if course_id is not None:
            q = q.where(Round.course_id == course_id)
        r = await session.execute(q)
        return list(r.scalars().all())

    async def get(self, session: AsyncSession, round_id: int) -> Round | None:
        return await session.get(Round, round_id)

    async def create(self, session: AsyncSession, data: RoundCreate) -> Round:
        rnd = Round(player_id=data.player_id, course_id=data.course_id)
        session.add(rnd)
        await session.flush()
        await session.refresh(rnd)
        return rnd

    async def update(
        self, session: AsyncSession, round_id: int, data: RoundUpdate
    ) -> Round | None:
        rnd = await self.get(session, round_id)
        if not rnd:
            return None
        if data.finished_at is not None:
            rnd.finished_at = data.finished_at
        await session.flush()
        await session.refresh(rnd)
        return rnd

    async def delete(self, session: AsyncSession, round_id: int) -> bool:
        rnd = await self.get(session, round_id)
        if not rnd:
            return False
        await session.delete(rnd)
        return True


round_service = RoundService()
