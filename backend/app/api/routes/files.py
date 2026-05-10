"""
File API routes
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
from fastapi.responses import FileResponse as FastAPIFileResponse
from ...db.session import get_db
from ...db.file_crud import file_crud, variant_group_crud
from ...db.project_crud import project_crud
from ...schemas.file import FileCreate, FileResponse, VariantGroupResponse, VariantSelect
from ...config import settings

router = APIRouter()


@router.get("", response_model=List[FileResponse])
def list_files(
    project_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """List all files, optionally filtered by project"""
    files = file_crud.get_all(db, project_id=project_id)
    return files


@router.get("/{file_id}", response_model=FileResponse)
def get_file(
    file_id: UUID,
    db: Session = Depends(get_db)
):
    """Get file by ID"""
    file = file_crud.get(db, file_id=file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )
    return file


@router.get("/{file_id}/url")
def get_file_url(
    file_id: UUID,
    db: Session = Depends(get_db)
):
    """Get file access URL or serve the file"""
    file = file_crud.get(db, file_id=file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )

    # Construct full path
    file_path = settings.storage_path / file.file_path

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found on disk: {file.file_path}"
        )

    # Return URL for frontend to access
    # For local development, return a data URL or direct path
    return {
        "id": str(file.id),
        "file_path": file.file_path,
        "url": f"/api/v1/files/{file_id}/download",
        "file_type": file.file_type,
    }


@router.get("/{file_id}/download")
def download_file(
    file_id: UUID,
    db: Session = Depends(get_db)
):
    """Download file"""
    file = file_crud.get(db, file_id=file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )

    file_path = settings.storage_path / file.file_path

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found on disk: {file.file_path}"
        )

    # Determine MIME type from file extension
    ext = file_path.suffix.lower()
    mime_map = {
        '.mp4': 'video/mp4', '.webm': 'video/webm',
        '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg',
        '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp',
        '.json': 'application/json', '.txt': 'text/plain',
    }
    media_type = mime_map.get(ext, 'application/octet-stream')

    return FastAPIFileResponse(file_path, media_type=media_type)


@router.post("", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
def create_file(
    file_in: FileCreate,
    db: Session = Depends(get_db)
):
    """Create a new file record"""
    # Verify project exists
    project = project_crud.get(db, project_id=file_in.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {file_in.project_id} not found"
        )

    file = file_crud.create(db, obj_in=file_in)
    return file


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete file"""
    success = file_crud.delete(db, file_id=file_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )
