"""
Load-style API scenario: reset data once at the start, then simulate many players and rounds.

**Requires a real HTTP API** — pass ``--api-base-url`` or ``PYTEST_API_BASE_URL`` (or
``--api-host`` / ``--api-port``). Running this file without that **fails on purpose** so you
do not get a false green run against an in-memory DB that never touches Postgres.

Uses POST /api/v1/dev/factory-default to wipe the database **before** the scenario only.
There is **no** teardown cleanup: the test does not delete data at the end.

**Inspect results in Postgres** after a successful run (same URL you used for pytest):

1. Rebuild the backend image so it includes ``app/routers/dev.py`` (factory-default).
2. Start the stack: ``docker compose -f infra/docker-compose.yml up -d db backend``
3. **On your host machine** (pytest not inside Docker), if the API is on localhost::

     python -m pytest backend/tests/test_07_load_scenario.py -v --api-base-url=http://127.0.0.1:8000

   **Inside the ``test-runner`` container**, ``127.0.0.1`` is the container itself — use the Compose
   **service name** (same network as ``backend``)::

     --api-base-url=http://backend:8000

   Or to reach a server published on the **host** (Docker Desktop): ``http://host.docker.internal:8000``.

The default ``test-runner`` image ``CMD`` excludes this file so one-shot ``docker compose run test-runner``
stays green without a live backend; run this file explicitly as above.
"""

from __future__ import annotations

import pytest

from tests.support.api_actions import (
    add_course,
    add_hole_to_course,
    add_player,
    create_round_for_player_on_course,
    factory_default,
    list_all_courses,
    list_all_players,
    list_all_rounds,
    list_all_shots,
    list_holes_for_course,
    record_shot_measurement,
)
from tests.support.bundled_init_counts import GOLF_COURSES as _BUNDLED_COURSES

pytestmark = pytest.mark.usefixtures("require_external_api_base_url")

NUM_PLAYERS = 10
HOLES_PER_COURSE = 18


@pytest.mark.asyncio
async def test_ten_players_each_full_round_on_ten_courses(api_host, api_port):
    """
    After a factory reset, 10 players each play one round on 10 different courses,
    completing every hole (one shot recorded per hole).

    No cleanup at the end — data remains in the API's database (requires external API; see module docstring).
    """
    await factory_default(api_host, api_port)
    assert (await list_all_players(api_host, api_port)) == []
    assert len(await list_all_courses(api_host, api_port)) == _BUNDLED_COURSES
    assert (await list_all_shots(api_host, api_port)) == []

    course_ids: list[int] = []
    for i in range(NUM_PLAYERS):
        cid = await add_course(api_host, api_port, f"LoadTest Course {i + 1}")
        course_ids.append(cid)
        for hole_num in range(1, HOLES_PER_COURSE + 1):
            par = 3 + (hole_num % 3)
            await add_hole_to_course(
                api_host,
                api_port,
                cid,
                hole_num,
                par=par,
                tee_x=float(hole_num),
                tee_y=0.0,
                green_x=float(hole_num) + 50.0,
                green_y=10.0,
            )

    player_ids: list[int] = []
    for i in range(NUM_PLAYERS):
        pid = await add_player(api_host, api_port, f"LoadTest Player {i + 1}")
        player_ids.append(pid)

    for i in range(NUM_PLAYERS):
        round_id = await create_round_for_player_on_course(
            api_host, api_port, player_ids[i], course_ids[i]
        )
        holes = await list_holes_for_course(api_host, api_port, course_ids[i])
        assert len(holes) == HOLES_PER_COURSE
        holes_sorted = sorted(holes, key=lambda h: h["hole"])
        for hole in holes_sorted:
            await record_shot_measurement(
                api_host,
                api_port,
                round_id,
                hole["id"],
                12.0,
                34.0,
                club="7i",
                distance=150.0,
            )

    players = await list_all_players(api_host, api_port)
    courses = await list_all_courses(api_host, api_port)
    rounds = await list_all_rounds(api_host, api_port)
    shots = await list_all_shots(api_host, api_port)

    assert len(players) == NUM_PLAYERS
    assert len(courses) == _BUNDLED_COURSES + NUM_PLAYERS
    assert len(rounds) == NUM_PLAYERS
    assert len(shots) == NUM_PLAYERS * HOLES_PER_COURSE
