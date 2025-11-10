# src/quadral_cluster/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# если у тебя роутер лежит в другом модуле — поправь импорт
from .api.routes import router

app = FastAPI(
    title="Quadral Cluster API",
    version="0.3.0",
    docs_url="/docs",         # ВКЛЮЧИТЬ Swagger UI
    redoc_url=None,
    openapi_url="/openapi.json",
)

# Разрешим CORS на время разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем твои эндпоинты
# Если ты хочешь префикс — используй: app.include_router(router, prefix="/api")
app.include_router(router)

# Health-check на корне, чтобы / не давал 404
@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "docs": "/docs", "openapi": "/openapi.json"}
