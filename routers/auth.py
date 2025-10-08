from fastapi import APIRouter, status

from engines import PostgresEngine
from routers.decorators import transaction
from schemas import LoginRequest, LoginResponse, RegisterRequest
from services import AuthService


def create_auth_router(
    auth_service: AuthService,
    postgres_engine: PostgresEngine,
) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/register", status_code=status.HTTP_201_CREATED)
    @transaction(postgres_engine)
    async def register(req: RegisterRequest) -> None:
        """Register a new user."""
        return await auth_service.register(req)

    @router.post("/login", response_model=LoginResponse)
    async def login(req: LoginRequest):
        """Login user and return JWT token."""
        return await auth_service.login(req)

    return router
