from fastapi import APIRouter

from app.routers import courses, dev, dev_logs, golf_clubs, holes, matches, players, rounds, shots

api_router = APIRouter()
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(golf_clubs.router, prefix="/golf-clubs", tags=["golf-clubs"])
api_router.include_router(holes.router, prefix="/holes", tags=["holes"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(rounds.router, prefix="/rounds", tags=["rounds"])
api_router.include_router(shots.router, prefix="/shots", tags=["shots"])
api_router.include_router(dev.router, prefix="/dev", tags=["dev"])
api_router.include_router(dev_logs.router, prefix="/dev", tags=["dev"])
