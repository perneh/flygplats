import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db.session import get_engine
from app.logging_setup import configure_logging
from app.routers import api_router

configure_logging(settings)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Golf API startup complete (prefix=%s)", settings.api_prefix)
    yield
    logger.info("Golf API shutdown: disposing DB engine")
    engine = get_engine()
    await engine.dispose()


app = FastAPI(title="Golf API", version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health():
    return {"status": "ok"}
