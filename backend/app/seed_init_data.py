"""
Load bundled golf definitions into an empty database.

Runs after migrations in Docker (see ``infra/docker-entrypoint-backend.sh``). Idempotent:
if a table already has rows, that seed step is skipped so existing deployments are not duplicated.

JSON sources under ``backend/init_data/``:

- ``golf_courses_25.json`` — courses + holes (``CourseRead`` / ``HoleRead`` shape).
- ``golf_clubs.json`` — golf clubs catalog.
- ``golf_players.json`` — player profiles (top-level JSON array of objects with
  ``first_name``, ``last_name``, ``email``, ``handicap``, ``birthdate``, ``country``, ``phone``, ``gender``,
  ``club``, ``ranking``).
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import async_session_maker
from app.geo.canvas_project import bounds_from_latlng_pairs, project_latlng_to_canvas
from app.models import Course, GolfClub, Hole, Player

logger = logging.getLogger("app.seed_init_data")

_DEFAULT_REL = Path("init_data") / "golf_courses_25.json"
_DEFAULT_GOLF_CLUBS = Path("init_data") / "golf_clubs.json"
_DEFAULT_GOLF_PLAYERS = Path("init_data") / "golf_players.json"


def _json_path() -> Path:
    env = (settings.init_data_json_path or "").strip()
    if env:
        return Path(env)
    base = Path(__file__).resolve().parent.parent
    return base / _DEFAULT_REL


def _golf_clubs_json_path() -> Path:
    env = (settings.init_data_golf_clubs_path or "").strip()
    if env:
        return Path(env)
    base = Path(__file__).resolve().parent.parent
    return base / _DEFAULT_GOLF_CLUBS


def _golf_players_json_path() -> Path:
    env = (settings.init_data_golf_players_path or "").strip()
    if env:
        return Path(env)
    base = Path(__file__).resolve().parent.parent
    return base / _DEFAULT_GOLF_PLAYERS


def _age_from_birthdate(iso: str) -> int | None:
    try:
        bd = date.fromisoformat(iso.strip()[:10])
    except (ValueError, AttributeError):
        return None
    today = date.today()
    age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    return max(1, min(120, age))


def _hole_geo_pairs(hole: dict[str, Any]) -> list[tuple[float, float]]:
    tee = hole.get("tee") or {}
    green = hole.get("green") or {}
    return [
        (float(tee["lat"]), float(tee["lng"])),
        (float(green["lat"]), float(green["lng"])),
    ]


async def seed_init_courses_if_empty_session(session: AsyncSession) -> bool:
    """
    Insert courses and holes from JSON when ``courses`` is empty.

    Caller commits. Used by CLI seed, ``factory-default`` (after wipe), and Docker entrypoint.
    """
    path = _json_path()
    if not path.is_file():
        logger.warning("Init data file missing at %s — skipping seed", path)
        return False

    raw = json.loads(path.read_text(encoding="utf-8"))
    courses_data = raw.get("golf_courses")
    if not isinstance(courses_data, list):
        logger.error("Invalid JSON: expected golf_courses array")
        return False

    r = await session.execute(select(func.count()).select_from(Course))
    existing = r.scalar_one()
    if existing and existing > 0:
        logger.info("Database already has %s course(s); skipping init seed", existing)
        return False

    for c in courses_data:
        name = str(c.get("name") or "Unnamed")
        country = (c.get("country") or None) and str(c.get("country"))
        catalog = c.get("id")
        catalog_id = int(catalog) if catalog is not None else None

        course = Course(
            name=name,
            country=country,
            catalog_id=catalog_id,
            description=None,
        )
        session.add(course)
        await session.flush()

        holes_raw = c.get("holes") or []
        all_pairs: list[tuple[float, float]] = []
        for h in holes_raw:
            all_pairs.extend(_hole_geo_pairs(h))
        bounds = bounds_from_latlng_pairs(all_pairs)

        for h in holes_raw:
            num = int(h["hole"])
            par = int(h["par"])
            length_m = float(h["length_m"])
            tee_d = h.get("tee") or {}
            green_d = h.get("green") or {}
            t_lat, t_lng = float(tee_d["lat"]), float(tee_d["lng"])
            g_lat, g_lng = float(green_d["lat"]), float(green_d["lng"])
            tx, ty = project_latlng_to_canvas(t_lat, t_lng, bounds)
            gx, gy = project_latlng_to_canvas(g_lat, g_lng, bounds)
            session.add(
                Hole(
                    course_id=course.id,
                    number=num,
                    par=par,
                    length_m=length_m,
                    tee_lat=t_lat,
                    tee_lng=t_lng,
                    green_lat=g_lat,
                    green_lng=g_lng,
                    tee_x=tx,
                    tee_y=ty,
                    green_x=gx,
                    green_y=gy,
                )
            )

    logger.info("Seeded %s courses from %s", len(courses_data), path)
    return True


async def seed_init_courses_if_empty() -> bool:
    """CLI / Docker entrypoint: own session and commit if seed ran."""
    async with async_session_maker() as session:
        ran = await seed_init_courses_if_empty_session(session)
        if ran:
            await session.commit()
        return ran


async def seed_golf_clubs_if_empty_session(session: AsyncSession) -> bool:
    """
    Insert golf clubs from JSON when ``golf_clubs`` is empty.

    Caller must ``commit`` the session when this returns True. Used by CLI seed and
    ``POST /dev/seed-golf-clubs`` so tests hit the same DB as the ASGI app.
    """
    path = _golf_clubs_json_path()
    if not path.is_file():
        logger.warning("Golf clubs init data missing at %s — skipping seed", path)
        return False

    raw = json.loads(path.read_text(encoding="utf-8"))
    clubs_data = raw.get("golf_clubs")
    if not isinstance(clubs_data, list):
        logger.error("Invalid JSON: expected golf_clubs array")
        return False

    r = await session.execute(select(func.count()).select_from(GolfClub))
    existing = r.scalar_one()
    if existing and existing > 0:
        logger.info("Database already has %s golf club(s); skipping init seed", existing)
        return False

    for item in clubs_data:
        catalog = item.get("id")
        catalog_id = int(catalog) if catalog is not None else None
        pl_raw = item.get("player_level")
        if isinstance(pl_raw, list):
            pl = [str(x) for x in pl_raw]
        else:
            pl = []
        session.add(
            GolfClub(
                catalog_id=catalog_id,
                name=str(item.get("name") or "Club"),
                club_type=str(item.get("type") or "Unknown"),
                loft_deg=float(item.get("loft_deg") or 0.0),
                difficulty=str(item.get("difficulty") or "Medium"),
                max_distance_m=int(item.get("max_distance_m") or 0),
                avg_distance_m=int(item.get("avg_distance_m") or 0),
                player_levels=pl,
            )
        )

    logger.info("Seeded %s golf clubs from %s", len(clubs_data), path)
    return True


async def seed_players_if_empty_session(session: AsyncSession) -> bool:
    """
    Insert players from JSON when ``players`` is empty.

    Caller must ``commit`` the session when this returns True. Used by CLI seed and
    ``POST /dev/factory-default`` after a wipe.
    """
    path = _golf_players_json_path()
    if not path.is_file():
        logger.warning("Players init data missing at %s — skipping seed", path)
        return False

    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        players_data = raw
    elif isinstance(raw, dict) and isinstance(raw.get("golf_players"), list):
        players_data = raw["golf_players"]
    else:
        logger.error("Invalid JSON: expected a top-level array or an object with golf_players array")
        return False

    r = await session.execute(select(func.count()).select_from(Player))
    existing = r.scalar_one()
    if existing and existing > 0:
        logger.info("Database already has %s player(s); skipping init seed", existing)
        return False

    for item in players_data:
        fn = str(item.get("first_name") or "").strip()
        ln = str(item.get("last_name") or "").strip()
        name = f"{fn} {ln}".strip() or "Unknown"
        hcp_raw = item.get("handicap")
        handicap = float(hcp_raw) if hcp_raw is not None else None
        bdate = item.get("birthdate")
        age = _age_from_birthdate(str(bdate)) if bdate else None
        gender = str(item.get("gender") or "").strip() or None
        email = str(item.get("email") or "").strip() or None
        phone = str(item.get("phone") or "").strip() or None
        country = str(item.get("country") or "").strip() or None
        club = str(item.get("club") or "").strip() or None
        rank_raw = item.get("ranking")
        try:
            rank = int(rank_raw) if rank_raw is not None else None
        except (TypeError, ValueError):
            rank = None

        session.add(
            Player(
                name=name,
                handicap=handicap,
                age=age,
                gender=gender,
                email=email,
                phone=phone,
                country=country,
                club=club,
                rank=rank,
                sponsor=None,
            )
        )

    logger.info("Seeded %s players from %s", len(players_data), path)
    return True


async def seed_init_golf_clubs_if_empty() -> bool:
    """CLI / Docker: open a session from the process engine and commit if seed ran."""
    async with async_session_maker() as session:
        ran = await seed_golf_clubs_if_empty_session(session)
        if ran:
            await session.commit()
        return ran


async def seed_init_players_if_empty() -> bool:
    """CLI / Docker: own session and commit if seed ran."""
    async with async_session_maker() as session:
        ran = await seed_players_if_empty_session(session)
        if ran:
            await session.commit()
        return ran


async def _async_main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    await seed_init_courses_if_empty()
    await seed_init_golf_clubs_if_empty()
    await seed_init_players_if_empty()


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
