import logging

import pytest
from fastapi import FastAPI, HTTPException
from httpx import AsyncClient

from routers.middlewares import LoggingMiddleware


@pytest.fixture
def app():
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)

    @app.get("/ok")
    async def ok_route():
        return {"message": "ok"}

    @app.get("/error")
    async def error_route():
        raise HTTPException(status_code=400, detail="bad request")

    return app


@pytest.mark.asyncio
async def test_logging_middleware_ok(app, caplog):
    caplog.set_level(logging.INFO)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/ok")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers

    # Extract the logged lines
    logs = [rec.message for rec in caplog.records]
    assert any("method=GET" in line for line in logs)
    assert any("status_code=200" in line for line in logs)
    assert any("request_id=" in line for line in logs)


@pytest.mark.asyncio
async def test_logging_middleware_error(app, caplog):
    caplog.set_level(logging.INFO)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/error")

    assert response.status_code == 400
    assert "X-Request-ID" in response.headers

    logs = [rec.message for rec in caplog.records]
    assert any("status_code=400" in line for line in logs)
    assert any("request_id=" in line for line in logs)
