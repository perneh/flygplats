from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.tournament import ScorecardHoleUpdateBody, ScorecardIdBody, ScorecardRead
from app.services.tournament_service import tournament_service

router = APIRouter()


@router.post("/detail", response_model=ScorecardRead)
async def get_scorecard(data: ScorecardIdBody, session: AsyncSession = Depends(get_session)):
    return await tournament_service.get_scorecard(session, data.scorecard_id)


@router.post("/hole", response_model=ScorecardRead)
async def patch_scorecard_hole(
    data: ScorecardHoleUpdateBody,
    session: AsyncSession = Depends(get_session),
):
    card = await tournament_service.patch_hole(session, data)
    await session.commit()
    return card
