from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.services.course_service import course_service

router = APIRouter()


@router.get("", response_model=list[CourseRead])
async def list_courses(session: AsyncSession = Depends(get_session)):
    return await course_service.list(session)


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(data: CourseCreate, session: AsyncSession = Depends(get_session)):
    c = await course_service.create(session, data)
    await session.commit()
    return c


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(course_id: int, session: AsyncSession = Depends(get_session)):
    c = await course_service.get(session, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    return c


@router.patch("/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: int, data: CourseUpdate, session: AsyncSession = Depends(get_session)
):
    c = await course_service.update(session, course_id, data)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    await session.commit()
    return c


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: int, session: AsyncSession = Depends(get_session)):
    ok = await course_service.delete(session, course_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Course not found")
    await session.commit()
