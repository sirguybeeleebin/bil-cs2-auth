import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from engines import PostgresEngine


@pytest.fixture(scope="session")
def sqlite_dsn() -> str:
    """Provide an in-memory SQLite DSN using async driver."""
    return "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
async def test_connect_and_disconnect(sqlite_dsn):
    engine = PostgresEngine()
    await engine.connect(dsn=sqlite_dsn, pool_size=2, pool_max_idle_cons=5)

    assert engine.engine is not None
    assert engine.session_factory is not None

    await engine.disconnect()
    assert engine.engine is None
    assert engine.session_factory is None


@pytest.mark.asyncio
async def test_disconnect_without_connect(caplog):
    engine = PostgresEngine()
    await engine.disconnect()

    assert "disconnect() called but engine was not initialized." in caplog.text


@pytest.mark.asyncio
async def test_get_session_creates_and_reuses(sqlite_dsn):
    engine = PostgresEngine()
    await engine.connect(dsn=sqlite_dsn)

    session1 = await engine.get_session()
    session2 = await engine.get_session()

    assert isinstance(session1, AsyncSession)
    assert session1 is session2  # contextvar reuse

    await engine.disconnect()


@pytest.mark.asyncio
async def test_get_session_without_connect_logs_error(caplog):
    engine = PostgresEngine()
    session = await engine.get_session()

    assert session is None
    assert "Attempted to get session before engine initialization." in caplog.text


@pytest.mark.asyncio
async def test_reset_context_clears_session(sqlite_dsn):
    engine = PostgresEngine()
    await engine.connect(dsn=sqlite_dsn)

    session = await engine.get_session()
    assert engine._session_context.get() is session

    engine.reset_context()
    assert engine._session_context.get() is None

    await engine.disconnect()
