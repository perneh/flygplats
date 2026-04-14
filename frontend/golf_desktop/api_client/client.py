"""Async HTTP client for the Golf API — easy to mock in tests."""

from __future__ import annotations

import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)


class GolfApiError(Exception):
    """Raised when the API returns an error response; message is usually FastAPI ``detail``."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _detail_from_error_response(response: httpx.Response) -> str:
    """Turn FastAPI JSON ``{detail: ...}`` (or plain text) into a short user-facing string."""
    try:
        data = response.json()
    except Exception:
        text = (response.text or "").strip()
        if text:
            return text[:2000] + ("…" if len(text) > 2000 else "")
        return f"HTTP {response.status_code} {response.reason_phrase}"

    if isinstance(data, dict) and "detail" in data:
        d = data["detail"]
        if isinstance(d, str):
            return d
        if isinstance(d, list) and d:
            parts: list[str] = []
            for item in d:
                if isinstance(item, dict) and "msg" in item:
                    parts.append(str(item["msg"]))
                else:
                    parts.append(str(item))
            return "; ".join(parts)
    return str(data)


class GolfApiClient:
    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self._base = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base, timeout=timeout)
        log.info("GolfApiClient initialized (base_url=%s)", self._base)

    @property
    def base_url(self) -> str:
        return self._base

    async def aclose(self) -> None:
        log.debug("Closing GolfApiClient HTTP session")
        await self._client.aclose()

    async def _get_json(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        extra = f" params={params!r}" if params else ""
        log.info("HTTP GET %s%s", path, extra)
        try:
            r = await self._client.get(path, params=params)
        except httpx.HTTPError:
            log.exception("HTTP GET %s failed (network/transport)", path)
            raise
        if r.status_code >= 400:
            msg = _detail_from_error_response(r)
            log.warning("HTTP GET %s -> %s: %s", path, r.status_code, msg)
            raise GolfApiError(msg, status_code=r.status_code)
        log.debug("HTTP GET %s -> %s", path, r.status_code)
        return r.json()

    async def _post_json(self, path: str, *, json: dict[str, Any] | None = None) -> Any:
        log.info("HTTP POST %s", path)
        if log.isEnabledFor(logging.DEBUG) and json is not None:
            log.debug("HTTP POST %s body=%s", path, json)
        try:
            r = await self._client.post(path, json=json)
        except httpx.HTTPError:
            log.exception("HTTP POST %s failed (network/transport)", path)
            raise
        if r.status_code >= 400:
            msg = _detail_from_error_response(r)
            log.warning("HTTP POST %s -> %s: %s", path, r.status_code, msg)
            raise GolfApiError(msg, status_code=r.status_code)
        log.debug("HTTP POST %s -> %s", path, r.status_code)
        return r.json()

    async def _patch_json(self, path: str, *, json: dict[str, Any] | None = None) -> Any:
        log.info("HTTP PATCH %s", path)
        if log.isEnabledFor(logging.DEBUG) and json is not None:
            log.debug("HTTP PATCH %s body=%s", path, json)
        try:
            r = await self._client.patch(path, json=json)
        except httpx.HTTPError:
            log.exception("HTTP PATCH %s failed (network/transport)", path)
            raise
        if r.status_code >= 400:
            msg = _detail_from_error_response(r)
            log.warning("HTTP PATCH %s -> %s: %s", path, r.status_code, msg)
            raise GolfApiError(msg, status_code=r.status_code)
        log.debug("HTTP PATCH %s -> %s", path, r.status_code)
        return r.json()

    async def _delete(self, path: str) -> None:
        log.info("HTTP DELETE %s", path)
        try:
            r = await self._client.delete(path)
        except httpx.HTTPError:
            log.exception("HTTP DELETE %s failed (network/transport)", path)
            raise
        if r.status_code >= 400:
            msg = _detail_from_error_response(r)
            log.warning("HTTP DELETE %s -> %s: %s", path, r.status_code, msg)
            raise GolfApiError(msg, status_code=r.status_code)
        log.debug("HTTP DELETE %s -> %s", path, r.status_code)

    async def get_players(self) -> list[dict[str, Any]]:
        return await self._get_json("/api/v1/players")

    async def create_player(
        self,
        *,
        name: str,
        handicap: float | None = None,
        age: int | None = None,
        gender: str | None = None,
        email: str | None = None,
        sponsor: str | None = None,
        phone: str | None = None,
        country: str | None = None,
        club: str | None = None,
        rank: int | None = None,
    ) -> dict[str, Any]:
        return await self._post_json(
            "/api/v1/players",
            json={
                "name": name,
                "handicap": handicap,
                "age": age,
                "gender": gender,
                "email": email,
                "sponsor": sponsor,
                "phone": phone,
                "country": country,
                "club": club,
                "rank": rank,
            },
        )

    async def update_player(
        self,
        player_id: int,
        *,
        name: str | None = None,
        handicap: float | None = None,
        age: int | None = None,
        gender: str | None = None,
        email: str | None = None,
        sponsor: str | None = None,
        phone: str | None = None,
        country: str | None = None,
        club: str | None = None,
        rank: int | None = None,
    ) -> dict[str, Any]:
        return await self._patch_json(
            f"/api/v1/players/{player_id}",
            json={
                "name": name,
                "handicap": handicap,
                "age": age,
                "gender": gender,
                "email": email,
                "sponsor": sponsor,
                "phone": phone,
                "country": country,
                "club": club,
                "rank": rank,
            },
        )

    async def delete_player(self, player_id: int) -> None:
        await self._delete(f"/api/v1/players/{player_id}")

    async def get_courses(self) -> list[dict[str, Any]]:
        return await self._get_json("/api/v1/courses")

    async def list_shots(
        self,
        *,
        round_id: int | None = None,
        hole_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """GET /shots — all shots, or filtered by round and/or hole."""
        params: dict[str, Any] = {}
        if round_id is not None:
            params["round_id"] = round_id
        if hole_id is not None:
            params["hole_id"] = hole_id
        return await self._get_json("/api/v1/shots", params=params or None)

    async def get_rounds(
        self,
        *,
        player_id: int | None = None,
        course_id: int | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if player_id is not None:
            params["player_id"] = player_id
        if course_id is not None:
            params["course_id"] = course_id
        return await self._get_json("/api/v1/rounds", params=params)

    async def get_shots_for_round(
        self,
        round_id: int,
        hole_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Shots for one round (nested route); optional hole filter."""
        params: dict[str, Any] = {}
        if hole_id is not None:
            params["hole_id"] = hole_id
        return await self._get_json(f"/api/v1/rounds/{round_id}/shots", params=params or None)

    async def create_round(self, *, player_id: int, course_id: int) -> dict[str, Any]:
        return await self._post_json(
            "/api/v1/rounds", json={"player_id": player_id, "course_id": course_id}
        )

    async def delete_shot(self, shot_id: int) -> None:
        await self._delete(f"/api/v1/shots/{shot_id}")

    async def get_holes(self, course_id: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if course_id is not None:
            params["course_id"] = course_id
        return await self._get_json("/api/v1/holes", params=params or None)

    async def create_shot(
        self,
        *,
        round_id: int,
        hole_id: int,
        x: float,
        y: float,
        club: str = "",
        distance: float | None = None,
    ) -> dict[str, Any]:
        body = {
            "round_id": round_id,
            "hole_id": hole_id,
            "x": x,
            "y": y,
            "club": club,
            "distance": distance,
        }
        return await self._post_json("/api/v1/shots", json=body)

    async def get_tournament_detail(self, tournament_id: int) -> dict[str, Any]:
        return await self._post_json(
            "/api/v1/tournaments/detail", json={"tournament_id": tournament_id}
        )

    async def post_scorecard_hole(
        self,
        *,
        scorecard_id: int,
        hole_number: int,
        strokes: int,
        player_id: int,
    ) -> dict[str, Any]:
        return await self._post_json(
            "/api/v1/scorecards/hole",
            json={
                "scorecard_id": scorecard_id,
                "hole_number": hole_number,
                "strokes": strokes,
                "player_id": player_id,
            },
        )

    async def get_tournaments(self) -> list[dict[str, Any]]:
        return await self._get_json("/api/v1/tournaments")

    async def get_tournament_drafts(self) -> list[dict[str, Any]]:
        return await self._get_json("/api/v1/tournaments/drafts")

    async def get_tournaments_started(self) -> list[dict[str, Any]]:
        return await self._get_json("/api/v1/tournaments/started")

    async def get_tournaments_non_draft(self) -> list[dict[str, Any]]:
        return await self._get_json("/api/v1/tournaments/non-draft")

    async def create_tournament(
        self,
        *,
        name: str,
        play_date: str,
        course_id: int,
    ) -> dict[str, Any]:
        body = {"name": name, "play_date": play_date, "course_id": course_id}
        return await self._post_json("/api/v1/tournaments", json=body)

    async def start_tournament(self, tournament_id: int) -> dict[str, Any]:
        return await self._post_json(
            "/api/v1/tournaments/start", json={"tournament_id": tournament_id}
        )

    async def stop_tournament(self, tournament_id: int) -> dict[str, Any]:
        return await self._post_json(
            "/api/v1/tournaments/stop", json={"tournament_id": tournament_id}
        )

    async def get_tournament_scorecards(self, tournament_id: int) -> list[dict[str, Any]]:
        return await self._post_json(
            "/api/v1/tournaments/scorecards", json={"tournament_id": tournament_id}
        )
