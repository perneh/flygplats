from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.tournament import (
    ScorecardRead,
    TournamentCreate,
    TournamentDetailRead,
    TournamentIdBody,
    TournamentLeaderboardRead,
    TournamentParticipantAddBody,
    TournamentParticipantCreate,
    TournamentParticipantRead,
    TournamentPlayerIdsBody,
    TournamentPlayerShotDetailRead,
    TournamentRead,
)
from app.services.tournament_service import tournament_service

router = APIRouter()


@router.get("", response_model=list[TournamentRead])
async def list_tournaments(session: AsyncSession = Depends(get_session)):
    return await tournament_service.list_all(session)


@router.get("/drafts", response_model=list[TournamentRead])
async def list_tournament_drafts(session: AsyncSession = Depends(get_session)):
    """Tournaments not yet started — suitable for picking one to start."""
    return await tournament_service.list_drafts(session)


@router.get("/started", response_model=list[TournamentRead])
async def list_tournaments_started(session: AsyncSession = Depends(get_session)):
    """Tournaments in progress (started, not marked finished)."""
    return await tournament_service.list_started(session)


@router.get("/non-draft", response_model=list[TournamentRead])
async def list_tournaments_non_draft(session: AsyncSession = Depends(get_session)):
    """Started or finished tournaments (have flights/scorecards) — e.g. scorecards / results."""
    return await tournament_service.list_non_drafts(session)


@router.post("", response_model=TournamentRead, status_code=status.HTTP_201_CREATED)
async def create_tournament(data: TournamentCreate, session: AsyncSession = Depends(get_session)):
    t = await tournament_service.create(session, data)
    await session.commit()
    return t


@router.post(
    "/participants",
    response_model=TournamentParticipantRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_participant(
    data: TournamentParticipantAddBody,
    session: AsyncSession = Depends(get_session),
):
    p = await tournament_service.add_participant(
        session,
        data.tournament_id,
        TournamentParticipantCreate(player_id=data.player_id, handicap=data.handicap),
    )
    await session.commit()
    return p


@router.post("/start", response_model=TournamentDetailRead)
async def start_tournament(data: TournamentIdBody, session: AsyncSession = Depends(get_session)):
    detail = await tournament_service.start(session, data.tournament_id)
    await session.commit()
    return detail


@router.post("/stop", response_model=TournamentDetailRead)
async def stop_tournament(data: TournamentIdBody, session: AsyncSession = Depends(get_session)):
    """Mark an in-progress tournament as finished."""
    detail = await tournament_service.stop(session, data.tournament_id)
    await session.commit()
    return detail


@router.post("/scorecards", response_model=list[ScorecardRead])
async def list_tournament_scorecards(data: TournamentIdBody, session: AsyncSession = Depends(get_session)):
    rows = await tournament_service.list_scorecards(session, data.tournament_id)
    return rows


@router.post("/leaderboard", response_model=TournamentLeaderboardRead)
async def get_tournament_leaderboard(data: TournamentIdBody, session: AsyncSession = Depends(get_session)):
    return await tournament_service.get_leaderboard(session, data.tournament_id)


@router.post("/shot-detail", response_model=TournamentPlayerShotDetailRead)
async def get_tournament_player_shot_detail(
    data: TournamentPlayerIdsBody,
    session: AsyncSession = Depends(get_session),
):
    return await tournament_service.get_player_shot_detail(session, data.tournament_id, data.player_id)


@router.post("/detail", response_model=TournamentDetailRead)
async def get_tournament(data: TournamentIdBody, session: AsyncSession = Depends(get_session)):
    return await tournament_service.get_detail(session, data.tournament_id)
