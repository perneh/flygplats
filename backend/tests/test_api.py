"""
Functional-style API tests: each test describes an outcome a user or integrator cares about,
not implementation details. Steps use `api_actions` helpers so the story stays visible.

Run:  python -m pytest backend/tests -v
"""

from datetime import date, datetime

import pytest
from golf_test_support import assert_shot_equals, assert_status_ok

from tests.support.api_actions import (
    add_course,
    add_hole_to_course,
    add_player,
    create_round_for_player_on_course,
    delete_player,
    filter_rounds_occuring_on_calendar_day,
    get_health_status,
    get_player_data,
    get_player_results_and_measurements_for_course_on_day,
    http_get,
    http_post,
    list_rounds_for_player_on_course,
    list_shot_measurements_for_round,
    list_shot_measurements_for_round_and_hole,
    record_shot_measurement,
    update_player_name,
)


# --- Service health ---


@pytest.mark.asyncio
async def test_service_reports_ready_for_use(api_host, api_port):
    """The API exposes a simple health check for monitoring and load balancers."""
    payload = await get_health_status(api_host, api_port)
    assert payload.get("status") == "ok"


# --- Players (identity / CRUD as one user journey) ---


@pytest.mark.asyncio
async def test_player_can_register_view_rename_and_be_removed(api_host, api_port):
    """
    A player can be created, inspected, renamed, deleted, and then no longer exists.
    """
    player_id = await add_player(api_host, api_port, "Alice")

    profile = await get_player_data(api_host, api_port, player_id)
    assert profile["name"] == "Alice"

    await update_player_name(api_host, api_port, player_id, "Alice B")
    profile = await get_player_data(api_host, api_port, player_id)
    assert profile["name"] == "Alice B"

    await delete_player(api_host, api_port, player_id)

    r = await http_get(api_host, api_port, f"/api/v1/players/{player_id}")
    assert r.status_code == 404


# --- Rounds & shots (golf domain flow) ---


@pytest.mark.asyncio
async def test_coach_can_review_shots_per_hole_or_for_full_round(api_host, api_port):
    """
    During a round, shots are stored per hole; the API can list shots for one hole
    or for the entire round.
    """
    player_id = await add_player(api_host, api_port, "P")
    course_id = await add_course(api_host, api_port, "C")
    hole1 = await add_hole_to_course(api_host, api_port, course_id, 1, par=4, tee_y=0.0, green_y=0.0)
    hole2 = await add_hole_to_course(
        api_host, api_port, course_id, 2, par=3, tee_y=50.0, green_y=50.0, green_x=100.0
    )
    round_id = await create_round_for_player_on_course(api_host, api_port, player_id, course_id)

    await record_shot_measurement(
        api_host, api_port, round_id, hole1["id"], 1, 2, club="Driver", distance=200.0
    )
    await record_shot_measurement(
        api_host, api_port, round_id, hole2["id"], 3, 4, club="Putter", distance=None
    )

    on_hole_1 = await list_shot_measurements_for_round_and_hole(
        api_host, api_port, round_id, hole1["id"]
    )
    assert len(on_hole_1) == 1
    assert_shot_equals(
        on_hole_1[0],
        {
            "x": 1,
            "y": 2,
            "club": "Driver",
            "distance": 200.0,
            "round_id": round_id,
            "hole_id": hole1["id"],
        },
    )

    all_in_round = await list_shot_measurements_for_round(api_host, api_port, round_id)
    assert len(all_in_round) == 2


@pytest.mark.asyncio
async def test_recording_a_shot_without_club_name_is_accepted(api_host, api_port):
    """Club is optional; an empty label is allowed when the player does not specify one."""
    course_id = await add_course(api_host, api_port, "C2")
    hole_id = (await add_hole_to_course(api_host, api_port, course_id, 1, green_x=1.0, green_y=0.0))[
        "id"
    ]
    player_id = await add_player(api_host, api_port, "Q")
    round_id = await create_round_for_player_on_course(api_host, api_port, player_id, course_id)

    r = await http_post(
        api_host,
        api_port,
        "/api/v1/shots",
        json={
            "round_id": round_id,
            "hole_id": hole_id,
            "x": 0.0,
            "y": 0.0,
            "club": "",
            "distance": None,
        },
    )
    assert_status_ok(r, 201)


@pytest.mark.asyncio
async def test_player_results_and_measurements_for_course_on_calendar_day(api_host, api_port):
    """
    Reporting helper: group shot measurements by round for rounds started on a given day.
    """
    player_id = await add_player(api_host, api_port, "R")
    course_id = await add_course(api_host, api_port, "DayCourse")
    hole = await add_hole_to_course(api_host, api_port, course_id, 1)
    round_id = await create_round_for_player_on_course(api_host, api_port, player_id, course_id)
    await record_shot_measurement(api_host, api_port, round_id, hole["id"], 10.0, 20.0, club="7i")

    rounds = await list_rounds_for_player_on_course(api_host, api_port, player_id, course_id)
    assert len(rounds) == 1
    started = rounds[0]["started_at"]
    if isinstance(started, str):
        s = started.replace("Z", "+00:00") if started.endswith("Z") else started
        calendar_day = datetime.fromisoformat(s).date()
    else:
        calendar_day = date.today()

    report = await get_player_results_and_measurements_for_course_on_day(
        api_host, api_port, player_id, course_id, calendar_day
    )
    assert len(report) == 1
    assert report[0]["round"]["id"] == round_id
    assert len(report[0]["shot_measurements"]) == 1
    assert report[0]["shot_measurements"][0]["club"] == "7i"


def test_filter_rounds_occuring_on_calendar_day_pure():
    """Date filter helper without HTTP (stable for CI)."""
    day = date(2026, 4, 10)
    rounds = [
        {"id": 1, "started_at": "2026-04-10T12:00:00+00:00"},
        {"id": 2, "started_at": "2026-04-09T12:00:00+00:00"},
    ]
    filtered = filter_rounds_occuring_on_calendar_day(rounds, day)
    assert [r["id"] for r in filtered] == [1]
