"""
Generator API routes
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_generators():
    """List available generators"""
    pass


@router.post("/{generator_type}/generate")
def generate(generator_type: str):
    """Execute generation"""
    pass
