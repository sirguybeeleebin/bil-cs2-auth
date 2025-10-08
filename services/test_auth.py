from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from schemas import LoginRequest, LoginResponse, RegisterRequest
from services.auth import AuthService


@pytest.mark.asyncio
async def test_register_success(monkeypatch):
    mock_repo = AsyncMock()
    mock_repo.get.return_value = None
    mock_repo.upsert.return_value = {"user_uuid": "123", "username": "alice"}

    auth_service = AuthService(mock_repo, jwt_secret="secret")

    req = RegisterRequest(username="alice", password="StrongPass1!")

    # bcrypt.hashpw returns bytes → AuthService decodes it internally
    with patch("bcrypt.hashpw", return_value=b"hashed_pw"):
        result = await auth_service.register(req)

    assert result is None
    mock_repo.get.assert_awaited_once_with(username="alice")
    mock_repo.upsert.assert_awaited_once_with(
        username="alice", password_hash="hashed_pw"
    )


@pytest.mark.asyncio
async def test_register_user_already_exists():
    mock_repo = AsyncMock()
    mock_repo.get.return_value = {"user_uuid": "1", "username": "bob"}

    auth_service = AuthService(mock_repo, jwt_secret="secret")

    req = RegisterRequest(username="bob", password="StrongPass1!")

    with pytest.raises(HTTPException) as exc:
        await auth_service.register(req)

    assert exc.value.status_code == 409
    assert "exists" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_register_upsert_failed():
    mock_repo = AsyncMock()
    mock_repo.get.return_value = None
    mock_repo.upsert.return_value = None

    auth_service = AuthService(mock_repo, jwt_secret="secret")

    req = RegisterRequest(username="charlie", password="ValidPass9!")

    with pytest.raises(HTTPException) as exc:
        with patch("bcrypt.hashpw", return_value=b"hashed_pw"):
            await auth_service.register(req)

    assert exc.value.status_code == 500
    assert "failed" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_login_success(monkeypatch):
    mock_repo = AsyncMock()
    user_data = {
        "user_uuid": "uuid-123",
        "username": "alice",
        "password_hash": "hashed_pw",
    }
    mock_repo.get.return_value = user_data

    auth_service = AuthService(mock_repo, jwt_secret="secret")

    req = LoginRequest(username="alice", password="StrongPass1!")

    with (
        patch("bcrypt.checkpw", return_value=True),
        patch("jwt.encode", return_value="fake_token"),
    ):
        result = await auth_service.login(req)

    assert isinstance(result, LoginResponse)
    assert result.token == "fake_token"


@pytest.mark.asyncio
async def test_login_invalid_username():
    mock_repo = AsyncMock()
    mock_repo.get.return_value = None

    auth_service = AuthService(mock_repo, jwt_secret="secret")

    req = LoginRequest(username="ghost", password="StrongPass1!")

    with pytest.raises(HTTPException) as exc:
        await auth_service.login(req)

    assert exc.value.status_code == 401
    assert "invalid" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_login_invalid_password(monkeypatch):
    mock_repo = AsyncMock()
    user_data = {
        "user_uuid": "uuid-123",
        "username": "alice",
        "password_hash": "hashed_pw",
    }
    mock_repo.get.return_value = user_data

    auth_service = AuthService(mock_repo, jwt_secret="secret")

    req = LoginRequest(username="alice", password="WrongPass1!")

    with patch("bcrypt.checkpw", return_value=False):
        with pytest.raises(HTTPException) as exc:
            await auth_service.login(req)

    assert exc.value.status_code == 401
    assert "invalid" in exc.value.detail.lower()
