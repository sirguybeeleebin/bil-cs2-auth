import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from engines.postgres import PostgresEngine
from repositories.models import UserDB
from repositories.user import UserRepository


@pytest.mark.asyncio
async def test_upsert_returns_user_dict():
    mock_engine = MagicMock(spec=PostgresEngine)
    mock_session = AsyncMock()
    mock_result = MagicMock()

    fake_user = UserDB(
        user_uuid=uuid.uuid4(), username="alice", password_hash="hash123"
    )
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_session.execute.return_value = mock_result
    mock_engine.get_session = AsyncMock(return_value=mock_session)

    repo = UserRepository(mock_engine)
    result = await repo.upsert(username="alice", password_hash="hash123")

    mock_engine.get_session.assert_awaited_once()
    mock_session.execute.assert_awaited_once()
    assert isinstance(result, dict)
    assert result["username"] == "alice"
    assert result["password_hash"] == "hash123"


@pytest.mark.asyncio
async def test_upsert_returns_none_when_no_user():
    mock_engine = MagicMock(spec=PostgresEngine)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    mock_engine.get_session = AsyncMock(return_value=mock_session)

    repo = UserRepository(mock_engine)
    result = await repo.upsert(username="bob", password_hash="pw")

    assert result is None
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_upsert_builds_insert_statement(monkeypatch):
    mock_engine = MagicMock(spec=PostgresEngine)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    fake_user = UserDB(user_uuid=uuid.uuid4(), username="bob", password_hash="pw")
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_session.execute.return_value = mock_result
    mock_engine.get_session = AsyncMock(return_value=mock_session)

    mock_insert = MagicMock(return_value=MagicMock())
    monkeypatch.setattr("repositories.user.insert", mock_insert)

    repo = UserRepository(mock_engine)
    await repo.upsert(username="bob", password_hash="pw")

    mock_insert.assert_called_once_with(UserDB)
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_uuid_returns_user_dict():
    mock_engine = MagicMock(spec=PostgresEngine)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    user_id = uuid.uuid4()
    fake_user = UserDB(user_uuid=user_id, username="alice", password_hash="pw")
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_session.execute.return_value = mock_result
    mock_engine.get_session = AsyncMock(return_value=mock_session)

    repo = UserRepository(mock_engine)
    result = await repo.get(user_uuid=user_id)

    mock_engine.get_session.assert_awaited_once()
    mock_session.execute.assert_awaited_once()
    assert isinstance(result, dict)
    assert result["user_uuid"] == user_id


@pytest.mark.asyncio
async def test_get_by_username_returns_user_dict():
    mock_engine = MagicMock(spec=PostgresEngine)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    fake_user = UserDB(user_uuid=uuid.uuid4(), username="charlie", password_hash="pw")
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_session.execute.return_value = mock_result
    mock_engine.get_session = AsyncMock(return_value=mock_session)

    repo = UserRepository(mock_engine)
    result = await repo.get(username="charlie")

    mock_engine.get_session.assert_awaited_once()
    mock_session.execute.assert_awaited_once()
    assert result["username"] == "charlie"


@pytest.mark.asyncio
async def test_get_returns_none_if_no_user():
    mock_engine = MagicMock(spec=PostgresEngine)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    mock_engine.get_session = AsyncMock(return_value=mock_session)

    repo = UserRepository(mock_engine)
    result = await repo.get(username="ghost")

    assert result is None
    mock_session.execute.assert_awaited_once()
