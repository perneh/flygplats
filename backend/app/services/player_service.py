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
        p = Player(
            name=data.name,
            handicap=data.handicap,
            age=data.age,
            gender=data.gender,
            email=data.email,
            sponsor=data.sponsor,
            phone=data.phone,
            country=data.country,
            club=data.club,
            rank=data.rank,
        )
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
        if "name" in data.model_fields_set and data.name is not None:
            p.name = data.name
        if "handicap" in data.model_fields_set:
            p.handicap = data.handicap
        if "age" in data.model_fields_set:
            p.age = data.age
        if "gender" in data.model_fields_set:
            p.gender = data.gender
        if "email" in data.model_fields_set:
            p.email = data.email
        if "sponsor" in data.model_fields_set:
            p.sponsor = data.sponsor
        if "phone" in data.model_fields_set:
            p.phone = data.phone
        if "country" in data.model_fields_set:
            p.country = data.country
        if "club" in data.model_fields_set:
            p.club = data.club
        if "rank" in data.model_fields_set:
            p.rank = data.rank
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
