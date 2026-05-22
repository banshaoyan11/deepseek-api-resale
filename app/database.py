# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

_db_url = settings.DATABASE_URL
_db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
_db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)

_is_sqlite = "sqlite" in _db_url

_connect_args = {}
if not _is_sqlite:
    _connect_args["server_settings"] = {"application_name": "deepseek-resale"}

engine = create_async_engine(
    _db_url,
    echo=True,
    pool_pre_ping=not _is_sqlite,
    pool_recycle=300 if not _is_sqlite else -1,
    connect_args=_connect_args if not _is_sqlite else {},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
