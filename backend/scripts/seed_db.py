"""Load regulation chunks and embeddings into PostgreSQL."""

import asyncio
import json
import sys
from pathlib import Path

_BACK_END = Path(__file__).resolve().parents[1]
if str(_BACK_END) not in sys.path:
    sys.path.insert(0, str(_BACK_END))

from sqlalchemy import select

from compliance_core.database import SessionLocal, engine, init_db
from compliance_core.embeddings import embed_texts
from compliance_core.models import Regulation


ROOT = _BACK_END


async def main() -> None:
    await init_db()
    data_path = ROOT / "compliance_core" / "seed_data" / "regulations.json"
    rows = json.loads(data_path.read_text(encoding="utf-8"))
    texts = [r["text"] for r in rows]
    embeddings = await embed_texts(texts)

    async with SessionLocal() as session:
        existing = (await session.execute(select(Regulation.id))).scalars().first()
        if existing:
            print("Regulations already seeded — skipping.")
            return

        for row, emb in zip(rows, embeddings, strict=True):
            session.add(
                Regulation(
                    framework=row["framework"],
                    clause_number=row["clause_number"],
                    source_document=row["source_document"],
                    version=row["version"],
                    jurisdiction=row.get("jurisdiction"),
                    text=row["text"],
                    embedding=emb,
                )
            )
        await session.commit()
        print(f"Seeded {len(rows)} regulation chunks.")


async def _entry() -> None:
    await main()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_entry())
