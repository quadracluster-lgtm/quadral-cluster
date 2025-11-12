from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .api.routes_matching import router as matching_router
from .database import Base, engine

app = FastAPI(
    title="Quadral Cluster Core API",
    version="0.3.0",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(matching_router)


@app.on_event("startup")
def on_startup() -> None:
    from .models import domain  # noqa: F401 - ensure models are imported
    from .models import availability, cluster, preference  # noqa: F401

    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {"status": "ok", "docs": "/docs", "openapi": "/openapi.json"}
