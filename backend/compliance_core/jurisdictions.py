"""Jurisdiction label normalization and RAG matching (supports comma‑separated values per row)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from compliance_core.models import Regulation

# Widened in migration 0003; merged CSV must fit
MAX_JURISDICTION_CSV = 256


def _iter_label_parts(
    jurisdiction: str | None = None,
    jurisdictions: list[str] | None = None,
) -> list[str]:
    """Split comma‑separated strings and expand the list; order preserved, no dedup."""
    out: list[str] = []
    for block in [jurisdiction, *(jurisdictions or [])]:
        if block is None:
            continue
        s = str(block).strip()
        if not s:
            continue
        for part in s.split(","):
            p = part.strip()
            if p:
                out.append(p)
    return out


def merge_jurisdiction_labels(
    jurisdiction: str | None = None,
    jurisdictions: list[str] | None = None,
) -> str | None:
    """
    Deduplicate case-insensitively, preserve first-seen order, join with comma.
    Comma‑separated values in `jurisdiction` and each `jurisdictions` item are split.
    """
    seen: set[str] = set()
    out: list[str] = []
    for p in _iter_label_parts(jurisdiction, jurisdictions):
        if len(p) > 128:
            p = p[:128]
        k = p.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    if not out:
        return None
    s = ",".join(out)
    return s[:MAX_JURISDICTION_CSV]


def split_jurisdiction_csv(value: str | None) -> set[str]:
    if not value:
        return set()
    return {p.strip().lower() for p in value.split(",") if p.strip()}


def wanted_jurisdiction_list(
    jurisdiction: str | None = None,
    jurisdictions: list[str] | None = None,
) -> list[str] | None:
    """Deduplicated tags to scope retrieval; ``None`` means do not filter by jurisdiction."""
    m = merge_jurisdiction_labels(jurisdiction=jurisdiction, jurisdictions=jurisdictions)
    if not m:
        return None
    return [p.strip() for p in m.split(",") if p.strip()]


def row_matches_jurisdictions(row_value: str | None, wanted: list[str] | None) -> bool:
    """A row with NULL jurisdiction is treated as global (always matches a filter)."""
    if not wanted:
        return True
    if row_value is None:
        return True
    row_tags = split_jurisdiction_csv(row_value)
    if not row_tags:
        return True
    want = {w.strip().lower() for w in wanted if w and w.strip()}
    if not want:
        return True
    return not row_tags.isdisjoint(want)


async def list_distinct_jurisdiction_hints(session: AsyncSession) -> list[str]:
    """All distinct sub-tags from simple and comma‑separated jurisdiction values in regulations."""
    stmt = select(Regulation.jurisdiction).where(Regulation.jurisdiction.is_not(None)).distinct()
    rows = (await session.execute(stmt)).scalars().all()
    out: set[str] = set()
    for raw in rows:
        if not raw:
            continue
        for part in str(raw).split(","):
            p = part.strip()
            if p:
                out.add(p)
    return sorted(out, key=str.casefold)
