"""Compliance AI API — FastAPI entrypoint."""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

_CAPSTONE_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = Path(__file__).resolve().parent
for _p in (_CAPSTONE_ROOT, _BACKEND_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import framework_documents, incidents, jurisdictions
from compliance_core.config import sync_sdk_environ_from_settings
from compliance_core.database import init_db

sync_sdk_environ_from_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Cyber Compliance AI Engine",
    description="Multi-agent governance API.",
    lifespan=lifespan,
)

_origins = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents.router)
app.include_router(framework_documents.router)
app.include_router(jurisdictions.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
