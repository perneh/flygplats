from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.schemas.course_statistics import CourseStatisticsRead
from app.schemas.hole import HoleRead
from app.schemas.hole_statistics import HoleStatisticsRead
from app.services.course_service import course_service
from app.services.hole_service import hole_service

router = APIRouter()


@router.get("/{course_id}/statistics", response_model=CourseStatisticsRead)
async def get_course_statistics(course_id: int, session: AsyncSession = Depends(get_session)):
    """
    Aggregates **rounds**, **strokes per player**, and **per-hole shot counts** on this course
    (all rounds / matches recorded for the course).
    """
    out = await course_service.get_statistics(session, course_id)
    if not out:
        raise HTTPException(status_code=404, detail="Course not found")
    return out


@router.get("/{course_id}/holes/{hole_number}", response_model=HoleRead)
async def get_course_hole_facts(
    course_id: int,
    hole_number: int = Path(..., ge=1, le=18, description="Hole index on the scorecard (1–18)"),
    session: AsyncSession = Depends(get_session),
):
    """Static hole data for this course: par, length, tee/green coordinates (same as ``GET /holes/{id}``, keyed by course + hole number)."""
    c = await course_service.get(session, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    h = await hole_service.get_by_course_and_number(session, course_id, hole_number)
    if not h:
        raise HTTPException(status_code=404, detail="Hole not found on this course")
    return HoleRead.from_hole(h)


@router.get("/{course_id}/holes/{hole_number}/statistics", response_model=HoleStatisticsRead)
async def get_course_hole_statistics(
    course_id: int,
    hole_number: int = Path(..., ge=1, le=18, description="Hole index on the scorecard (1–18)"),
    session: AsyncSession = Depends(get_session),
):
    """Aggregated shots on this hole: totals, distinct rounds, and per-player stroke counts."""
    c = await course_service.get(session, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    h = await hole_service.get_by_course_and_number(session, course_id, hole_number)
    if not h:
        raise HTTPException(status_code=404, detail="Hole not found on this course")
    return await course_service.aggregate_hole_statistics(session, c, h)


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
