"""Tournament lifecycle: participants, flights by handicap, scorecards."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Hole, Player, Round, Shot
from app.models.tournament import Tournament, TournamentFlight, TournamentParticipant, TournamentStatus
from app.models.tournament_scorecard import HoleScore, Scorecard
from app.schemas.tournament import (
    CourseBrief,
    HoleScoreItem,
    LeaderboardHoleRow,
    LeaderboardPlayerRow,
    ScorecardHoleUpdateBody,
    ScorecardRead,
    TournamentCreate,
    TournamentDetailRead,
    TournamentFlightRead,
    TournamentHoleShotDetail,
    TournamentLeaderboardRead,
    TournamentParticipantCreate,
    TournamentParticipantRead,
    TournamentPlayerShotDetailRead,
    TournamentRead,
    TournamentShotDetailItem,
)
from app.services.course_service import course_service

MAX_TOURNAMENT_PARTICIPANTS = 75
FLIGHT_SIZE = 4


def _totals_from_holes(holes: Sequence[HoleScoreItem]) -> tuple[int, int, int]:
    by_n = {h.hole_number: h.strokes for h in holes}
    out_sum = 0
    inn_sum = 0
    for n in range(1, 10):
        v = by_n.get(n)
        if v is not None:
            out_sum += v
    for n in range(10, 19):
        v = by_n.get(n)
        if v is not None:
            inn_sum += v
    return out_sum, inn_sum, out_sum + inn_sum


def _scorecard_to_read(sc: Scorecard) -> ScorecardRead:
    player = sc.player
    holes_sorted = sorted(sc.hole_scores, key=lambda h: h.hole_number)
    items = [HoleScoreItem(hole_number=h.hole_number, strokes=h.strokes) for h in holes_sorted]
    out_t, in_t, gross = _totals_from_holes(items)
    return ScorecardRead(
        id=sc.id,
        tournament_id=sc.tournament_id,
        player_id=sc.player_id,
        player_name=player.name if player else "",
        flight_id=sc.flight_id,
        flight_sequence=sc.flight.sequence if sc.flight else 0,
        holes=items,
        out_total=out_t,
        in_total=in_t,
        gross_total=gross,
    )


class TournamentService:
    async def list_all(self, session: AsyncSession) -> list[TournamentRead]:
        r = await session.execute(select(Tournament).order_by(Tournament.play_date.desc(), Tournament.id.desc()))
        rows = list(r.scalars().all())
        return [TournamentRead.model_validate(t) for t in rows]

    async def list_drafts(self, session: AsyncSession) -> list[TournamentRead]:
        r = await session.execute(
            select(Tournament)
            .where(Tournament.status == TournamentStatus.DRAFT)
            .order_by(Tournament.play_date.desc(), Tournament.id.desc())
        )
        rows = list(r.scalars().all())
        return [TournamentRead.model_validate(t) for t in rows]

    async def list_started(self, session: AsyncSession) -> list[TournamentRead]:
        """Tournaments currently in progress (started, not yet marked finished)."""
        r = await session.execute(
            select(Tournament)
            .where(Tournament.status == TournamentStatus.STARTED)
            .order_by(Tournament.play_date.desc(), Tournament.id.desc())
        )
        rows = list(r.scalars().all())
        return [TournamentRead.model_validate(t) for t in rows]

    async def list_non_drafts(self, session: AsyncSession) -> list[TournamentRead]:
        """Tournaments that have been started at least once (in progress or finished) — for scorecards / results."""
        r = await session.execute(
            select(Tournament)
            .where(Tournament.status.in_((TournamentStatus.STARTED, TournamentStatus.FINISHED)))
            .order_by(Tournament.play_date.desc(), Tournament.id.desc())
        )
        rows = list(r.scalars().all())
        return [TournamentRead.model_validate(t) for t in rows]

    async def create(self, session: AsyncSession, data: TournamentCreate) -> TournamentRead:
        course = await course_service.get(session, data.course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        t = Tournament(
            name=data.name.strip(),
            play_date=data.play_date,
            course_id=data.course_id,
            status=TournamentStatus.DRAFT,
        )
        session.add(t)
        await session.flush()
        await session.refresh(t)
        return TournamentRead.model_validate(t)

    async def add_participant(
        self,
        session: AsyncSession,
        tournament_id: int,
        data: TournamentParticipantCreate,
    ) -> TournamentParticipantRead:
        t = await session.get(Tournament, tournament_id)
        if not t:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if t.status != TournamentStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add participants after the tournament has started",
            )
        count = await session.scalar(
            select(TournamentParticipant).where(TournamentParticipant.tournament_id == tournament_id)
        )
        # scalar on select entity returns wrong - use count
        from sqlalchemy import func

        n = await session.scalar(
            select(func.count()).select_from(TournamentParticipant).where(
                TournamentParticipant.tournament_id == tournament_id
            )
        )
        if n is not None and n >= MAX_TOURNAMENT_PARTICIPANTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tournament is limited to {MAX_TOURNAMENT_PARTICIPANTS} participants",
            )

        player = await session.get(Player, data.player_id)
        if not player:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

        existing = await session.scalar(
            select(TournamentParticipant).where(
                TournamentParticipant.tournament_id == tournament_id,
                TournamentParticipant.player_id == data.player_id,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Player is already registered for this tournament",
            )

        tp = TournamentParticipant(
            tournament_id=tournament_id,
            player_id=data.player_id,
            handicap=float(data.handicap),
        )
        session.add(tp)
        await session.flush()
        await session.refresh(tp, attribute_names=["player"])
        return TournamentParticipantRead(
            id=tp.id,
            player_id=tp.player_id,
            player_name=tp.player.name,
            handicap=tp.handicap,
        )

    async def start(self, session: AsyncSession, tournament_id: int) -> TournamentDetailRead:
        t = await session.get(
            Tournament,
            tournament_id,
            options=[
                selectinload(Tournament.participants).selectinload(TournamentParticipant.player),
            ],
        )
        if not t:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if t.status == TournamentStatus.FINISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot start a tournament that has already finished",
            )
        if t.status == TournamentStatus.STARTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tournament has already been started",
            )
        if not t.participants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Need at least one participant to start",
            )

        # Remove any stale flights/scorecards (should not exist in draft)
        await session.execute(
            HoleScore.__table__.delete().where(
                HoleScore.scorecard_id.in_(
                    select(Scorecard.id).where(Scorecard.tournament_id == tournament_id)
                )
            )
        )
        await session.execute(Scorecard.__table__.delete().where(Scorecard.tournament_id == tournament_id))
        await session.execute(
            TournamentFlight.__table__.delete().where(TournamentFlight.tournament_id == tournament_id)
        )

        sorted_parts = sorted(t.participants, key=lambda p: (p.handicap, p.id))
        flights: list[tuple[TournamentFlight, list[TournamentParticipant]]] = []
        seq = 1
        for i in range(0, len(sorted_parts), FLIGHT_SIZE):
            chunk = sorted_parts[i : i + FLIGHT_SIZE]
            fl = TournamentFlight(
                tournament_id=tournament_id,
                sequence=seq,
                name=f"Flight {seq}",
            )
            session.add(fl)
            await session.flush()
            flights.append((fl, chunk))
            seq += 1

        for fl, chunk in flights:
            for tp in chunk:
                sc = Scorecard(
                    tournament_id=tournament_id,
                    player_id=tp.player_id,
                    flight_id=fl.id,
                )
                session.add(sc)
                await session.flush()
                for hole_number in range(1, 19):
                    session.add(HoleScore(scorecard_id=sc.id, hole_number=hole_number, strokes=None))
        t.status = TournamentStatus.STARTED
        await session.flush()
        return await self.get_detail(session, tournament_id)

    async def stop(self, session: AsyncSession, tournament_id: int) -> TournamentDetailRead:
        """Mark an in-progress tournament as finished (no more scoring changes expected)."""
        t = await session.get(Tournament, tournament_id)
        if not t:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        if t.status != TournamentStatus.STARTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only a tournament that has been started can be marked finished",
            )
        t.status = TournamentStatus.FINISHED
        await session.flush()
        return await self.get_detail(session, tournament_id)

    async def get_detail(self, session: AsyncSession, tournament_id: int) -> TournamentDetailRead:
        result = await session.execute(
            select(Tournament)
            .where(Tournament.id == tournament_id)
            .options(
                selectinload(Tournament.course),
                selectinload(Tournament.participants).selectinload(TournamentParticipant.player),
                selectinload(Tournament.flights).selectinload(TournamentFlight.scorecards),
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        return self._to_detail_read(row)

    def _to_detail_read(self, t: Tournament) -> TournamentDetailRead:
        course = t.course
        assert course is not None
        parts = sorted(
            (
                TournamentParticipantRead(
                    id=p.id,
                    player_id=p.player_id,
                    player_name=p.player.name,
                    handicap=p.handicap,
                )
                for p in t.participants
            ),
            key=lambda x: (x.handicap, x.player_id),
        )
        flight_reads: list[TournamentFlightRead] = []
        for fl in sorted(t.flights, key=lambda f: f.sequence):
            pids: list[int] = []
            for sc in sorted(fl.scorecards, key=lambda s: s.id):
                pids.append(sc.player_id)
            flight_reads.append(
                TournamentFlightRead(id=fl.id, sequence=fl.sequence, name=fl.name, player_ids=pids)
            )
        base = TournamentRead.model_validate(t)
        return TournamentDetailRead(
            **base.model_dump(),
            course=CourseBrief(id=course.id, name=course.name),
            participants=parts,
            flights=flight_reads,
        )

    async def list_scorecards(self, session: AsyncSession, tournament_id: int) -> list[ScorecardRead]:
        t = await session.get(Tournament, tournament_id)
        if not t:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        r = await session.execute(
            select(Scorecard)
            .where(Scorecard.tournament_id == tournament_id)
            .options(
                selectinload(Scorecard.player),
                selectinload(Scorecard.flight),
                selectinload(Scorecard.hole_scores),
            )
            .order_by(Scorecard.flight_id, Scorecard.id)
        )
        cards = list(r.scalars().all())
        return [_scorecard_to_read(sc) for sc in cards]

    async def get_scorecard(self, session: AsyncSession, scorecard_id: int) -> ScorecardRead:
        r = await session.execute(
            select(Scorecard)
            .where(Scorecard.id == scorecard_id)
            .options(
                selectinload(Scorecard.player),
                selectinload(Scorecard.flight),
                selectinload(Scorecard.hole_scores),
            )
        )
        sc = r.scalar_one_or_none()
        if not sc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scorecard not found")
        return _scorecard_to_read(sc)

    async def patch_hole(self, session: AsyncSession, body: ScorecardHoleUpdateBody) -> ScorecardRead:
        scorecard_id = body.scorecard_id
        hole_number = body.hole_number
        r = await session.execute(
            select(Scorecard)
            .where(Scorecard.id == scorecard_id)
            .options(
                selectinload(Scorecard.player),
                selectinload(Scorecard.flight),
                selectinload(Scorecard.hole_scores),
            )
        )
        sc = r.scalar_one_or_none()
        if not sc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scorecard not found")
        tr = await session.get(Tournament, sc.tournament_id)
        if tr is not None and tr.status == TournamentStatus.FINISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tournament is finished; stroke updates are not allowed",
            )
        if body.player_id != sc.player_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="player_id does not match this scorecard",
            )
        hs = next((h for h in sc.hole_scores if h.hole_number == hole_number), None)
        if not hs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hole not found on scorecard")
        hs.strokes = body.strokes
        await session.flush()
        await session.refresh(sc, attribute_names=["hole_scores", "player", "flight"])
        return _scorecard_to_read(sc)

    async def _par_by_hole_number(self, session: AsyncSession, course_id: int) -> dict[int, int]:
        r = await session.execute(
            select(Hole).where(Hole.course_id == course_id).order_by(Hole.number)
        )
        return {h.number: h.par for h in r.scalars().all()}

    @staticmethod
    def _utc_calendar_date(dt: datetime) -> date:
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).date()
        return dt.date()

    async def get_leaderboard(self, session: AsyncSession, tournament_id: int) -> TournamentLeaderboardRead:
        t = await session.execute(
            select(Tournament)
            .where(Tournament.id == tournament_id)
            .options(selectinload(Tournament.course))
        )
        row = t.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
        course = row.course
        assert course is not None
        par_by = await self._par_by_hole_number(session, course.id)
        course_par_total = sum(par_by.get(n, 4) for n in range(1, 19))

        r_sc = await session.execute(
            select(Scorecard)
            .where(Scorecard.tournament_id == tournament_id)
            .options(selectinload(Scorecard.player), selectinload(Scorecard.hole_scores))
        )
        cards = list(r_sc.scalars().all())

        players_out: list[LeaderboardPlayerRow] = []
        for sc in sorted(cards, key=lambda x: x.player_id):
            by_hole = {h.hole_number: h.strokes for h in sc.hole_scores}
            holes_out: list[LeaderboardHoleRow] = []
            gross = 0
            par_sum_recorded = 0
            for n in range(1, 19):
                par = par_by.get(n, 4)
                strokes = by_hole.get(n)
                if strokes is not None:
                    gross += strokes
                    par_sum_recorded += par
                    to_h = strokes - par
                else:
                    to_h = None
                holes_out.append(
                    LeaderboardHoleRow(
                        hole_number=n,
                        par=par,
                        strokes=strokes,
                        to_par=to_h,
                    )
                )
            to_par = gross - par_sum_recorded if par_sum_recorded > 0 else None
            pname = sc.player.name if sc.player else ""
            players_out.append(
                LeaderboardPlayerRow(
                    rank=0,
                    player_id=sc.player_id,
                    player_name=pname,
                    gross_total=gross,
                    to_par=to_par,
                    holes=holes_out,
                )
            )

        players_sorted = sorted(players_out, key=lambda p: (p.gross_total, p.player_id))
        for p in players_sorted:
            p.rank = 1 + sum(1 for q in players_sorted if q.gross_total < p.gross_total)

        return TournamentLeaderboardRead(
            tournament_id=row.id,
            tournament_name=row.name,
            course_id=course.id,
            course_name=course.name,
            course_par_total=course_par_total,
            players=players_sorted,
        )

    async def _pick_round_for_tournament_player(
        self, session: AsyncSession, tournament: Tournament, player_id: int
    ) -> Round | None:
        """Same course, same calendar day as ``tournament.play_date``; prefer most shots then latest start."""
        r = await session.execute(
            select(Round).where(Round.player_id == player_id, Round.course_id == tournament.course_id)
        )
        candidates = list(r.scalars().all())
        day = tournament.play_date
        matching = [x for x in candidates if self._utc_calendar_date(x.started_at) == day]
        if not matching:
            return None

        best: Round | None = None
        best_n = -1
        for rnd in matching:
            n = await session.scalar(
                select(func.count()).select_from(Shot).where(Shot.round_id == rnd.id)
            )
            n = int(n or 0)
            if best is None:
                best = rnd
                best_n = n
            elif n > best_n:
                best = rnd
                best_n = n
            elif n == best_n and rnd.started_at > best.started_at:
                best = rnd
        return best

    async def get_player_shot_detail(
        self, session: AsyncSession, tournament_id: int, player_id: int
    ) -> TournamentPlayerShotDetailRead:
        t = await session.execute(
            select(Tournament)
            .where(Tournament.id == tournament_id)
            .options(selectinload(Tournament.course))
        )
        tournament = t.scalar_one_or_none()
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")

        player = await session.get(Player, player_id)
        if not player:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

        tp = await session.scalar(
            select(TournamentParticipant).where(
                TournamentParticipant.tournament_id == tournament_id,
                TournamentParticipant.player_id == player_id,
            )
        )
        if not tp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player is not a participant in this tournament",
            )

        rnd = await self._pick_round_for_tournament_player(session, tournament, player_id)
        note = (
            "Shots from the Round on this course whose start date (UTC) matches the tournament play date. "
            "If you record only HoleScore strokes on the tournament scorecard without a tracked Round, "
            "this list will be empty — use the leaderboard for gross vs par."
        )
        if not rnd:
            return TournamentPlayerShotDetailRead(
                tournament_id=tournament_id,
                player_id=player_id,
                player_name=player.name,
                matched_round_id=None,
                match_note=note + " No matching round was found.",
                holes=[],
            )

        sh = await session.execute(
            select(Shot)
            .where(Shot.round_id == rnd.id)
            .options(selectinload(Shot.hole))
            .order_by(Shot.shot_at, Shot.id)
        )
        shots = list(sh.scalars().all())
        by_num: dict[int, list[Shot]] = defaultdict(list)
        for s in shots:
            if s.hole:
                by_num[s.hole.number].append(s)

        holes_out: list[TournamentHoleShotDetail] = []
        for hole_number in sorted(by_num.keys()):
            group = sorted(by_num[hole_number], key=lambda x: (x.shot_at, x.id))
            par = group[0].hole.par if group[0].hole else 4
            stroke_count = len(group)
            items = [
                TournamentShotDetailItem(
                    shot_id=s.id,
                    order=i,
                    distance_m=s.distance,
                    club=s.club or "",
                    x=s.x,
                    y=s.y,
                )
                for i, s in enumerate(group, start=1)
            ]
            holes_out.append(
                TournamentHoleShotDetail(
                    hole_number=hole_number,
                    par=par,
                    stroke_count=stroke_count,
                    to_par=stroke_count - par,
                    shots=items,
                )
            )

        return TournamentPlayerShotDetailRead(
            tournament_id=tournament_id,
            player_id=player_id,
            player_name=player.name,
            matched_round_id=rnd.id,
            match_note=note,
            holes=holes_out,
        )


tournament_service = TournamentService()
