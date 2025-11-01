from __future__ import annotations

from fastapi import FastAPI

from .api.routes import router
from .config import get_settings

settings = get_settings()

app = FastAPI(title="Quadral Cluster Core API", debug=settings.debug)
app.include_router(router)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
