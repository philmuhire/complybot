from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from compliance_core.embeddings import embed_query
from compliance_core.jurisdictions import row_matches_jurisdictions, wanted_jurisdiction_list
from compliance_core.models import Regulation


async def hybrid_search(
    session: AsyncSession,
    query: str,
    *,
    jurisdiction: str | None = None,
    jurisdictions: list[str] | None = None,
    framework: str | None = None,
    limit: int = 8,
) -> list[dict]:
    """Semantic + lightweight lexical ranking over regulation chunks.

    When one or more jurisdiction tags are given (single `jurisdiction` string and/or
    `jurisdictions` list, merged and comma-split), only rows that match *any* tag
    (including NULL/global rows) are kept, consistent with :func:`row_matches_jurisdictions`.
    """
    want = wanted_jurisdiction_list(jurisdiction, jurisdictions)
    pre_limit = min(240, (limit * 6)) if want else (limit * 3)

    q_vec = await embed_query(query)
    distance = Regulation.embedding.cosine_distance(q_vec)
    stmt = (
        select(Regulation, distance.label("distance"))
        .where(Regulation.embedding.is_not(None))
        .order_by(distance)
        .limit(pre_limit)
    )
    if framework:
        stmt = stmt.where(Regulation.framework == framework)

    rows = (await session.execute(stmt)).all()
    ranked: list[tuple[Regulation, float, int]] = []
    for row in rows:
        reg, dist = row[0], float(row[1])
        if want and not row_matches_jurisdictions(reg.jurisdiction, want):
            continue
        kw = [k for k in query.lower().split() if len(k) > 2]
        hit = sum(1 for k in kw if k in reg.text.lower())
        ranked.append((reg, dist, hit))

    ranked.sort(key=lambda r: r[1] - 0.05 * r[2])

    out: list[dict] = []
    for reg, dist, hit in ranked[:limit]:
        out.append(
            {
                "id": reg.id,
                "framework": reg.framework,
                "clause_number": reg.clause_number,
                "source_document": reg.source_document,
                "version": reg.version,
                "jurisdiction": reg.jurisdiction,
                "text": reg.text[:2000],
                "semantic_distance": dist,
                "keyword_hits": hit,
            }
        )
    return out
