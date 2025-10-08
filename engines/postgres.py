import logging
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

log = logging.getLogger(__name__)


class PostgresEngine:
    """Manages async PostgreSQL engine and session lifecycle."""

    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self._session_context: ContextVar[AsyncSession | None] = ContextVar(
            "postgres_session_context", default=None
        )

    async def connect(
        self, dsn: str, pool_size: int = 10, pool_max_idle_cons: int = 20
    ) -> None:
        try:
            engine_args = {"echo": False, "future": True}
            if not dsn.startswith("sqlite"):
                engine_args.update(
                    {"pool_size": pool_size, "max_overflow": pool_max_idle_cons}
                )

            self.engine = create_async_engine(dsn, **engine_args)
            self.session_factory = async_sessionmaker(
                bind=self.engine, class_=AsyncSession, expire_on_commit=False
            )
        except Exception as e:
            log.error("Error initializing PostgreSQL engine: %s", e, exc_info=True)

    async def disconnect(self) -> None:
        if not self.engine:
            log.warning("disconnect() called but engine was not initialized.")
            return None
        try:
            await self.engine.dispose()
        except Exception as e:
            log.exception(f"Error closing PostgreSQL connection: {e}")
        finally:
            self.engine = None
            self.session_factory = None
            self._session_context.set(None)
        return None

    async def get_session(self) -> AsyncSession | None:
        if self.session_factory is None:
            log.error("Attempted to get session before engine initialization.")
            return None
        try:
            session = self._session_context.get()
            if session is None:
                new_session = self.session_factory()
                self._session_context.set(new_session)
                return new_session
            return session
        except Exception as e:
            log.exception(f"Error creating or retrieving session: {e}")
            return None

    def reset_context(self) -> None:
        try:
            self._session_context.set(None)
        except Exception as e:
            log.warning(f"Failed to reset session context: {e}")


postgres_engine: PostgresEngine | None = None
