from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://golf:golf@db:5432/golf"
    api_prefix: str = "/api/v1"

    #: Root log level for app loggers (``LOG_LEVEL``). Uvicorn also reads ``--log-level`` from the shell.
    log_level: str = "INFO"
    #: When true, SQLAlchemy emits SQL to logs (``LOG_SQL``). Noisy; use for debugging only.
    log_sql: bool = False

    #: Append ``app`` logs to this file (rotating) for ``/api/v1/dev/log*`` endpoints (``LOG_FILE_PATH``).
    log_file_path: str = "/tmp/golf-api.log"

    #: Override path to ``golf_courses_25.json`` for ``seed_init_data`` (default: ``<backend>/init_data/...``).
    init_data_json_path: str = ""
    #: Override path to ``golf_clubs.json`` for ``seed_init_data`` (default: ``<backend>/init_data/golf_clubs.json``).
    init_data_golf_clubs_path: str = ""


settings = Settings()
