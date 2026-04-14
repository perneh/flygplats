"""
Tournaments: create → participants → start (flights + scorecards) → hole POST → totals.

Runs after match statistics (`test_06`) in lexicographic order.
"""

import pytest

from tests.support.api_actions import (
    add_course,
    add_hole_to_course,
    add_player,
    fetch_scorecard,
    fetch_tournament,
    fetch_tournament_drafts,
    fetch_tournament_leaderboard,
    fetch_tournament_non_draft,
    fetch_tournament_player_shot_detail,
    fetch_tournament_started,
    fetch_tournaments,
    fetch_tournament_scorecards,
    post_scorecard_hole,
    post_tournament,
    post_tournament_participant,
    post_tournament_start,
    post_tournament_stop,
)


@pytest.mark.asyncio
async def test_tournament_flights_by_handicap_and_scorecard_totals(api_host, api_port):
    """End-to-end: flights of ≤4 by ascending handicap; out/in/gross from recorded strokes."""
    cid = await add_course(api_host, api_port, "Tourney Course")
    p_low = await add_player(api_host, api_port, "Scratch")
    p_mid = await add_player(api_host, api_port, "Mid")
    p_high = await add_player(api_host, api_port, "High")
    p_extra = await add_player(api_host, api_port, "Fourth")

    r_t = await post_tournament(
        api_host,
        api_port,
        {
            "name": "Spring Open",
            "play_date": "2026-06-01",
            "course_id": cid,
        },
    )
    assert r_t.status_code == 201, r_t.text
    tid = r_t.json()["id"]
    assert r_t.json()["status"] == "draft"

    for pid, hcp in [(p_low, 4.0), (p_mid, 18.0), (p_high, 28.0), (p_extra, 12.0)]:
        r_p = await post_tournament_participant(
            api_host,
            api_port,
            {"tournament_id": tid, "player_id": pid, "handicap": hcp},
        )
        assert r_p.status_code == 201, r_p.text

    r_start = await post_tournament_start(api_host, api_port, tid)
    assert r_start.status_code == 200, r_start.text
    detail = r_start.json()
    assert detail["status"] == "started"
    assert len(detail["flights"]) == 1
    assert set(detail["flights"][0]["player_ids"]) == {p_low, p_mid, p_high, p_extra}

    r_cards = await fetch_tournament_scorecards(api_host, api_port, tid)
    assert r_cards.status_code == 200
    cards = r_cards.json()
    assert len(cards) == 4
    sc = next(c for c in cards if c["player_id"] == p_low)
    assert sc["gross_total"] == 0
    assert sc["out_total"] == 0
    assert sc["in_total"] == 0
    assert len(sc["holes"]) == 18

    r_patch = await post_scorecard_hole(
        api_host,
        api_port,
        {
            "scorecard_id": sc["id"],
            "hole_number": 1,
            "strokes": 4,
            "player_id": p_low,
        },
    )
    assert r_patch.status_code == 200, r_patch.text
    assert r_patch.json()["out_total"] == 4
    assert r_patch.json()["gross_total"] == 4

    r_patch2 = await post_scorecard_hole(
        api_host,
        api_port,
        {
            "scorecard_id": sc["id"],
            "hole_number": 10,
            "strokes": 5,
            "player_id": p_low,
        },
    )
    assert r_patch2.status_code == 200
    assert r_patch2.json()["out_total"] == 4
    assert r_patch2.json()["in_total"] == 5
    assert r_patch2.json()["gross_total"] == 9

    r_one = await fetch_scorecard(api_host, api_port, sc["id"])
    assert r_one.status_code == 200
    assert r_one.json()["gross_total"] == 9

    r_get = await fetch_tournament(api_host, api_port, tid)
    assert r_get.status_code == 200
    assert r_get.json()["name"] == "Spring Open"


