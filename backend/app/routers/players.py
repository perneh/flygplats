from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.performance import PlayerPerformanceRead
from app.schemas.player import PlayerCreate, PlayerRead, PlayerUpdate
from app.services.performance_service import performance_service
from app.services.player_service import player_service

router = APIRouter()


@router.get("", response_model=list[PlayerRead])
async def list_players(session: AsyncSession = Depends(get_session)):
    rows = await player_service.list(session)
    return rows


@router.post("", response_model=PlayerRead, status_code=status.HTTP_201_CREATED)
async def create_player(data: PlayerCreate, session: AsyncSession = Depends(get_session)):
    p = await player_service.create(session, data)
    await session.commit()
    return p


@router.get("/{player_id}/performance", response_model=PlayerPerformanceRead)
async def get_player_performance(
    player_id: int,
    course_id: list[int] | None = Query(
        None,
        description="Only rounds on these course ids (repeat param for multiple)",
    ),
    hole_number: list[int] | None = Query(
        None,
        description="Only these hole numbers (1–18); repeat for multiple",
    ),
    session: AsyncSession = Depends(get_session),
):
    """
    Shots grouped by round and hole for this player. Filter by one or more **courses** and/or
    **hole numbers** across all their rounds.
    """
    return await performance_service.get_player_performance(
        session,
        player_id,
        course_id or (),
        hole_number or (),
    )


@router.get("/{player_id}", response_model=PlayerRead)
async def get_player(player_id: int, session: AsyncSession = Depends(get_session)):
    p = await player_service.get(session, player_id)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    return p


@router.patch("/{player_id}", response_model=PlayerRead)
async def update_player(
    player_id: int, data: PlayerUpdate, session: AsyncSession = Depends(get_session)
):
    p = await player_service.update(session, player_id, data)
    if not p:
        raise HTTPException(status_code=404, detail="Player not found")
    await session.commit()
    return p


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_player(player_id: int, session: AsyncSession = Depends(get_session)):
    ok = await player_service.delete(session, player_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Player not found")
    await session.commit()
