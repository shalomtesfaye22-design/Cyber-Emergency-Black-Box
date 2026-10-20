"""Database engine and FastAPI dependency."""
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.config import settings
from backend.database.models import Base

_engine = None
_sessions = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(settings.database_url, future=True)
        @event.listens_for(_engine.sync_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA busy_timeout=5000")
            finally:
                cursor.close()
    return _engine


def get_session_factory():
    global _sessions
    if _sessions is None:
        _sessions = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    return _sessions


async def init_db() -> None:
    from backend.database.crud import seed_default_settings
    async with get_engine().begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with get_session_factory()() as session:
        await seed_default_settings(session)


async def get_db():
    async with get_session_factory()() as session:
        yield session

