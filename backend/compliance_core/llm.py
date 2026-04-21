"""OpenRouter-backed chat model + separate OpenAI key for platform traces."""

from __future__ import annotations

from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from compliance_core.config import Settings, get_settings


def resolve_llm_api_key(settings: Settings | None = None) -> str:
    """Prefer OpenRouter; fall back to OpenAI key for local/dev without OpenRouter."""
    s = settings or get_settings()
    api_key = s.openrouter_api_key or s.openai_api_key
    if not api_key:
        raise ValueError(
            "No API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY for model calls."
        )
    return api_key


def get_async_openai_client_for_llm(settings: Settings | None = None) -> AsyncOpenAI:
    """Async OpenAI-compatible client pointing at OpenRouter (or compatible gateway)."""
    s = settings or get_settings()
    api_key = resolve_llm_api_key(s)
    headers: dict[str, str] = {}
    if s.openrouter_http_referer:
        headers["HTTP-Referer"] = s.openrouter_http_referer
    if s.openrouter_x_title:
        headers["X-Title"] = s.openrouter_x_title
    return AsyncOpenAI(
        base_url=s.openrouter_base_url,
        api_key=api_key,
        default_headers=headers or None,
    )


def get_agent_chat_model(settings: Settings | None = None) -> OpenAIChatCompletionsModel:
    s = settings or get_settings()
    client = get_async_openai_client_for_llm(s)
    return OpenAIChatCompletionsModel(model=s.llm_model, openai_client=client)
