"""
Artifact Uploader — unified OSS upload hook for pipeline artifacts.

Called after each workflow stage completes. Uploads generated files to OSS
and updates File records with the OSS URL.
"""
import logging
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from ..config import settings
from ..core.oss_service import OSSService
from ..db.session import SessionLocal
from ..db.storage_provider_crud import storage_provider_crud
from ..db.file_crud import file_crud

logger = logging.getLogger(__name__)

# OSS directory structure:
# ops-video/projects/{project_id}/{stage}/{filename}
_STAGE_PREFIX = {
    "script": "scripts",
    "storyboard": "storyboards",
    "image": "images",
    "tts": "audio/tts",
    "bgm": "audio/bgm",
    "sfx": "audio/sfx",
    "video_composer": "video",
    "inspiration": "inspiration",
    "story": "story",
    "chapter_outline": "chapters",
}


async def upload_artifact(
    project_id: UUID,
    task_id: UUID,
    stage: str,
    file_path: str,
    file_id: Optional[UUID] = None,
) -> Optional[str]:
    """Upload a single pipeline artifact to OSS and update its File record.

    Args:
        project_id: Project UUID — used as top-level directory.
        task_id: Task UUID — used as sub-directory.
        stage: Generation stage (script, storyboard, image, tts, bgm, sfx, video_composer).
        file_path: Local path to the file.
        file_id: Optional File record ID to update with oss_url.

    Returns:
        OSS URL string, or None if upload was skipped/failed.
    """
    # Resolve relative to storage path; absolute paths used as-is
    local_path = Path(file_path)
    if not local_path.is_absolute():
        local_path = settings.storage_path / local_path
    if not local_path.exists():
        logger.warning("Artifact not found, skipping OSS upload: %s", local_path)
        return None

    try:
        db = SessionLocal()
        try:
            provider = storage_provider_crud.get_active(db)
            if not provider:
                logger.debug("No active storage provider, skipping OSS upload")
                return None

            prefix = _STAGE_PREFIX.get(stage, "other")
            # Build OSS key: projects/{pid}/{prefix}/{task_id}/{filename}
            # Use the original filename (not a generated UUID) for dedup
            filename = local_path.name
            oss_key = f"projects/{project_id}/{prefix}/{task_id}/{filename}"

            oss = OSSService(provider)
            oss_url = oss.upload(str(local_path), prefix=oss_key)

            logger.info(
                "Artifact uploaded: %s -> %s (stage=%s, task=%s)",
                file_path, oss_url, stage, task_id,
            )

            # Update File record if file_id provided
            if file_id:
                file_crud.update_oss_url(db, file_id, oss_url)

            return oss_url
        finally:
            db.close()
    except Exception as e:
        logger.warning("OSS upload failed for %s (stage=%s): %s", file_path, stage, e)
        return None


async def upload_artifacts_batch(
    project_id: UUID,
    task_id: UUID,
    stage: str,
    file_paths: List[str],
    file_ids: Optional[List[UUID]] = None,
) -> List[Optional[str]]:
    """Upload multiple artifacts from the same stage.

    Args:
        project_id: Project UUID.
        task_id: Task UUID.
        stage: Generation stage key.
        file_paths: List of local file paths.
        file_ids: Optional parallel list of File record IDs.

    Returns:
        List of OSS URLs (None for failed uploads).
    """
    results = []
    for i, fp in enumerate(file_paths):
        fid = file_ids[i] if file_ids and i < len(file_ids) else None
        url = await upload_artifact(project_id, task_id, stage, fp, fid)
        results.append(url)
    return results