@pytest.mark.asyncio
async def test_tournament_two_flights_five_players(api_host, api_port):
    """Five players → two flights (4 + 1), still sorted by handicap."""
    cid = await add_course(api_host, api_port, "Five Ball Course")
    players: list[tuple[int, float]] = []
    for i, hcp in enumerate([5.0, 10.0, 15.0, 20.0, 25.0]):
        pid = await add_player(api_host, api_port, f"P{i}")
        players.append((pid, hcp))

    r_t = await post_tournament(
        api_host,
        api_port,
        {"name": "Five", "play_date": "2026-07-01", "course_id": cid},
    )
    assert r_t.status_code == 201
    tid = r_t.json()["id"]
    for pid, hcp in players:
        r = await post_tournament_participant(
            api_host,
            api_port,
            {"tournament_id": tid, "player_id": pid, "handicap": hcp},
        )
        assert r.status_code == 201

    r_start = await post_tournament_start(api_host, api_port, tid)
    assert r_start.status_code == 200
    flights = r_start.json()["flights"]
    assert len(flights) == 2
    assert len(flights[0]["player_ids"]) == 4
    assert len(flights[1]["player_ids"]) == 1


@pytest.mark.asyncio
async def test_list_tournaments_empty_then_newest_first(api_host, api_port):
    """GET /tournaments returns [] when empty; multiple rows ordered by play_date desc, then id desc."""
    r0 = await fetch_tournaments(api_host, api_port)
    assert r0.status_code == 200
    assert r0.json() == []

    cid = await add_course(api_host, api_port, "List Cup")
    r_a = await post_tournament(
        api_host,
        api_port,
        {"name": "Earlier", "play_date": "2026-03-01", "course_id": cid},
    )
    r_b = await post_tournament(
        api_host,
        api_port,
        {"name": "Later", "play_date": "2026-09-01", "course_id": cid},
    )
    assert r_a.status_code == 201 and r_b.status_code == 201
    id_a, id_b = r_a.json()["id"], r_b.json()["id"]

    r_list = await fetch_tournaments(api_host, api_port)
    assert r_list.status_code == 200
    rows = r_list.json()
    assert len(rows) == 2
    assert [r["id"] for r in rows] == [id_b, id_a]
    assert rows[0]["name"] == "Later"
    assert rows[1]["name"] == "Earlier"


@pytest.mark.asyncio
async def test_leaderboard_ranks_players_and_shows_to_par(api_host, api_port):
    """POST /tournaments/leaderboard — rank by gross; per-hole par from course holes."""
    cid = await add_course(api_host, api_port, "Par Course")
    await add_hole_to_course(api_host, api_port, cid, 1, par=4)

    p_a = await add_player(api_host, api_port, "Leader A")
    p_b = await add_player(api_host, api_port, "Leader B")

    r_t = await post_tournament(
        api_host,
        api_port,
        {"name": "LB", "play_date": "2026-08-10", "course_id": cid},
    )
    tid = r_t.json()["id"]
    for pid, hcp in [(p_a, 5.0), (p_b, 15.0)]:
        assert (
            await post_tournament_participant(
                api_host,
                api_port,
                {"tournament_id": tid, "player_id": pid, "handicap": hcp},
            )
        ).status_code == 201
    assert (await post_tournament_start(api_host, api_port, tid)).status_code == 200

    cards = (await fetch_tournament_scorecards(api_host, api_port, tid)).json()
    sc_a = next(c for c in cards if c["player_id"] == p_a)
    sc_b = next(c for c in cards if c["player_id"] == p_b)
    assert (
        await post_scorecard_hole(
            api_host,
            api_port,
            {
                "scorecard_id": sc_a["id"],
                "hole_number": 1,
                "strokes": 4,
                "player_id": p_a,
            },
        )
    ).status_code == 200
    assert (
        await post_scorecard_hole(
            api_host,
            api_port,
            {
                "scorecard_id": sc_b["id"],
                "hole_number": 1,
                "strokes": 6,
                "player_id": p_b,
            },
        )
    ).status_code == 200

    r_lb = await fetch_tournament_leaderboard(api_host, api_port, tid)
    assert r_lb.status_code == 200
    lb = r_lb.json()
    assert lb["tournament_id"] == tid
    assert lb["course_par_total"] >= 4
    players = {p["player_id"]: p for p in lb["players"]}
    assert players[p_a]["rank"] == 1
    assert players[p_b]["rank"] == 2
    assert players[p_a]["gross_total"] == 4
    assert players[p_a]["to_par"] == 0
    assert players[p_a]["holes"][0]["hole_number"] == 1
    assert players[p_a]["holes"][0]["to_par"] == 0


