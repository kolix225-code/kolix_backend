# app/core/database.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Engine SQLAlchemy 2.0 Async
connect_args = {}
# Supabase PgBouncer (Transaction Pooler) & Cloud SSL compatibility
if "supabase" in settings.ASYNC_DATABASE_URI or "pooler" in settings.ASYNC_DATABASE_URI:
    connect_args["statement_cache_size"] = 0
    connect_args["prepared_statement_cache_size"] = 0

engine_kwargs = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
}

if connect_args:
    engine_kwargs["connect_args"] = connect_args

# Adapter la taille du pool si on passe par un pooler externe (ex: Supabase PgBouncer 6543)
if "pooler" in settings.ASYNC_DATABASE_URI:
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 5
else:
    engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW

engine = create_async_engine(settings.ASYNC_DATABASE_URI, **engine_kwargs)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Declarative Base
class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

