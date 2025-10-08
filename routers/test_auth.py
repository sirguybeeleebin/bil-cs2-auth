from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from routers.auth import create_auth_router
from schemas import LoginResponse


@pytest.fixture
def mock_auth_service():
    """Mocked AuthService."""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_postgres_engine():
    """Mocked PostgresEngine with async session support."""
    engine = MagicMock()

    # ✅ Create mock async session with async commit/rollback
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    async def get_session():
        return mock_session

    engine.get_session = get_session
    engine.reset_context = MagicMock()

    return engine


@pytest.fixture
def app(mock_auth_service, mock_postgres_engine):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    router = create_auth_router(mock_auth_service, mock_postgres_engine)
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """FastAPI test client."""
    return TestClient(app)


# ========================= TESTS =========================


def test_register_success(client, mock_auth_service):
    """✅ Should call AuthService.register and return 201."""
    mock_auth_service.register.return_value = None

    payload = {"username": "alice", "password": "StrongPass1!"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    mock_auth_service.register.assert_awaited_once()


def test_register_failure(client, mock_auth_service):
    """❌ Should return 400 if AuthService.register raises HTTPException."""

    async def fail_register(req):
        raise HTTPException(status_code=400, detail="Invalid request")

    mock_auth_service.register.side_effect = fail_register

    payload = {"username": "bob", "password": "StrongPass1!"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()
    mock_auth_service.register.assert_awaited_once()


def test_login_success(client, mock_auth_service):
    """✅ Should return JWT token from AuthService.login."""
    mock_auth_service.login.return_value = LoginResponse(token="fake_jwt_token")

    payload = {"username": "alice", "password": "StrongPass1!"}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    assert response.json() == {"token": "fake_jwt_token"}
    mock_auth_service.login.assert_awaited_once()


def test_login_failure(client, mock_auth_service):
    """❌ Should return 401 if AuthService.login raises HTTPException."""

    async def fail_login(req):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    mock_auth_service.login.side_effect = fail_login

    payload = {"username": "bob", "password": "StrongPass1!"}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()
    mock_auth_service.login.assert_awaited_once()
