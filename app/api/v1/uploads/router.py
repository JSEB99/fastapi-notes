from fastapi import APIRouter, File, UploadFile, HTTPException, status
import os
import shutil
import uuid
from app.services.file_storage import save_uploaded_image

router = APIRouter(prefix="/upload", tags=["uploads"])

MEDIA_DIR = "app/media"


@router.post("/bytes")
async def upload_bytes(file: bytes = File(...)):
    """Subir bytes"""
    return {
        "filename": "archivo_subido",
        "size_bytes": len(file)
    }


@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    """Subir archivo directamente"""
    return {
        "filename": file.filename,
        "content_type": file.content_type
    }


@router.post("/save")
async def save_file(file: UploadFile = File(...)):
    """Subir y persistir archivo"""
    saved = save_uploaded_image(file)

    return {
        "filename": saved["filename"],
        "content_type": saved["content_type"],
        "url": saved["url"],
        # "size": saved["size"],
        # "chunk_size": saved["chunk_size"],
        # "chunk_calls": saved["chunk_calls"],
        # "chunk_size_sample": saved["chunk_size_sample"]
    }
