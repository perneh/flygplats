from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.geo.canvas_project import bounds_from_latlng_pairs, project_latlng_to_canvas
from app.models import Hole
from app.schemas.hole import HoleCreate, HoleUpdate


class HoleService:
    async def list(self, session: AsyncSession, course_id: int | None = None) -> list[Hole]:
        q = select(Hole).order_by(Hole.course_id, Hole.number)
        if course_id is not None:
            q = q.where(Hole.course_id == course_id)
        r = await session.execute(q)
        return list(r.scalars().all())

    async def get(self, session: AsyncSession, hole_id: int) -> Hole | None:
        return await session.get(Hole, hole_id)

    async def get_by_course_and_number(
        self, session: AsyncSession, course_id: int, hole_number: int
    ) -> Hole | None:
        r = await session.execute(
            select(Hole).where(Hole.course_id == course_id, Hole.number == hole_number)
        )
        return r.scalar_one_or_none()

    async def create(self, session: AsyncSession, data: HoleCreate) -> Hole:
        if data.tee is not None and data.green is not None:
            pairs = [
                (data.tee.lat, data.tee.lng),
                (data.green.lat, data.green.lng),
            ]
            b = bounds_from_latlng_pairs(pairs)
            tx, ty = project_latlng_to_canvas(data.tee.lat, data.tee.lng, b)
            gx, gy = project_latlng_to_canvas(data.green.lat, data.green.lng, b)
            h = Hole(
                course_id=data.course_id,
                number=data.hole,
                par=data.par,
                length_m=data.length_m,
                tee_lat=data.tee.lat,
                tee_lng=data.tee.lng,
                green_lat=data.green.lat,
                green_lng=data.green.lng,
                tee_x=tx,
                tee_y=ty,
                green_x=gx,
                green_y=gy,
            )
        else:
            h = Hole(
                course_id=data.course_id,
                number=data.hole,
                par=data.par,
                length_m=data.length_m,
                tee_lat=None,
                tee_lng=None,
                green_lat=None,
                green_lng=None,
                tee_x=data.tee_x,
                tee_y=data.tee_y,
                green_x=data.green_x,
                green_y=data.green_y,
            )
        session.add(h)
        await session.flush()
        await session.refresh(h)
        return h

    async def update(
        self, session: AsyncSession, hole_id: int, data: HoleUpdate
    ) -> Hole | None:
        h = await self.get(session, hole_id)
        if not h:
            return None
        for field in (
            "number",
            "par",
            "length_m",
            "tee_lat",
            "tee_lng",
            "green_lat",
            "green_lng",
            "tee_x",
            "tee_y",
            "green_x",
            "green_y",
        ):
            val = getattr(data, field)
            if val is not None:
                setattr(h, field, val)
        await session.flush()
        await session.refresh(h)
        return h

    async def delete(self, session: AsyncSession, hole_id: int) -> bool:
        h = await self.get(session, hole_id)
        if not h:
            return False
        await session.delete(h)
        return True


hole_service = HoleService()
