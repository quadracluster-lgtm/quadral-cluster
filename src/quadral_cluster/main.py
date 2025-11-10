from __future__ import annotations

from fastapi import FastAPI

from quadral_cluster.api.routes import router
from quadral_cluster.config import get_settings
from quadral_cluster.database import Base, engine

settings = get_settings()

app = FastAPI(title="Quadral Cluster Core API", debug=settings.debug)
app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
