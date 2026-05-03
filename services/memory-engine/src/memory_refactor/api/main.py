from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from memory_refactor.api.routes import health, memories, raw_memory_events, refactor_runs
from memory_refactor.core.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Memory Refactor API",
        version="0.1.0",
        description="Typed memory refactor engine API.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(raw_memory_events.router)
    app.include_router(memories.router)
    app.include_router(refactor_runs.router)

    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run(
        "memory_refactor.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
