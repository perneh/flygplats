"""
Golf club catalog: only public API routes under ``/api/v1/golf-clubs`` (no ``/dev/*``).

Uses ``httpx`` via ``tests.support.api_actions`` — same surface a client app would call.
"""

import pytest

from tests.support.api_actions import PREFIX, http_get, http_patch, http_post

_DRIVER_BODY = {
    "catalog_id": 1,
    "name": "Driver",
    "type": "Wood",
    "loft_deg": 10.5,
    "difficulty": "High",
    "max_distance_m": 270,
    "avg_distance_m": 230,
    "player_level": ["Intermediate", "Pro"],
}


@pytest.mark.asyncio
async def test_list_golf_clubs_empty_catalog(api_host, api_port, api_client, test_db):
    assert test_db is not None
    r = await http_get(api_host, api_port, f"{PREFIX}/golf-clubs")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_list_get_patch_and_missing_returns_404(api_host, api_port, test_db):
    assert test_db is not None
    created = await http_post(api_host, api_port, f"{PREFIX}/golf-clubs", json=_DRIVER_BODY)
    assert created.status_code == 201
    c0 = created.json()
    assert c0["name"] == "Driver"
    assert c0["type"] == "Wood"
    assert c0["player_level"] == ["Intermediate", "Pro"]

    listed = await http_get(api_host, api_port, f"{PREFIX}/golf-clubs")
    assert listed.status_code == 200
    clubs = listed.json()
    assert len(clubs) == 1
    club_id = clubs[0]["id"]

    one = await http_get(api_host, api_port, f"{PREFIX}/golf-clubs/{club_id}")
    assert one.status_code == 200
    assert one.json()["catalog_id"] == 1

    patched = await http_patch(
        api_host,
        api_port,
        f"{PREFIX}/golf-clubs/{club_id}",
        json={"avg_distance_m": 225, "type": "Wood"},
    )
    assert patched.status_code == 200
    p = patched.json()
    assert p["avg_distance_m"] == 225
    assert p["type"] == "Wood"

    missing = await http_get(api_host, api_port, f"{PREFIX}/golf-clubs/99999")
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_patch_golf_club_player_level(api_host, api_port, test_db):
    assert test_db is not None
    r = await http_post(api_host, api_port, f"{PREFIX}/golf-clubs", json=_DRIVER_BODY)
    assert r.status_code == 201
    club_id = r.json()["id"]

    r2 = await http_patch(
        api_host,
        api_port,
        f"{PREFIX}/golf-clubs/{club_id}",
        json={"player_level": ["Beginner", "Intermediate"]},
    )
    assert r2.status_code == 200
    assert r2.json()["player_level"] == ["Beginner", "Intermediate"]
