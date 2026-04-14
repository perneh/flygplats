"""Sanity checks for bundled init data and seed layout (no DB required)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _json_file() -> Path:
    return Path(__file__).resolve().parents[1] / "init_data" / "golf_courses_25.json"


def _players_json_file() -> Path:
    return Path(__file__).resolve().parents[1] / "init_data" / "golf_players.json"


def test_golf_courses_json_exists_and_has_25_courses():
    p = _json_file()
    assert p.is_file(), f"expected {p}"
    data = json.loads(p.read_text(encoding="utf-8"))
    courses = data["golf_courses"]
    assert len(courses) == 25
    for c in courses:
        assert "name" in c
        assert "id" in c
        assert "country" in c
        holes = c["holes"]
        assert len(holes) == 18
        for h in holes:
            assert "hole" in h and "par" in h and "length_m" in h
            assert "tee" in h and "green" in h
            assert "lat" in h["tee"] and "lng" in h["tee"]
            assert "lat" in h["green"] and "lng" in h["green"]


def test_golf_players_json_exists_and_layout():
    p = _players_json_file()
    assert p.is_file(), f"expected {p}"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 200
    for row in data:
        for key in (
            "id",
            "first_name",
            "last_name",
            "email",
            "handicap",
            "birthdate",
            "country",
            "phone",
            "gender",
            "club",
            "ranking",
        ):
            assert key in row

