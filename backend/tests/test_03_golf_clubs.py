"""
Golf club catalog: only public API routes under ``/api/v1/golf-clubs`` (no ``/dev/*``).

Uses ``httpx`` via ``tests.support.api_actions`` — same surface a client app would call.

Remote API runs apply ``factory-default`` before each test (bundled ``golf_clubs.json`` restored).
In-process tests use an empty SQLite DB unless you add seeding elsewhere.
"""

import pytest

from tests.support.api_actions import (
    fetch_golf_club,
    fetch_golf_clubs,
    patch_golf_club,
    post_golf_club,
)
from tests.support.bundled_init_counts import GOLF_CLUBS as _BUNDLED_CLUBS

# Does not collide with catalog ids 1–15 in ``golf_clubs.json``.
_EXTRA_CLUB_BODY = {
    "catalog_id": 9999,
    "name": "Extra Test Club",
    "type": "Iron",
    "loft_deg": 30.0,
    "difficulty": "Low",
    "max_distance_m": 50,
    "avg_distance_m": 40,
    "player_level": ["Beginner"],
}


@pytest.mark.asyncio
async def test_list_golf_clubs_matches_mode(
    api_host, api_port, api_client, expect_bundled_init_data
):
    r = await fetch_golf_clubs(api_host, api_port)
    assert r.status_code == 200
    body = r.json()
    if expect_bundled_init_data:
        assert len(body) == _BUNDLED_CLUBS
        assert body[0]["name"] == "Driver"
    else:
        assert body == []


@pytest.mark.asyncio
async def test_create_list_get_patch_and_missing_returns_404(
    api_host, api_port, api_client, expect_bundled_init_data
):
    created = await post_golf_club(api_host, api_port, _EXTRA_CLUB_BODY)
    assert created.status_code == 201
    c0 = created.json()
    assert c0["name"] == "Extra Test Club"
    assert c0["type"] == "Iron"

    listed = await fetch_golf_clubs(api_host, api_port)
    assert listed.status_code == 200
    clubs = listed.json()
    assert len(clubs) == (_BUNDLED_CLUBS + 1 if expect_bundled_init_data else 1)
    club_id = c0["id"]

    one = await fetch_golf_club(api_host, api_port, club_id)
    assert one.status_code == 200
    assert one.json()["catalog_id"] == 9999

    patched = await patch_golf_club(
        api_host, api_port, club_id, {"avg_distance_m": 41, "type": "Iron"}
    )
    assert patched.status_code == 200
    p = patched.json()
    assert p["avg_distance_m"] == 41
    assert p["type"] == "Iron"

    missing = await fetch_golf_club(api_host, api_port, 99999)
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_patch_golf_club_player_level(
    api_host, api_port, api_client, expect_bundled_init_data
):
    if expect_bundled_init_data:
        listed = await fetch_golf_clubs(api_host, api_port)
        driver = next(c for c in listed.json() if c["name"] == "Driver")
        club_id = driver["id"]
    else:
        r = await post_golf_club(api_host, api_port, _EXTRA_CLUB_BODY)
        assert r.status_code == 201
        club_id = r.json()["id"]

    r2 = await patch_golf_club(
        api_host, api_port, club_id, {"player_level": ["Beginner", "Intermediate"]}
    )
    assert r2.status_code == 200
    assert r2.json()["player_level"] == ["Beginner", "Intermediate"]
