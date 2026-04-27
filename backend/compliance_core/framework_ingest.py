from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from compliance_core.chunking import chunk_text
from compliance_core.embeddings import embed_texts
from compliance_core.models import FrameworkDocumentOriginal, Regulation

EMBED_BATCH = 64

# Matches upload guidance in the UI
MAX_STORED_ORIGINAL_BYTES = 12 * 1024 * 1024


async def _embed_many(texts: list[str]) -> list[list[float]]:
    out: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i : i + EMBED_BATCH]
        out.extend(await embed_texts(batch))
    return out


async def insert_framework_text(
    session: AsyncSession,
    *,
    owner_id: str,
    framework: str,
    source_document: str,
    version: str,
    jurisdiction: str | None,
    full_text: str,
    user_document_id: str | None = None,
    original: tuple[bytes, str, str] | None = None,
) -> dict[str, str | int | bool]:
    label = (framework or "Custom")[:128]
    title = (source_document or "Framework document")[:512]
    ver = (version or "1.0")[:64]
    doc_id = user_document_id or str(uuid.uuid4())
    text = (full_text or "").strip()
    if not text:
        return {"ok": False, "error": "empty text", "chunks": 0}

    await session.execute(
        delete(Regulation).where(
            Regulation.user_document_id == doc_id,
            Regulation.owner_id == owner_id,
        )
    )
    await session.execute(
        delete(FrameworkDocumentOriginal).where(
            FrameworkDocumentOriginal.user_document_id == doc_id,
            FrameworkDocumentOriginal.owner_id == owner_id,
        )
    )

    parts = chunk_text(text)
    vectors = await _embed_many(parts)

    for i, (chunk, vec) in enumerate(zip(parts, vectors, strict=True)):
        session.add(
            Regulation(
                framework=label,
                clause_number=f"{title}-{i + 1}",
                source_document=title,
                version=ver,
                jurisdiction=jurisdiction,
                user_document_id=doc_id,
                owner_id=owner_id,
                text=chunk,
                embedding=vec,
            )
        )
    if original is not None:
        raw, orig_name, content_type = original
        if len(raw) > MAX_STORED_ORIGINAL_BYTES:
            await session.rollback()
            return {"ok": False, "error": "file too large", "chunks": 0}
        session.add(
            FrameworkDocumentOriginal(
                user_document_id=doc_id,
                owner_id=owner_id,
                original_filename=(orig_name or "document")[:512],
                content_type=(content_type or "application/octet-stream")[:256],
                data=raw,
            )
        )
    await session.commit()
    return {
        "ok": True,
        "user_document_id": doc_id,
        "chunks": len(parts),
    }


async def list_owner_documents(
    session: AsyncSession, owner_id: str
) -> list[dict[str, str | int | None]]:
    stmt = (
        select(
            Regulation.user_document_id,
            func.max(Regulation.framework).label("framework"),
            func.max(Regulation.source_document).label("source_document"),
            func.max(Regulation.version).label("version"),
            func.max(Regulation.jurisdiction).label("jurisdiction"),
            func.count().label("chunk_count"),
        )
        .where(
            Regulation.owner_id == owner_id,
            Regulation.user_document_id.is_not(None),
        )
        .group_by(Regulation.user_document_id)
        .order_by(Regulation.user_document_id.desc())
    )
    rows = (await session.execute(stmt)).all()
    if not rows:
        return []
    doc_ids = [r[0] for r in rows if r[0]]
    o_stmt = select(
        FrameworkDocumentOriginal.user_document_id,
        FrameworkDocumentOriginal.original_filename,
    ).where(FrameworkDocumentOriginal.user_document_id.in_(doc_ids))
    originals: dict[str, str] = {
        o[0]: o[1] for o in (await session.execute(o_stmt)).all()
    }
    return [
        {
            "user_document_id": r[0],
            "framework": r[1],
            "source_document": r[2],
            "version": r[3],
            "jurisdiction": r[4],
            "chunk_count": int(r[5] or 0),
            "has_original": r[0] in originals,
            "original_filename": originals.get(r[0]),
        }
        for r in rows
    ]


async def get_framework_document_original(
    session: AsyncSession, owner_id: str, user_document_id: str
) -> FrameworkDocumentOriginal | None:
    stmt = select(FrameworkDocumentOriginal).where(
        FrameworkDocumentOriginal.user_document_id == user_document_id,
        FrameworkDocumentOriginal.owner_id == owner_id,
    )
    return (await session.execute(stmt)).scalars().first()


async def delete_user_document(
    session: AsyncSession, owner_id: str, user_document_id: str
) -> int:
    res = await session.execute(
        delete(Regulation).where(
            Regulation.user_document_id == user_document_id,
            Regulation.owner_id == owner_id,
        )
    )
    await session.execute(
        delete(FrameworkDocumentOriginal).where(
            FrameworkDocumentOriginal.user_document_id == user_document_id,
            FrameworkDocumentOriginal.owner_id == owner_id,
        )
    )
    await session.commit()
    return res.rowcount or 0
