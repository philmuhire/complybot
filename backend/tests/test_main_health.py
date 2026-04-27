"""Smoke tests for FastAPI entrypoint helpers (no database)."""

import asyncio

from main import health


def test_health_handler_returns_ok():
    result = asyncio.run(health())
    assert result == {"status": "ok"}
