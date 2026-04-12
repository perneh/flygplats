from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Hole, Player, Round, Shot
from app.schemas.match import MatchCreate, MatchRead
from app.schemas.round import RoundRead
from app.services.course_service import course_service


class MatchService:
    async def create_match(self, session: AsyncSession, data: MatchCreate) -> MatchRead:
        course_id = data.course_id
        player_ids = data.player_ids

        course = await course_service.get(session, course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

        for pid in player_ids:
            p = await session.get(Player, pid)
            if not p:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Player not found: {pid}",
                )

        rounds: list[Round] = []
        player_to_round: dict[int, int] = {}
        for pid in player_ids:
            rnd = Round(player_id=pid, course_id=course_id)
            session.add(rnd)
            await session.flush()
            await session.refresh(rnd)
            rounds.append(rnd)
            player_to_round[pid] = rnd.id

        shots_created = 0
        for hole_in in data.holes:
            hole = await self._get_hole(session, course_id, hole_in.hole_number)
            if not hole:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No hole {hole_in.hole_number} on course {course_id}",
                )

            seen_players: set[int] = set()
            for block in hole_in.by_player:
                if block.player_id not in player_to_round:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"player_id {block.player_id} is not in this match",
                    )
                if block.player_id in seen_players:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"duplicate player_id {block.player_id} for hole {hole_in.hole_number}",
                    )
                seen_players.add(block.player_id)

                rid = player_to_round[block.player_id]
                for s in block.shots:
                    session.add(
                        Shot(
                            round_id=rid,
                            hole_id=hole.id,
                            x=s.x,
                            y=s.y,
                            club=s.club,
                            distance=s.distance,
                        )
                    )
                    shots_created += 1

        if data.finished_at is not None:
            for rnd in rounds:
                rnd.finished_at = data.finished_at

        await session.flush()
        for rnd in rounds:
            await session.refresh(rnd)

        return MatchRead(
            course_id=course_id,
            rounds=[RoundRead.model_validate(r) for r in rounds],
            shots_created=shots_created,
        )

    async def _get_hole(
        self, session: AsyncSession, course_id: int, hole_number: int
    ) -> Hole | None:
        r = await session.execute(
            select(Hole).where(Hole.course_id == course_id, Hole.number == hole_number)
        )
        return r.scalar_one_or_none()


match_service = MatchService()
