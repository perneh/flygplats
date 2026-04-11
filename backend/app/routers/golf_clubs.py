from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.golf_club import GolfClubCreate, GolfClubRead, GolfClubUpdate
from app.services.golf_club_service import golf_club_service

router = APIRouter()


@router.post("", response_model=GolfClubRead, status_code=status.HTTP_201_CREATED, response_model_by_alias=True)
async def create_golf_club(data: GolfClubCreate, session: AsyncSession = Depends(get_session)):
    c = await golf_club_service.create(session, data)
    await session.commit()
    return c


@router.get("", response_model=list[GolfClubRead], response_model_by_alias=True)
async def list_golf_clubs(session: AsyncSession = Depends(get_session)):
    return await golf_club_service.list(session)


@router.get("/{club_id}", response_model=GolfClubRead, response_model_by_alias=True)
async def get_golf_club(club_id: int, session: AsyncSession = Depends(get_session)):
    c = await golf_club_service.get(session, club_id)
    if not c:
        raise HTTPException(status_code=404, detail="Golf club not found")
    return c


@router.patch("/{club_id}", response_model=GolfClubRead, response_model_by_alias=True)
async def update_golf_club(
    club_id: int, data: GolfClubUpdate, session: AsyncSession = Depends(get_session)
):
    c = await golf_club_service.update(session, club_id, data)
    if not c:
        raise HTTPException(status_code=404, detail="Golf club not found")
    await session.commit()
    return c
