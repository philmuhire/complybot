import logging
import mimetypes
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import clerk_user
from compliance_core.document_text import text_from_bytes
from compliance_core.framework_ingest import (
    delete_user_document,
    get_framework_document_original,
    insert_framework_text,
    list_owner_documents,
)
from compliance_core.database import get_session
from compliance_core.jurisdictions import merge_jurisdiction_labels
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
    jur = merge_jurisdiction_labels(
        jurisdiction=body.jurisdiction, jurisdictions=body.jurisdictions
    )
    return await insert_framework_text(
        session,
        owner_id=owner,
        framework=body.framework,
        source_document=body.title,
        version=body.version,
        jurisdiction=jur,
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
    jurisdictions: list[str] = Form(default_factory=list),
    paste: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
):
    owner = _owner_id(user)
    jur = merge_jurisdiction_labels(
        jurisdiction=jurisdiction.strip() if jurisdiction else None,
        jurisdictions=jurisdictions or None,
    )

    text_content: str | None = None
    file_bytes: bytes | None = None
    file_name: str | None = None
    if file and file.filename:
        try:
            data = await file.read()
            file_bytes = data
            file_name = file.filename
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

    original: tuple[bytes, str, str] | None = None
    if file_bytes is not None and file_name is not None:
        guessed, _ = mimetypes.guess_type(file_name)
        ct = file.content_type and file.content_type.split(";")[0].strip() or None
        content_type = (ct or guessed or "application/octet-stream")
        original = (file_bytes, file_name, content_type)

    result = await insert_framework_text(
        session,
        owner_id=owner,
        framework=framework.strip(),
        source_document=title.strip(),
        version=version.strip() or "1.0",
        jurisdiction=jur,
        full_text=text_content,
        original=original,
    )
    if not result.get("ok") and result.get("error") == "file too large":
        raise HTTPException(413, "Original file is too large (max ~12 MB)")
    return result


@router.get("/{user_document_id}/original")
async def download_framework_document_original(
    user_document_id: str,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(clerk_user),
):
    owner = _owner_id(user)
    row = await get_framework_document_original(session, owner, user_document_id)
    if row is None:
        raise HTTPException(404, "No stored original file for this document")
    safe = quote(row.original_filename, safe="")
    return Response(
        content=row.data,
        media_type=row.content_type,
        headers={
            "Content-Disposition": f'inline; filename="{row.original_filename}"; filename*=UTF-8\'\'{safe}'
        },
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
