from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.shot import ShotCreate, ShotRead, ShotUpdate
from app.services.shot_service import shot_service

router = APIRouter()


@router.get("", response_model=list[ShotRead])
async def list_shots(
    round_id: int | None = Query(None, description="Filter by round"),
    hole_id: int | None = Query(None, description="Filter by hole"),
    session: AsyncSession = Depends(get_session),
):
    """List shots, optionally filtered by round and/or hole."""
    if round_id is None and hole_id is None:
        return await shot_service.list(session)
    return await shot_service.list(session, round_id=round_id, hole_id=hole_id)


@router.post("", response_model=ShotRead, status_code=status.HTTP_201_CREATED)
async def create_shot(data: ShotCreate, session: AsyncSession = Depends(get_session)):
    s = await shot_service.create(session, data)
    await session.commit()
    return s


@router.get("/{shot_id}", response_model=ShotRead)
async def get_shot(shot_id: int, session: AsyncSession = Depends(get_session)):
    s = await shot_service.get(session, shot_id)
    if not s:
        raise HTTPException(status_code=404, detail="Shot not found")
    return s


@router.patch("/{shot_id}", response_model=ShotRead)
async def update_shot(
    shot_id: int, data: ShotUpdate, session: AsyncSession = Depends(get_session)
):
    s = await shot_service.update(session, shot_id, data)
    if not s:
        raise HTTPException(status_code=404, detail="Shot not found")
    await session.commit()
    return s


@router.delete("/{shot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shot(shot_id: int, session: AsyncSession = Depends(get_session)):
    ok = await shot_service.delete(session, shot_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Shot not found")
    await session.commit()
