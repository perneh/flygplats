"""Async HTTP client for the Golf API — easy to mock in tests."""

from __future__ import annotations

from typing import Any

import httpx


class GolfApiClient:
    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self._base = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base, timeout=timeout)

    @property
    def base_url(self) -> str:
        return self._base

    async def aclose(self) -> None:
        await self._client.aclose()

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
        r = await self._client.get("/api/v1/rounds", params=params)
        r.raise_for_status()
        return r.json()

    async def get_shots(
        self,
        round_id: int,
        hole_id: int | None = None,
    ) -> list[dict[str, Any]]:
        params = {}
        if hole_id is not None:
            params["hole_id"] = hole_id
        r = await self._client.get(f"/api/v1/rounds/{round_id}/shots", params=params)
        r.raise_for_status()
        return r.json()

    async def get_holes(self, course_id: int | None = None) -> list[dict[str, Any]]:
        params = {}
        if course_id is not None:
            params["course_id"] = course_id
        r = await self._client.get("/api/v1/holes", params=params)
        r.raise_for_status()
        return r.json()

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
        r = await self._client.post("/api/v1/shots", json=body)
        r.raise_for_status()
        return r.json()
