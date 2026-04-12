from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Course, Hole, Player, Round, Shot
from app.schemas.course import CourseCreate, CourseUpdate
from app.schemas.course_statistics import CourseStatisticsRead, HoleActivityRow, PlayerCourseStatisticsRow


class CourseService:
    async def list(self, session: AsyncSession) -> list[Course]:
        r = await session.execute(select(Course).order_by(Course.id))
        return list(r.scalars().all())

    async def get(self, session: AsyncSession, course_id: int) -> Course | None:
        return await session.get(Course, course_id)

    async def create(self, session: AsyncSession, data: CourseCreate) -> Course:
        c = Course(
            name=data.name,
            country=data.country,
            description=data.description,
            catalog_id=data.catalog_id,
        )
        session.add(c)
        await session.flush()
        await session.refresh(c)
        return c

    async def update(
        self, session: AsyncSession, course_id: int, data: CourseUpdate
    ) -> Course | None:
        c = await self.get(session, course_id)
        if not c:
            return None
        if data.name is not None:
            c.name = data.name
        if data.country is not None:
            c.country = data.country
        if data.description is not None:
            c.description = data.description
        if data.catalog_id is not None:
            c.catalog_id = data.catalog_id
        await session.flush()
        await session.refresh(c)
        return c

    async def delete(self, session: AsyncSession, course_id: int) -> bool:
        c = await self.get(session, course_id)
        if not c:
            return False
        await session.delete(c)
        return True

    async def get_statistics(self, session: AsyncSession, course_id: int) -> CourseStatisticsRead | None:
        course = await self.get(session, course_id)
        if not course:
            return None

        r = await session.execute(select(Round).where(Round.course_id == course_id))
        rounds = list(r.scalars().all())
        total_rounds = len(rounds)
        if not rounds:
            return CourseStatisticsRead(
                course_id=course.id,
                course_name=course.name,
                total_rounds=0,
                players=[],
                holes=[],
            )

        round_ids = [x.id for x in rounds]
        sc = await session.execute(
            select(Shot.round_id, func.count(Shot.id))
            .where(Shot.round_id.in_(round_ids))
            .group_by(Shot.round_id)
        )
        count_by_round = {row[0]: int(row[1]) for row in sc.all()}

        from collections import defaultdict

        agg: dict[int, dict[str, int]] = defaultdict(lambda: {"rounds": 0, "strokes": 0})
        for rnd in rounds:
            pid = rnd.player_id
            agg[pid]["rounds"] += 1
            agg[pid]["strokes"] += count_by_round.get(rnd.id, 0)

        pids = sorted(agg.keys())
        pl = await session.execute(select(Player).where(Player.id.in_(pids)))
        names = {p.id: p.name for p in pl.scalars().all()}

        players = [
            PlayerCourseStatisticsRow(
                player_id=pid,
                player_name=names.get(pid, ""),
                rounds_played=agg[pid]["rounds"],
                total_strokes=agg[pid]["strokes"],
            )
            for pid in pids
        ]

        hole_rows = await session.execute(
            select(Hole.number, func.count(Shot.id))
            .select_from(Shot)
            .join(Hole, Shot.hole_id == Hole.id)
            .join(Round, Shot.round_id == Round.id)
            .where(Round.course_id == course_id)
            .group_by(Hole.number)
            .order_by(Hole.number)
        )
        holes = [
            HoleActivityRow(hole_number=int(n), total_strokes_recorded=int(cnt))
            for n, cnt in hole_rows.all()
        ]

        return CourseStatisticsRead(
            course_id=course.id,
            course_name=course.name,
            total_rounds=total_rounds,
            players=players,
            holes=holes,
        )


course_service = CourseService()
