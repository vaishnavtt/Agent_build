import os
import re
import uuid
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.engine.security import get_allowed_document_roots

router = APIRouter(prefix="/documents", tags=["Documents"])

_ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".json", ".csv"}
_MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


def _get_upload_dir() -> Path:
    """Returns and ensures the primary secure upload directory exists."""
    allowed = get_allowed_document_roots()
    upload_dir = allowed[0]
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


@router.post("/upload", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """Securely uploads and validates a document for Document Reader workflow nodes.

    Validates file extension, magic bytes, file size, and stores in an allowlisted root.
    """
    original_filename = file.filename or "uploaded_document"
    suffix = Path(original_filename).suffix.lower()

    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{suffix}'. Allowed formats: {sorted(_ALLOWED_EXTENSIONS)}",
        )

    # Read and validate content & size
    content = await file.read()
    if not content or len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if len(content) > _MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {_MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
        )

    # Validate PDF magic header
    if suffix == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file format: file header does not match PDF signature.",
        )

    # Sanitize filename to prevent directory traversal or script injection
    safe_basename = re.sub(r"[^A-Za-z0-9_.-]", "_", Path(original_filename).stem)[:40]
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    stored_name = f"{doc_id}_{safe_basename}{suffix}"

    upload_dir = _get_upload_dir()
    destination_path = upload_dir / stored_name

    destination_path.write_bytes(content)

    return {
        "document_id": doc_id,
        "filename": original_filename,
        "stored_filename": stored_name,
        "file_path": str(destination_path.resolve()),
        "file_size": len(content),
        "content_type": file.content_type or "application/octet-stream",
        "status": "ready",
    }


@router.get("/{document_id}", response_model=Dict[str, Any])
def get_document_info(document_id: str) -> Dict[str, Any]:
    """Retrieves metadata and existence check for an uploaded document."""
    upload_dir = _get_upload_dir()
    clean_id = re.sub(r"[^A-Za-z0-9_]", "", document_id)

    matching = list(upload_dir.glob(f"{clean_id}_*"))
    if not matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    file_path = matching[0]
    return {
        "document_id": document_id,
        "filename": file_path.name,
        "file_path": str(file_path.resolve()),
        "file_size": file_path.stat().st_size,
        "exists": True,
    }
