"""Sanity checks for bundled init data and seed layout (no DB required)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _json_file() -> Path:
    return Path(__file__).resolve().parents[1] / "init_data" / "golf_courses_25.json"


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

