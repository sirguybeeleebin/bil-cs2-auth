import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

log = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        request.state.request_id = request_id

        log.info(
            f"request_id={request_id}, method={request.method}, path={request.url.path}"
        )

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            log.exception(f"request_id={request_id}, error={exc}")
            raise

        duration = (time.perf_counter() - start_time) * 1000  # ms
        size = response.headers.get("content-length") or "unknown"

        response.headers["X-Request-ID"] = request_id

        log.info(
            f"request_id={request_id}, method={request.method}, path={request.url.path}, "
            f"status_code={response.status_code}, size={size}, duration_ms={duration:.2f}"
        )

        return response
