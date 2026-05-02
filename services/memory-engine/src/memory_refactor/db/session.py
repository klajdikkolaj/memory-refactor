from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from memory_refactor.core.settings import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def create_engine(database_url: str | None = None) -> AsyncEngine:
    return create_async_engine(
        database_url or get_settings().database_url,
        echo=False,
        pool_pre_ping=True,
    )


def get_engine() -> AsyncEngine:
    global _engine

    if _engine is None:
        _engine = create_engine()

    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker

    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
        )

    return _sessionmaker


async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with get_sessionmaker()() as session:
        yield session


async def dispose_engine() -> None:
    global _engine, _sessionmaker

    if _engine is not None:
        await _engine.dispose()

    _engine = None
    _sessionmaker = None
