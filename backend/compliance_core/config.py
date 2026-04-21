from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root (capstone/, two levels above this file: compliance_core/config.py).
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

    database_url: str = "postgresql+asyncpg://compliance:compliance@localhost:5432/compliance"

    # Chat + embeddings go through OpenRouter (OpenAI-compatible API).
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_http_referer: str | None = Field(
        default=None,
        description="Optional OpenRouter HTTP-Referer header (rankings); can use OPENROUTER_HTTP_REFERER env.",
    )
    openrouter_x_title: str | None = Field(
        default=None,
        description="Optional X-Title header for OpenRouter.",
    )

    # Used only for OpenAI platform traces (https://platform.openai.com/logs/trace), not chat.
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key for Agents SDK trace export to OpenAI — not used for model calls when OpenRouter is configured.",
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
    embedding_model: str = "openai/text-embedding-3-small"

    langfuse_secret_key: str | None = None
    langfuse_public_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    clerk_jwks_url: str = Field(
        ...,
        min_length=8,
        description="Clerk JWKS URL for JWT verification (Clerk Dashboard → configure → API keys).",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
