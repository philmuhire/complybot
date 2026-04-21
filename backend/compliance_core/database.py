from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from compliance_core.config import get_settings


class Base(DeclarativeBase):
    pass


def _engine():
    url = get_settings().database_url
    return create_async_engine(url, echo=False, pool_pre_ping=True)


engine = _engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


_PGVECTOR_HINT = (
    "pgvector is required for regulation embeddings. Options:\n"
    "  • Run Postgres with pgvector: from repo root, `docker compose up -d` and set "
    "DATABASE_URL=postgresql+asyncpg://compliance:compliance@localhost:5432/compliance\n"
    "  • Or install pgvector on your existing Postgres (macOS Homebrew Postgres: "
    "`brew install pgvector` then `CREATE EXTENSION vector` as a superuser)."
)


async def init_db() -> None:
    async with engine.begin() as conn:
        try:
            await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        except Exception as exc:
            msg = str(exc).lower()
            if "vector" in msg or "featurenotsupported" in msg.replace(" ", ""):
                raise RuntimeError(_PGVECTOR_HINT) from exc
            raise
        await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
