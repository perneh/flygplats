#!/usr/bin/env python3
"""Insert demo player, course, holes, round, and shots. Run from backend dir with DATABASE_URL set."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import Course, Hole, Player, Round, Shot


async def main() -> None:
    url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./seed.db")
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        player = Player(name="Demo Player")
        course = Course(name="Demo Links", description="Flat par-72 for visualization")
        session.add_all([player, course])
        await session.flush()

        holes = []
        for n in range(1, 4):
            tee_y = (n - 1) * 30.0
            h = Hole(
                course_id=course.id,
                number=n,
                par=4,
                tee_x=0.0,
                tee_y=tee_y,
                green_x=200.0,
                green_y=tee_y + 5.0,
            )
            holes.append(h)
        session.add_all(holes)
        await session.flush()

        rnd = Round(player_id=player.id, course_id=course.id)
        session.add(rnd)
        await session.flush()

        h1 = holes[0]
        shots_data = [
            (10.0, h1.tee_y, "Driver", 180.0),
            (80.0, h1.tee_y + 8.0, "7-iron", 120.0),
            (h1.green_x - 5, h1.green_y, "Putter", 12.0),
        ]
        for x, y, club, dist in shots_data:
            session.add(
                Shot(
                    round_id=rnd.id,
                    hole_id=h1.id,
                    x=x,
                    y=y,
                    club=club,
                    distance=dist,
                )
            )

        await session.commit()
        print(f"Seeded player id={player.id}, course id={course.id}, round id={rnd.id}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
