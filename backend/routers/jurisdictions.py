from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import clerk_user
from compliance_core.database import get_session
from compliance_core.jurisdictions import list_distinct_jurisdiction_hints

router = APIRouter(prefix="/api/jurisdictions", tags=["jurisdictions"])


@router.get("/hints")
async def get_jurisdiction_hints(
    session: AsyncSession = Depends(get_session),
    _user: dict = Depends(clerk_user),
):
    items = await list_distinct_jurisdiction_hints(session)
    return {"items": items}
