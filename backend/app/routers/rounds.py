from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.round import RoundCreate, RoundRead, RoundUpdate
from app.schemas.shot import ShotRead
from app.services.round_service import round_service
from app.services.shot_service import shot_service

router = APIRouter()


@router.get("", response_model=list[RoundRead])
async def list_rounds(
    player_id: int | None = Query(None),
    course_id: int | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    return await round_service.list(session, player_id=player_id, course_id=course_id)


@router.post("", response_model=RoundRead, status_code=status.HTTP_201_CREATED)
async def create_round(data: RoundCreate, session: AsyncSession = Depends(get_session)):
    rnd = await round_service.create(session, data)
    await session.commit()
    return rnd


@router.get("/{round_id}/shots", response_model=list[ShotRead])
async def list_shots_for_round(
    round_id: int,
    hole_id: int | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Shots for a round, optionally restricted to one hole."""
    rnd = await round_service.get(session, round_id)
    if not rnd:
        raise HTTPException(status_code=404, detail="Round not found")
    return await shot_service.list(session, round_id=round_id, hole_id=hole_id)


@router.get("/{round_id}", response_model=RoundRead)
async def get_round(round_id: int, session: AsyncSession = Depends(get_session)):
    rnd = await round_service.get(session, round_id)
    if not rnd:
        raise HTTPException(status_code=404, detail="Round not found")
    return rnd


@router.patch("/{round_id}", response_model=RoundRead)
async def update_round(
    round_id: int, data: RoundUpdate, session: AsyncSession = Depends(get_session)
):
    rnd = await round_service.update(session, round_id, data)
    if not rnd:
        raise HTTPException(status_code=404, detail="Round not found")
    await session.commit()
    return rnd


@router.delete("/{round_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_round(round_id: int, session: AsyncSession = Depends(get_session)):
    ok = await round_service.delete(session, round_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Round not found")
    await session.commit()
