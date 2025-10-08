import uuid

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert

from engines import PostgresEngine
from repositories.models import UserDB


class UserRepository:
    def __init__(self, engine: PostgresEngine) -> None:
        self._engine = engine

    async def upsert(
        self,
        *,
        username: str,
        password_hash: str,
    ) -> dict | None:
        session = await self._engine.get_session()

        stmt = (
            insert(UserDB)
            .values(username=username, password_hash=password_hash)
            .on_conflict_do_update(
                index_elements=[UserDB.username],
                set_={"password_hash": password_hash},
            )
            .returning(UserDB)
        )

        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return dict(user.__dict__) if user else None

    async def get(
        self,
        *,
        user_uuid: uuid.UUID | None = None,
        username: str | None = None,
    ) -> dict | None:
        session = await self._engine.get_session()

        conditions = []
        if user_uuid:
            conditions.append(UserDB.user_uuid == user_uuid)
        if username:
            conditions.append(UserDB.username == username)

        stmt = select(UserDB).where(or_(*conditions))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        return dict(user.__dict__) if user else None


user_repository: UserRepository | None = None
