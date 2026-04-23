import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import clerk_user
from compliance_core.document_text import text_from_bytes
from compliance_core.framework_ingest import (
    delete_user_document,
    insert_framework_text,
    list_owner_documents,
)
from compliance_core.database import get_session
from compliance_core.schemas_framework import FrameworkIngestBody

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/framework-documents", tags=["framework-documents"])


def _owner_id(user: dict) -> str:
    sub = user.get("sub")
    if not sub:
        raise HTTPException(401, "Missing user id in token")
    return str(sub)


@router.get("")
async def list_my_framework_documents(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(clerk_user),
):
    owner = _owner_id(user)
    items = await list_owner_documents(session, owner)
    return {"items": items}


@router.post("")
async def ingest_paste(
    body: FrameworkIngestBody,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(clerk_user),
):
    owner = _owner_id(user)
    return await insert_framework_text(
        session,
        owner_id=owner,
        framework=body.framework,
        source_document=body.title,
        version=body.version,
        jurisdiction=body.jurisdiction,
        full_text=body.text,
    )


@router.post("/upload")
async def upload_framework_file(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(clerk_user),
    title: str = Form(..., min_length=1),
    framework: str = Form(..., min_length=1),
    version: str = Form(default="1.0"),
    jurisdiction: str | None = Form(default=None),
    paste: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
):
    owner = _owner_id(user)

    text_content: str | None = None
    if file and file.filename:
        try:
            data = await file.read()
            text_content = text_from_bytes(file.filename, data)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
    if paste and paste.strip():
        if text_content is not None:
            text_content = f"{text_content}\n\n{paste.strip()}"
        else:
            text_content = paste.strip()

    if not text_content or not text_content.strip():
        raise HTTPException(400, "Provide a file and/or paste text with content")

    return await insert_framework_text(
        session,
        owner_id=owner,
        framework=framework.strip(),
        source_document=title.strip(),
        version=version.strip() or "1.0",
        jurisdiction=(jurisdiction.strip() if jurisdiction else None),
        full_text=text_content,
    )


@router.delete("/{user_document_id}")
async def remove_framework_document(
    user_document_id: str,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(clerk_user),
):
    owner = _owner_id(user)
    n = await delete_user_document(session, owner, user_document_id)
    if n == 0:
        raise HTTPException(404, "Document not found or not owned by you")
    return {"ok": True, "deleted": n}
