from collections import defaultdict
from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Course, Hole, Player, Round, Shot
from app.schemas.performance import PerformanceHoleBlock, PerformanceRoundBlock, PlayerPerformanceRead
from app.schemas.shot import ShotRead


class PerformanceService:
    async def get_player_performance(
        self,
        session: AsyncSession,
        player_id: int,
        course_ids: Sequence[int] | None,
        hole_numbers: Sequence[int] | None,
    ) -> PlayerPerformanceRead:
        player = await session.get(Player, player_id)
        if not player:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

        q = select(Round).where(Round.player_id == player_id).order_by(Round.started_at.desc())
        r = await session.execute(q)
        all_rounds = list(r.scalars().all())

        if course_ids:
            cid_set = set(course_ids)
            all_rounds = [x for x in all_rounds if x.course_id in cid_set]

        if not all_rounds:
            return PlayerPerformanceRead(
                player_id=player.id,
                player_name=player.name,
                rounds=[],
            )

        round_ids = [x.id for x in all_rounds]
        sh = await session.execute(select(Shot).where(Shot.round_id.in_(round_ids)))
        shots = list(sh.scalars().all())

        hole_ids = {s.hole_id for s in shots}
        holes_by_id: dict[int, Hole] = {}
        if hole_ids:
            hr = await session.execute(select(Hole).where(Hole.id.in_(hole_ids)))
            for h in hr.scalars().all():
                holes_by_id[h.id] = h

        course_ids_needed = {x.course_id for x in all_rounds}
        courses_by_id: dict[int, Course] = {}
        if course_ids_needed:
            cr = await session.execute(select(Course).where(Course.id.in_(course_ids_needed)))
            for c in cr.scalars().all():
                courses_by_id[c.id] = c

        hole_filter = set(hole_numbers) if hole_numbers else None

        # (round_id, hole_id) -> list[Shot]
        bucket: dict[tuple[int, int], list[Shot]] = defaultdict(list)
        for s in shots:
            h = holes_by_id.get(s.hole_id)
            if not h:
                continue
            if hole_filter is not None and h.number not in hole_filter:
                continue
            bucket[(s.round_id, s.hole_id)].append(s)

        blocks: list[PerformanceRoundBlock] = []
        for rnd in all_rounds:
            c = courses_by_id.get(rnd.course_id)
            course_name = c.name if c else ""

            hole_blocks: list[PerformanceHoleBlock] = []
            keys_for_round = [k for k in bucket if k[0] == rnd.id]
            keys_for_round.sort(key=lambda k: holes_by_id[k[1]].number)

            for _, hid in keys_for_round:
                h = holes_by_id[hid]
                group = bucket[(rnd.id, hid)]
                group.sort(key=lambda x: (x.shot_at, x.id))
                hole_blocks.append(
                    PerformanceHoleBlock(
                        hole_number=h.number,
                        hole_id=h.id,
                        par=h.par,
                        stroke_count=len(group),
                        shots=[ShotRead.model_validate(x) for x in group],
                    )
                )

            if hole_filter is not None and not hole_blocks:
                continue

            blocks.append(
                PerformanceRoundBlock(
                    round_id=rnd.id,
                    course_id=rnd.course_id,
                    course_name=course_name,
                    started_at=rnd.started_at,
                    finished_at=rnd.finished_at,
                    holes=hole_blocks,
                )
            )

        return PlayerPerformanceRead(
            player_id=player.id,
            player_name=player.name,
            rounds=blocks,
        )


performance_service = PerformanceService()
