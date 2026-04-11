from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Player
from app.schemas.player import PlayerCreate, PlayerUpdate


class PlayerService:
    async def list(self, session: AsyncSession) -> list[Player]:
        r = await session.execute(select(Player).order_by(Player.id))
        return list(r.scalars().all())

    async def get(self, session: AsyncSession, player_id: int) -> Player | None:
        return await session.get(Player, player_id)

    async def create(self, session: AsyncSession, data: PlayerCreate) -> Player:
        p = Player(name=data.name)
        session.add(p)
        await session.flush()
        await session.refresh(p)
        return p

    async def update(
        self, session: AsyncSession, player_id: int, data: PlayerUpdate
    ) -> Player | None:
        p = await self.get(session, player_id)
        if not p:
            return None
        if data.name is not None:
            p.name = data.name
        await session.flush()
        await session.refresh(p)
        return p

    async def delete(self, session: AsyncSession, player_id: int) -> bool:
        p = await self.get(session, player_id)
        if not p:
            return False
        await session.delete(p)
        return True


player_service = PlayerService()
