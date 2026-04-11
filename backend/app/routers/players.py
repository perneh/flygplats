from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.player import PlayerCreate, PlayerRead, PlayerUpdate
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
