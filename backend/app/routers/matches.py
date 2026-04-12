from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.match import MatchCreate, MatchRead
from app.services.match_service import match_service

router = APIRouter()


@router.post("", response_model=MatchRead, status_code=status.HTTP_201_CREATED)
async def create_match(data: MatchCreate, session: AsyncSession = Depends(get_session)):
    """
    One shared **match**: creates one **round** per player on the same course, then records
    shots per hole. Use existing ``player`` ids and a ``course`` that already has **holes**
    defined (e.g. seeded courses).
    """
    out = await match_service.create_match(session, data)
    await session.commit()
    return out
