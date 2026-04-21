"""
File API routes
"""
from uuid import UUID
from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_files():
    """List all files"""
    pass


@router.get("/{file_id}")
def get_file(file_id: UUID):
    """Get file by ID"""
    pass


@router.get("/{file_id}/url")
def get_file_url(file_id: UUID):
    """Get file access URL"""
    pass
