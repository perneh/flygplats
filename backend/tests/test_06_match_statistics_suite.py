"""
Multi-match suite: ``POST /matches`` (several times), ``GET /players/{id}/performance``,
and ``GET /courses/{id}/statistics``.

Demonstrates how to inspect **per-player** history and **course-level** aggregates after one or
more multi-player matches.
"""

import pytest

from tests.support.api_actions import (
    PREFIX,
    add_course,
    add_hole_to_course,
    add_player,
    get_course_statistics,
    http_get,
    http_post,
)


def _match_payload(course_id: int, p1: int, p2: int, *, second_hole: bool = True) -> dict:
    """Two players; hole 1 always; optional hole 2 for variety."""
    holes = [
        {
            "hole_number": 1,
            "by_player": [
                {
                    "player_id": p1,
                    "shots": [{"x": 0.0, "y": 0.0, "club": "Driver", "distance": 200.0}],
                },
                {
                    "player_id": p2,
                    "shots": [
                        {"x": 1.0, "y": 0.0, "club": "3W", "distance": 180.0},
                        {"x": 2.0, "y": 1.0, "club": "7i", "distance": 40.0},
                    ],
                },
            ],
        },
    ]
    if second_hole:
        holes.append(
            {
                "hole_number": 2,
                "by_player": [
                    {"player_id": p1, "shots": [{"x": 0.0, "y": 0.0, "club": "Putter"}]},
                    {"player_id": p2, "shots": []},
                ],
            }
        )
    return {"course_id": course_id, "player_ids": [p1, p2], "holes": holes}


@pytest.mark.asyncio
async def test_single_match_smoke_then_player_filters(api_host, api_port, api_client):
    """One match → performance + optional course_id / hole_number filters."""
    cid = await add_course(api_host, api_port, "Suite Course A")
    await add_hole_to_course(api_host, api_port, cid, 1, par=4)
    await add_hole_to_course(api_host, api_port, cid, 2, par=3)
    p1 = await add_player(api_host, api_port, "Alpha")
    p2 = await add_player(api_host, api_port, "Bravo")

    r = await http_post(api_host, api_port, f"{PREFIX}/matches", json=_match_payload(cid, p1, p2))
    assert r.status_code == 201, r.text
    # Hole 1: 1 + 2 shots; hole 2: 1 + 0 (p2 has an empty shot list on hole 2) → 4 rows
    assert r.json()["shots_created"] == 4

    perf = (await http_get(api_host, api_port, f"{PREFIX}/players/{p1}/performance")).json()
    assert perf["player_name"] == "Alpha"
    assert len(perf["rounds"]) == 1
    assert len(perf["rounds"][0]["holes"]) == 2

    perf_h1 = (
        await http_get(
            api_host,
            api_port,
            f"{PREFIX}/players/{p2}/performance",
            params=[("hole_number", "1")],
        )
    ).json()
    assert len(perf_h1["rounds"][0]["holes"]) == 1
    assert perf_h1["rounds"][0]["holes"][0]["stroke_count"] == 2

    stats = await get_course_statistics(api_host, api_port, cid)
    assert stats["course_name"] == "Suite Course A"
    assert stats["total_rounds"] == 2
    assert {p["player_name"]: p["total_strokes"] for p in stats["players"]} == {
        "Alpha": 2,
        "Bravo": 2,
    }
    by_hole = {h["hole_number"]: h["total_strokes_recorded"] for h in stats["holes"]}
    assert by_hole[1] == 3
    assert by_hole[2] == 1


@pytest.mark.asyncio
async def test_multi_match_increments_player_rounds_and_course_totals(api_host, api_port, api_client):
    """Two matches on the same course: player performance shows two rounds; course stats sum strokes."""
    cid = await add_course(api_host, api_port, "Suite Course B")
    await add_hole_to_course(api_host, api_port, cid, 1, par=4)
    await add_hole_to_course(api_host, api_port, cid, 2, par=3)
    p1 = await add_player(api_host, api_port, "M1")
    p2 = await add_player(api_host, api_port, "M2")

    r1 = await http_post(api_host, api_port, f"{PREFIX}/matches", json=_match_payload(cid, p1, p2))
    assert r1.status_code == 201
    r2 = await http_post(
        api_host,
        api_port,
        f"{PREFIX}/matches",
        json=_match_payload(cid, p1, p2, second_hole=False),
    )
    assert r2.status_code == 201
    assert r2.json()["shots_created"] == 3

    # Performance lists newest round first; each block’s holes are ordered by hole number.
    for pid, name, older_match_hole1_strokes, newer_match_hole1_strokes in (
        (p1, "M1", 1, 1),
        (p2, "M2", 2, 2),
    ):
        perf = (await http_get(api_host, api_port, f"{PREFIX}/players/{pid}/performance")).json()
        assert perf["player_name"] == name
        assert len(perf["rounds"]) == 2
        assert perf["rounds"][0]["holes"][0]["stroke_count"] == newer_match_hole1_strokes
        assert perf["rounds"][1]["holes"][0]["stroke_count"] == older_match_hole1_strokes

    stats = await get_course_statistics(api_host, api_port, cid)
    assert stats["total_rounds"] == 4
    assert {p["player_name"]: (p["rounds_played"], p["total_strokes"]) for p in stats["players"]} == {
        "M1": (2, 3),
        "M2": (2, 4),
    }
    by_hole = {h["hole_number"]: h["total_strokes_recorded"] for h in stats["holes"]}
    assert by_hole[1] == 3 + 3
    assert by_hole[2] == 1


@pytest.mark.asyncio
async def test_course_statistics_only_includes_that_course(api_host, api_port, api_client):
    """Activity on course C does not appear in statistics for course D."""
    c_other = await add_course(api_host, api_port, "Other Course")
    await add_hole_to_course(api_host, api_port, c_other, 1, par=4)

    c_focus = await add_course(api_host, api_port, "Focus Course")
    await add_hole_to_course(api_host, api_port, c_focus, 1, par=5)

    p1 = await add_player(api_host, api_port, "Solo")
    await http_post(
        api_host,
        api_port,
        f"{PREFIX}/matches",
        json={
            "course_id": c_focus,
            "player_ids": [p1],
            "holes": [
                {
                    "hole_number": 1,
                    "by_player": [
                        {"player_id": p1, "shots": [{"x": 0.0, "y": 0.0, "club": "D"}]},
                    ],
                }
            ],
        },
    )

    st_other = await get_course_statistics(api_host, api_port, c_other)
    assert st_other["total_rounds"] == 0
    assert st_other["players"] == []
    assert st_other["holes"] == []

    st_focus = await get_course_statistics(api_host, api_port, c_focus)
    assert st_focus["total_rounds"] == 1
    assert st_focus["players"][0]["total_strokes"] == 1
    assert st_focus["holes"][0]["total_strokes_recorded"] == 1
