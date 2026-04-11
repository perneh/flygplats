"""
Test helpers: one function = one API action or a small reporting composition.

Each async helper takes ``(host, port, ...)`` first so tests read like integration calls
against a real server; ``host`` / ``port`` must match the ``api_host`` / ``api_port``
fixtures (the bound ``httpx.AsyncClient`` comes from the ``api_client`` fixture).

Naming: verb + object (e.g. list_all_players, get_player_data, record_shot_measurement).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from httpx import AsyncClient, Response

from tests.support.api_context import assert_host_port_matches, require_client

PREFIX = "/api/v1"


def _client(host: str, port: int) -> AsyncClient:
    assert_host_port_matches(host, port)
    return require_client()


# --- Raw HTTP (when a test needs method/path directly) ---


async def http_get(host: str, port: int, path: str, **kwargs: Any) -> Response:
    return await _client(host, port).get(path, **kwargs)


async def http_post(host: str, port: int, path: str, **kwargs: Any) -> Response:
    return await _client(host, port).post(path, **kwargs)


async def http_patch(host: str, port: int, path: str, **kwargs: Any) -> Response:
    return await _client(host, port).patch(path, **kwargs)


async def http_delete(host: str, port: int, path: str, **kwargs: Any) -> Response:
    return await _client(host, port).delete(path, **kwargs)


# --- Health ---


async def get_health_status(host: str, port: int) -> dict[str, Any]:
    client = _client(host, port)
    r = await client.get("/health")
    assert r.status_code == 200, r.text
    return r.json()


# --- Dev / factory ---


async def factory_default(host: str, port: int) -> dict[str, Any]:
    """POST /dev/factory-default — delete all domain data."""
    client = _client(host, port)
    r = await client.post(f"{PREFIX}/dev/factory-default")
    assert r.status_code == 200, r.text
    return r.json()


async def list_all_shots(host: str, port: int) -> list[dict[str, Any]]:
    """GET /shots with no filters (all shots in the database)."""
    client = _client(host, port)
    r = await client.get(f"{PREFIX}/shots")
    assert r.status_code == 200, r.text
    return r.json()


async def list_all_rounds(host: str, port: int) -> list[dict[str, Any]]:
    """GET /rounds with no filters."""
    client = _client(host, port)
    r = await client.get(f"{PREFIX}/rounds")
    assert r.status_code == 200, r.text
    return r.json()


# --- Players ---


async def list_all_players(host: str, port: int) -> list[dict[str, Any]]:
    client = _client(host, port)
    r = await client.get(f"{PREFIX}/players")
    assert r.status_code == 200, r.text
    return r.json()


async def add_player(host: str, port: int, name: str) -> int:
    client = _client(host, port)
    r = await client.post(f"{PREFIX}/players", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def get_player_data(host: str, port: int, player_id: int) -> dict[str, Any]:
    client = _client(host, port)
    r = await client.get(f"{PREFIX}/players/{player_id}")
    assert r.status_code == 200, r.text
    return r.json()


async def update_player_name(host: str, port: int, player_id: int, new_name: str) -> None:
    client = _client(host, port)
    r = await client.patch(f"{PREFIX}/players/{player_id}", json={"name": new_name})
    assert r.status_code == 200, r.text


async def delete_player(host: str, port: int, player_id: int) -> None:
    client = _client(host, port)
    r = await client.delete(f"{PREFIX}/players/{player_id}")
    assert r.status_code == 204, r.text


# --- Courses & holes ---


async def list_all_courses(host: str, port: int) -> list[dict[str, Any]]:
    client = _client(host, port)
    r = await client.get(f"{PREFIX}/courses")
    assert r.status_code == 200, r.text
    return r.json()


async def add_course(host: str, port: int, name: str, *, description: str | None = None) -> int:
    client = _client(host, port)
    body: dict[str, Any] = {"name": name}
    if description is not None:
        body["description"] = description
    r = await client.post(f"{PREFIX}/courses", json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def list_holes_for_course(host: str, port: int, course_id: int) -> list[dict[str, Any]]:
    client = _client(host, port)
    r = await client.get(f"{PREFIX}/holes", params={"course_id": course_id})
    assert r.status_code == 200, r.text
    return r.json()


async def add_hole_to_course(
    host: str,
    port: int,
    course_id: int,
    number: int,
    *,
    par: int = 4,
    tee_x: float = 0.0,
    tee_y: float = 0.0,
    green_x: float = 100.0,
    green_y: float = 0.0,
) -> dict[str, Any]:
    client = _client(host, port)
    r = await client.post(
        f"{PREFIX}/holes",
        json={
            "course_id": course_id,
            "number": number,
            "par": par,
            "tee_x": tee_x,
            "tee_y": tee_y,
            "green_x": green_x,
            "green_y": green_y,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


# --- Rounds ---


async def list_rounds_for_player_on_course(
    host: str, port: int, player_id: int, course_id: int
) -> list[dict[str, Any]]:
    """All rounds that match both player and course (GET /rounds?player_id=&course_id=)."""
    client = _client(host, port)
    r = await client.get(
        f"{PREFIX}/rounds",
        params={"player_id": player_id, "course_id": course_id},
    )
    assert r.status_code == 200, r.text
    return r.json()


async def list_rounds_for_player(host: str, port: int, player_id: int) -> list[dict[str, Any]]:
    client = _client(host, port)
    r = await client.get(f"{PREFIX}/rounds", params={"player_id": player_id})
    assert r.status_code == 200, r.text
    return r.json()


async def list_rounds_for_course(host: str, port: int, course_id: int) -> list[dict[str, Any]]:
    client = _client(host, port)
    r = await client.get(f"{PREFIX}/rounds", params={"course_id": course_id})
    assert r.status_code == 200, r.text
    return r.json()


async def create_round_for_player_on_course(
    host: str, port: int, player_id: int, course_id: int
) -> int:
    client = _client(host, port)
    r = await client.post(
        f"{PREFIX}/rounds",
        json={"player_id": player_id, "course_id": course_id},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _parse_started_at(round_payload: dict[str, Any]) -> datetime | None:
    raw = round_payload.get("started_at")
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, str):
        s = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None
    return None


def filter_rounds_occuring_on_calendar_day(
    rounds: list[dict[str, Any]], day: date
) -> list[dict[str, Any]]:
    """
    Pure filter: keep rounds whose started_at falls on the given local/calendar day
    (date part only; useful until the API exposes a server-side date filter).
    """
    out: list[dict[str, Any]] = []
    for rnd in rounds:
        dt = _parse_started_at(rnd)
        if dt is not None and dt.date() == day:
            out.append(rnd)
    return out


async def get_player_results_and_measurements_for_course_on_day(
    host: str,
    port: int,
    player_id: int,
    course_id: int,
    day: date,
) -> list[dict[str, Any]]:
    """
    For reporting / UI tests: rounds on that course for that player, started on `day`,
    each with all shot measurements for that round.

    Returns a list of:
      {"round": <round json>, "shot_measurements": [ shot json, ... ]}
    """
    rounds = await list_rounds_for_player_on_course(host, port, player_id, course_id)
    rounds_today = filter_rounds_occuring_on_calendar_day(rounds, day)
    result: list[dict[str, Any]] = []
    for rnd in rounds_today:
        rid = rnd["id"]
        shots = await list_shot_measurements_for_round(host, port, rid)
        result.append({"round": rnd, "shot_measurements": shots})
    return result


# --- Shots (measurements) ---


async def record_shot_measurement(
    host: str,
    port: int,
    round_id: int,
    hole_id: int,
    x: float,
    y: float,
    *,
    club: str = "",
    distance: float | None = None,
) -> dict[str, Any]:
    client = _client(host, port)
    r = await client.post(
        f"{PREFIX}/shots",
        json={
            "round_id": round_id,
            "hole_id": hole_id,
            "x": x,
            "y": y,
            "club": club,
            "distance": distance,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


async def list_shot_measurements_for_round_and_hole(
    host: str, port: int, round_id: int, hole_id: int
) -> list[dict[str, Any]]:
    client = _client(host, port)
    r = await client.get(f"{PREFIX}/rounds/{round_id}/shots", params={"hole_id": hole_id})
    assert r.status_code == 200, r.text
    return r.json()


async def list_shot_measurements_for_round(host: str, port: int, round_id: int) -> list[dict[str, Any]]:
    client = _client(host, port)
    r = await client.get(f"{PREFIX}/shots", params={"round_id": round_id})
    assert r.status_code == 200, r.text
    return r.json()
