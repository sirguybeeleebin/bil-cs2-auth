import functools
import logging
from typing import Any, Awaitable, Callable, TypeVar

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from engines import PostgresEngine

log = logging.getLogger(__name__)
R = TypeVar("R")


def transaction(engine: PostgresEngine):
    def decorator(func: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> R:
            session = await engine.get_session()
            if session is None:
                raise HTTPException(
                    status_code=500, detail="Database session not available."
                )

            try:
                result = await func(*args, **kwargs)
                await session.commit()
                return result
            except SQLAlchemyError as e:
                await session.rollback()
                log.warning(f"Transaction rolled back due to SQLAlchemyError: {e}")
                raise HTTPException(
                    status_code=500, detail="Database transaction failed."
                )
            except Exception as e:
                await session.rollback()
                log.exception(f"Unexpected error during transaction: {e}")
                raise
            finally:
                engine.reset_context()

        return wrapper

    return decorator
