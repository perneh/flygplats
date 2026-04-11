from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.hole import HoleCreate, HoleRead, HoleUpdate
from app.services.hole_service import hole_service

router = APIRouter()


@router.get("", response_model=list[HoleRead])
async def list_holes(
    course_id: int | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    rows = await hole_service.list(session, course_id=course_id)
    return [HoleRead.from_hole(h) for h in rows]


@router.post("", response_model=HoleRead, status_code=status.HTTP_201_CREATED)
async def create_hole(data: HoleCreate, session: AsyncSession = Depends(get_session)):
    h = await hole_service.create(session, data)
    await session.commit()
    await session.refresh(h)
    return HoleRead.from_hole(h)


@router.get("/{hole_id}", response_model=HoleRead)
async def get_hole(hole_id: int, session: AsyncSession = Depends(get_session)):
    h = await hole_service.get(session, hole_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hole not found")
    return HoleRead.from_hole(h)


@router.patch("/{hole_id}", response_model=HoleRead)
async def update_hole(
    hole_id: int, data: HoleUpdate, session: AsyncSession = Depends(get_session)
):
    h = await hole_service.update(session, hole_id, data)
    if not h:
        raise HTTPException(status_code=404, detail="Hole not found")
    await session.commit()
    await session.refresh(h)
    return HoleRead.from_hole(h)


@router.delete("/{hole_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hole(hole_id: int, session: AsyncSession = Depends(get_session)):
    ok = await hole_service.delete(session, hole_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Hole not found")
    await session.commit()
