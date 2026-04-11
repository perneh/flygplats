from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Course
from app.schemas.course import CourseCreate, CourseUpdate


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


course_service = CourseService()
