from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: capstone/ (two levels above compliance_core/config.py).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    # Always load the same files regardless of cwd (MCP stdio uses cwd=backend/).
    model_config = SettingsConfigDict(
        env_file=(
            _REPO_ROOT / ".env",
            _BACKEND_ROOT / ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project Settings → Database (or local Postgres in dev). This is the only supported
    # database URL variable — `DATABASE_URL` and other names are not read. Alembic uses
    # the same value, rewritten to a sync driver in `alembic/env.py`. Direct 5432 or
    # pooler 6543: asyncpg connect args adapt for the pooler.
    database_url: str = Field(
        ...,
        min_length=1,
        validation_alias="SUPABASE_DATABASE_URL",
    )

    # Chat + embeddings go through OpenRouter (OpenAI-compatible API).
    openrouter_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENROUTER_API_KEY", "openrouter_api_key"),
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        validation_alias=AliasChoices("OPENROUTER_BASE_URL", "openrouter_base_url"),
    )
    openrouter_http_referer: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENROUTER_HTTP_REFERER", "openrouter_http_referer"),
        description="Optional OpenRouter HTTP-Referer header (rankings).",
    )
    openrouter_x_title: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENROUTER_X_TITLE", "openrouter_x_title"),
        description="Optional X-Title header for OpenRouter.",
    )

    # OpenAI platform / Agents SDK traces; also used as LLM key fallback in llm.py.
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key"),
        description="OpenAI API key for trace export; fallback LLM when OpenRouter is unset.",
    )

    llm_model: str = Field(
        default="openai/gpt-4.1-mini",
        validation_alias=AliasChoices(
            "llm_model",
            "LLM_MODEL",
            "agent_model",
            "AGENT_MODEL",
        ),
    )
    embedding_model: str = Field(
        default="openai/text-embedding-3-small",
        validation_alias=AliasChoices("EMBEDDING_MODEL", "embedding_model"),
    )

    langfuse_secret_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGFUSE_SECRET_KEY", "langfuse_secret_key"),
    )
    langfuse_public_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGFUSE_PUBLIC_KEY", "langfuse_public_key"),
    )
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        validation_alias=AliasChoices("LANGFUSE_HOST", "LANGFUSE_BASE_URL"),
    )

    openai_agents_disable_tracing: bool = False

    # Comma-separated browser origins (FastAPI CORS)
    cors_origins: str = "http://localhost:3000"

    clerk_issuer: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CLERK_ISSUER", "clerk_issuer"),
    )
    clerk_jwks_url: str = Field(
        ...,
        min_length=8,
        validation_alias=AliasChoices("CLERK_JWKS_URL", "clerk_jwks_url"),
        description="Clerk JWKS URL for API JWT verification.",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def sync_sdk_environ_from_settings() -> None:
    import os

    s = get_settings()
    if s.openai_api_key:
        os.environ["OPENAI_API_KEY"] = s.openai_api_key
    if s.openrouter_api_key:
        os.environ["OPENROUTER_API_KEY"] = s.openrouter_api_key
    if s.langfuse_public_key:
        os.environ["LANGFUSE_PUBLIC_KEY"] = s.langfuse_public_key
    if s.langfuse_secret_key:
        os.environ["LANGFUSE_SECRET_KEY"] = s.langfuse_secret_key
    if s.langfuse_host and s.langfuse_host != "https://cloud.langfuse.com":
        os.environ["LANGFUSE_BASE_URL"] = s.langfuse_host
        os.environ["LANGFUSE_HOST"] = s.langfuse_host