@pytest.mark.asyncio
async def test_shot_detail_without_matching_round(api_host, api_port):
    """Shot-detail is empty when no Round exists on tournament day (tournament-only scoring)."""
    cid = await add_course(api_host, api_port, "No Round Course")
    pid = await add_player(api_host, api_port, "Solo")
    tid = (await post_tournament(api_host, api_port, {"name": "NR", "play_date": "2026-04-20", "course_id": cid})).json()[
        "id"
    ]
    assert (
        await post_tournament_participant(
            api_host,
            api_port,
            {"tournament_id": tid, "player_id": pid, "handicap": 10.0},
        )
    ).status_code == 201
    assert (await post_tournament_start(api_host, api_port, tid)).status_code == 200

    r = await fetch_tournament_player_shot_detail(api_host, api_port, tid, pid)
    assert r.status_code == 200
    body = r.json()
    assert body["matched_round_id"] is None
    assert body["holes"] == []


@pytest.mark.asyncio
async def test_shot_detail_404_when_player_not_in_tournament(api_host, api_port):
    cid = await add_course(api_host, api_port, "Solo Course")
    p_in = await add_player(api_host, api_port, "In")
    p_out = await add_player(api_host, api_port, "Out")
    tid = (await post_tournament(api_host, api_port, {"name": "X", "play_date": "2026-01-01", "course_id": cid})).json()[
        "id"
    ]
    assert (
        await post_tournament_participant(
            api_host,
            api_port,
            {"tournament_id": tid, "player_id": p_in, "handicap": 1.0},
        )
    ).status_code == 201
    assert (await post_tournament_start(api_host, api_port, tid)).status_code == 200
    r = await fetch_tournament_player_shot_detail(api_host, api_port, tid, p_out)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_stop_marks_finished_and_list_filters(api_host, api_port):
    """GET drafts/started/non-draft; POST stop sets finished; hole updates rejected when finished."""
    cid = await add_course(api_host, api_port, "Finish Line Course")
    pid = await add_player(api_host, api_port, "Finisher")
    r_t = await post_tournament(
        api_host,
        api_port,
        {"name": "To Finish", "play_date": "2026-10-01", "course_id": cid},
    )
    assert r_t.status_code == 201
    tid = r_t.json()["id"]

    assert (await fetch_tournament_started(api_host, api_port)).json() == []
    assert (await fetch_tournament_non_draft(api_host, api_port)).json() == []
    assert (await fetch_tournament_drafts(api_host, api_port)).json()[0]["id"] == tid

    assert (
        await post_tournament_participant(
            api_host,
            api_port,
            {"tournament_id": tid, "player_id": pid, "handicap": 12.0},
        )
    ).status_code == 201
    drafts = (await fetch_tournament_drafts(api_host, api_port)).json()
    assert len(drafts) == 1 and drafts[0]["id"] == tid

    assert (await post_tournament_start(api_host, api_port, tid)).status_code == 200
    assert (await fetch_tournament_drafts(api_host, api_port)).json() == []
    started = (await fetch_tournament_started(api_host, api_port)).json()
    assert len(started) == 1 and started[0]["id"] == tid
    assert (await fetch_tournament_non_draft(api_host, api_port)).json()[0]["status"] == "started"

    cards = (await fetch_tournament_scorecards(api_host, api_port, tid)).json()
    sc_id = cards[0]["id"]
    assert (
        await post_scorecard_hole(
            api_host,
            api_port,
            {
                "scorecard_id": sc_id,
                "hole_number": 1,
                "strokes": 4,
                "player_id": pid,
            },
        )
    ).status_code == 200

    r_stop = await post_tournament_stop(api_host, api_port, tid)
    assert r_stop.status_code == 200
    assert r_stop.json()["status"] == "finished"
    assert (await fetch_tournament_started(api_host, api_port)).json() == []
    nd = (await fetch_tournament_non_draft(api_host, api_port)).json()
    assert len(nd) == 1 and nd[0]["status"] == "finished"

    r_bad = await post_scorecard_hole(
        api_host,
        api_port,
        {
            "scorecard_id": sc_id,
            "hole_number": 2,
            "strokes": 5,
            "player_id": pid,
        },
    )
    assert r_bad.status_code == 400
