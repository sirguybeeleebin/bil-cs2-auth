import argparse
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Literal

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ConfigDict, computed_field
from pydantic_settings import BaseSettings

from engines import PostgresEngine
from repositories import UserRepository
from routers import create_auth_router
from services import AuthService


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    APP_TITLE: str = "Auth Service"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_WORKERS: int = 1
    APP_DEBUG: bool = False
    APP_LOG_LEVEL: Literal[
        "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"
    ] = "INFO"
    APP_API_PREFIX: str = "/api/v1"
    APP_VERSION: str = "1.0.0"

    POSTGRES_USER: str = "test_user"
    POSTGRES_PASSWORD: str = "test_password"
    POSTGRES_DB: str = "test_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_POOL_SIZE: int = 5
    POSTGRES_POOL_IDLE_CONS: int = 10

    JWT_SECRET: str = "test_secret"
    JWT_EXPIRE_SECONDS: int = 60 * 60 * 24  # 1 day

    CORS_ALLOW_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True

    @computed_field(return_type=str)
    @property
    def DATABASE_DSN(self) -> str:
        """Return formatted async DSN string for PostgreSQL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auth Service")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Path to environment file (default: .env)",
    )
    return parser.parse_args()


def parse_env_file(env_file: Path) -> Settings:
    return Settings(_env_file=env_file)


def configure_logger(settings: Settings):
    logging.basicConfig(
        level=getattr(logging, settings.APP_LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def create_app(settings: Settings) -> FastAPI:
    postgres_engine = PostgresEngine()
    user_repository = UserRepository(postgres_engine)
    auth_service = AuthService(
        repository=user_repository,
        jwt_secret=settings.JWT_SECRET,
        jwt_exp=settings.JWT_EXPIRE_SECONDS,
    )
    auth_router = create_auth_router(auth_service, postgres_engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await postgres_engine.connect(
            dsn=settings.DATABASE_DSN,
            pool_size=settings.POSTGRES_POOL_SIZE,
            pool_max_idle_cons=settings.POSTGRES_POOL_IDLE_CONS,
        )
        logging.info("Connected to PostgreSQL.")
        yield
        await postgres_engine.disconnect()
        logging.info("PostgreSQL connection closed.")

    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    router = APIRouter(prefix=settings.APP_API_PREFIX)
    router.include_router(auth_router)
    app.include_router(router)

    return app


def run_uvicorn(app: FastAPI, settings: Settings) -> None:
    uvicorn.run(
        app,
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        workers=settings.APP_WORKERS,
        log_level=settings.APP_LOG_LEVEL.lower(),
    )


def main():
    args = parse_args()
    settings = parse_env_file(args.env_file)
    configure_logger(settings)
    app = create_app(settings)
    run_uvicorn(app, settings)


if __name__ == "__main__":
    main()
