from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status

from repositories import UserRepository
from schemas import LoginRequest, LoginResponse, RegisterRequest


class AuthService:
    def __init__(
        self,
        repository: UserRepository,
        jwt_secret: str,
        jwt_exp: int = 60,
        jwt_algorithm: str = "HS256",
    ) -> None:
        self._repository = repository
        self._jwt_secret = jwt_secret
        self._jwt_exp = jwt_exp
        self._jwt_algorithm = jwt_algorithm

    async def register(self, req: RegisterRequest) -> None:
        existing_user = await self._repository.get(username=req.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists.",
            )

        password_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()

        user = await self._repository.upsert(
            username=req.username,
            password_hash=password_hash,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user.",
            )

        return None

    async def login(self, data: LoginRequest) -> LoginResponse:
        user = await self._repository.get(username=data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        if not bcrypt.checkpw(data.password.encode(), user["password_hash"].encode()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        payload = {
            "sub": str(user["user_uuid"]),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=self._jwt_exp),
        }

        token = jwt.encode(payload, self._jwt_secret, algorithm=self._jwt_algorithm)

        return LoginResponse(token=token)


auth_service: AuthService | None = None
