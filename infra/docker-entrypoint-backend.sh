#!/bin/sh
set -e
cd /app
alembic upgrade head
python -m app.seed_init_data
# LOG_LEVEL: uvicorn access/error + matches app logging (see app.logging_setup)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level "${LOG_LEVEL:-info}"
