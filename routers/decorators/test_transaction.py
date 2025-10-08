from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from routers.decorators import transaction


@pytest.fixture
def mock_engine():
    """Mock PostgresEngine with async session."""
    engine = MagicMock()
    engine.get_session = AsyncMock()
    engine.reset_context = MagicMock()

    # Create an async session mock with async commit/rollback
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    # Default behavior: return our session
    engine.get_session.return_value = mock_session
    return engine


@pytest.mark.asyncio
async def test_transaction_success(mock_engine):
    """✅ Should commit and reset context on success."""
    mock_session = await mock_engine.get_session()

    @transaction(mock_engine)
    async def dummy_func(x):
        return x * 2

    result = await dummy_func(5)

    assert result == 10
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_not_awaited()
    mock_engine.reset_context.assert_called_once()


@pytest.mark.asyncio
async def test_transaction_sqlalchemy_error(mock_engine):
    """❌ Should rollback and raise HTTPException on SQLAlchemyError."""
    mock_session = await mock_engine.get_session()

    @transaction(mock_engine)
    async def failing_func():
        raise SQLAlchemyError("DB issue")

    with pytest.raises(HTTPException) as exc:
        await failing_func()

    assert exc.value.status_code == 500
    assert "transaction failed" in exc.value.detail.lower()
    mock_session.rollback.assert_awaited_once()
    mock_session.commit.assert_not_awaited()
    mock_engine.reset_context.assert_called_once()


@pytest.mark.asyncio
async def test_transaction_generic_exception(mock_engine):
    """❌ Should rollback and re-raise non-SQLAlchemy exceptions."""
    mock_session = await mock_engine.get_session()

    @transaction(mock_engine)
    async def crashing_func():
        raise ValueError("unexpected")

    with pytest.raises(ValueError):
        await crashing_func()

    mock_session.rollback.assert_awaited_once()
    mock_session.commit.assert_not_awaited()
    mock_engine.reset_context.assert_called_once()


@pytest.mark.asyncio
async def test_transaction_no_session(mock_engine):
    """❌ Should raise HTTPException if session is None."""
    mock_engine.get_session.return_value = None

    @transaction(mock_engine)
    async def dummy_func():
        return "ok"

    with pytest.raises(HTTPException) as exc:
        await dummy_func()

    assert exc.value.status_code == 500
    assert "session not available" in exc.value.detail.lower()
    mock_engine.reset_context.assert_not_called()
