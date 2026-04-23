from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from compliance_core.config import get_settings


class Base(DeclarativeBase):
    pass


def _asyncpg_connect_args_for_url(url: str) -> dict:
    u = url.lower()
    if ":6543" in u or "pooler" in u:
        return {"statement_cache_size": 0}
    return {}


def _engine():
    url = get_settings().database_url
    return create_async_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        connect_args=_asyncpg_connect_args_for_url(url),
    )


engine = _engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


def _is_extension_permission_denied(exc: Exception) -> bool:
    m = str(exc).lower()
    return "must be superuser" in m or "permission denied" in m or "insufficient privilege" in m


_PGVECTOR_HINT = (
    "pgvector is required. Enable the vector extension in Supabase (or run backend/supabase_setup.sql). "
    "Check SUPABASE_DATABASE_URL in .env."
)


async def init_db() -> None:
    async with engine.begin() as conn:
        for sql, ext_name in (
            ("CREATE EXTENSION IF NOT EXISTS vector", "vector"),
            ("CREATE EXTENSION IF NOT EXISTS pg_trgm", "pg_trgm"),
        ):
            try:
                await conn.exec_driver_sql(sql)
            except Exception as exc:
                if _is_extension_permission_denied(exc):
                    continue
                if ext_name == "vector":
                    msg = str(exc).lower()
                    if "vector" in msg or "featurenotsupported" in msg.replace(" ", ""):
                        raise RuntimeError(_PGVECTOR_HINT) from exc
                raise
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        for stmt in (
            "ALTER TABLE regulations "
            "ADD COLUMN IF NOT EXISTS user_document_id VARCHAR(36) NULL",
            "ALTER TABLE regulations ADD COLUMN IF NOT EXISTS owner_id VARCHAR(128) NULL",
            "CREATE INDEX IF NOT EXISTS ix_regulations_user_document_id "
            "ON regulations (user_document_id) "
            "WHERE user_document_id IS NOT NULL",
            "CREATE INDEX IF NOT EXISTS ix_regulations_owner_id "
            "ON regulations (owner_id) "
            "WHERE owner_id IS NOT NULL",
        ):
            try:
                await conn.exec_driver_sql(stmt)
            except Exception:
                pass
