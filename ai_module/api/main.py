import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import Response

from ai_module.api.routers.health import router as health_router
from ai_module.api.routers.suggestions import router as suggestions_router
from ai_module.core.logging import configure_logging

logger = logging.getLogger("ai_module.api")


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="SMTH AI Module",
        version="0.1.0",
        docs_url="/swagger",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    @app.middleware("http")
    async def log_http_response(request: Request, call_next):
        request_id = str(uuid4())
        started = time.perf_counter()

        response = await call_next(request)

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        duration_ms = int((time.perf_counter() - started) * 1000)
        body_text = body.decode("utf-8", errors="replace")

        logger.info(
            "response request_id=%s method=%s path=%s status=%s duration_ms=%s body=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            body_text,
        )

        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

    app.include_router(health_router, prefix="/api/v1", tags=["health"])
    app.include_router(suggestions_router, prefix="/api/v1", tags=["suggestions"])
    return app


app = create_app()
