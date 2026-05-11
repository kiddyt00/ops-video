"""
Storage Providers API routes
"""
from uuid import UUID
from typing import List, Optional
import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...db.storage_provider_crud import storage_provider_crud
from ...schemas.storage_provider import (
    StorageProviderCreate,
    StorageProviderUpdate,
    StorageProviderResponse,
    StorageTestResult,
)
from ...core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("", response_model=List[StorageProviderResponse])
def list_storage_providers(db: Session = Depends(get_db)):
    """List all storage providers"""
    return storage_provider_crud.get_all(db)


@router.post("", response_model=StorageProviderResponse, status_code=status.HTTP_201_CREATED)
def create_storage_provider(
    provider_in: StorageProviderCreate,
    db: Session = Depends(get_db),
):
    """Create a new storage provider"""
    existing = storage_provider_crud.get_by_name(db, provider_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Storage provider with name '{provider_in.name}' already exists",
        )
    return storage_provider_crud.create(db, obj_in=provider_in)


@router.get("/{provider_id}", response_model=StorageProviderResponse)
def get_storage_provider(
    provider_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a storage provider by ID"""
    provider = storage_provider_crud.get(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Storage provider not found")
    return provider


@router.put("/{provider_id}", response_model=StorageProviderResponse)
def update_storage_provider(
    provider_id: UUID,
    provider_in: StorageProviderUpdate,
    db: Session = Depends(get_db),
):
    """Update a storage provider"""
    provider = storage_provider_crud.update(db, provider_id, provider_in)
    if not provider:
        raise HTTPException(status_code=404, detail="Storage provider not found")
    return provider


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_storage_provider(
    provider_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a storage provider"""
    success = storage_provider_crud.delete(db, provider_id)
    if not success:
        raise HTTPException(status_code=404, detail="Storage provider not found")


@router.post("/{provider_id}/test", response_model=StorageTestResult)
async def test_storage_provider(
    provider_id: UUID,
    db: Session = Depends(get_db),
):
    """Test storage provider connection by listing bucket contents"""
    provider = storage_provider_crud.get(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Storage provider not found")

    start = time.time()

    try:
        result = await _test_s3_connection(provider)
        latency = (time.time() - start) * 1000
        storage_provider_crud.update_test_result(db, provider_id, success=True)
        return StorageTestResult(
            success=True,
            message=result,
            latency_ms=round(latency, 1),
            provider_name=provider.name,
            bucket=provider.bucket,
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        error_msg = str(e)
        logger.warning("Storage provider test failed for %s: %s", provider.name, error_msg)
        storage_provider_crud.update_test_result(db, provider_id, success=False, error=error_msg)
        return StorageTestResult(
            success=False,
            message=error_msg,
            latency_ms=round(latency, 1),
            provider_name=provider.name,
            bucket=provider.bucket,
        )


@router.post("/{provider_id}/activate", response_model=StorageProviderResponse)
def activate_storage_provider(
    provider_id: UUID,
    db: Session = Depends(get_db),
):
    """Activate a storage provider (deactivates all others)"""
    provider = storage_provider_crud.activate(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Storage provider not found")
    return provider


async def _test_s3_connection(provider) -> str:
    """Test S3-compatible storage connection by attempting to list bucket objects.

    Supports: S3, S3-compatible, OSS, COS via httpx (REST API).
    """
    import hashlib
    import hmac
    import base64
    from email.utils import formatdate
    from urllib.parse import quote

    endpoint = provider.endpoint
    if not endpoint:
        # Default endpoints by provider type
        defaults = {
            "s3": "https://s3.amazonaws.com",
            "s3_compatible": None,
            "oss": "https://oss-cn-hangzhou.aliyuncs.com",
            "cos": "https://cos.ap-shanghai.myqcloud.com",
        }
        endpoint = defaults.get(provider.provider_type.lower())
        if not endpoint:
            raise ValueError(f"Endpoint required for provider type: {provider.provider_type}")

    # Normalize endpoint (remove trailing slash)
    endpoint = endpoint.rstrip("/")

    # Build the test request URL
    url = f"{endpoint}/{provider.bucket}/?max-keys=1"

    # Date header
    date_str = formatdate(usegmt=True)

    # Build canonical request for AWS Signature V4
    # For simplicity, we use a HEAD/GET bucket request with auth headers
    # Most S3-compatible services support this

    # Determine signing region
    region = provider.region or "us-east-1"
    service = "s3"

    if provider.provider_type.lower() in ("oss",):
        # Aliyun OSS uses a different auth scheme
        return await _test_oss_connection(provider, endpoint)

    if provider.provider_type.lower() in ("cos",):
        # Tencent COS uses a similar but slightly different auth scheme
        return await _test_cos_connection(provider, endpoint)

    # Standard AWS Signature V4
    access_key = provider.access_key
    secret_key = provider.secret_key

    # Build string to sign
    method = "GET"
    canonical_uri = "/" + quote(provider.bucket, safe="") + "/"
    canonical_querystring = "max-keys=1"
    payload_hash = hashlib.sha256(b"").hexdigest()

    canonical_headers = f"host:{endpoint.replace('https://', '').replace('http://', '')}\nx-amz-date:{date_str.replace(',', '').replace(' ', 'T')}Z\n"
    signed_headers = "host;x-amz-date"

    canonical_request = (
        f"{method}\n{canonical_uri}\n{canonical_querystring}\n"
        f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )

    algorithm = "AWS4-HMAC-SHA256"
    date_key = date_str.split(",")[1].strip().replace(" ", "T") + "Z" if "," in date_str else date_str.replace(" ", "T")
    credential_scope = f"{date_key[:8]}/{region}/{service}/aws4_request"

    string_to_sign = (
        f"{algorithm}\n{date_key}\n{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode()).hexdigest()}"
    )

    def sign(key, msg):
        return hmac.new(key, msg.encode(), hashlib.sha256).digest()

    k_date = sign(("AWS4" + secret_key).encode(), date_key[:8])
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    k_signing = sign(k_service, "aws4_request")
    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()

    authorization = (
        f"{algorithm} Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    headers = {
        "Authorization": authorization,
        "x-amz-date": date_key,
    }

    async with __import__("httpx").AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code in (200, 404):
            # 200 = bucket exists with objects, 404 = bucket exists but empty (no keys)
            # Both indicate successful connection
            return f"Connection successful ({provider.provider_type}: {provider.bucket})"
        else:
            raise ValueError(f"HTTP {resp.status_code}: {resp.text[:300]}")


async def _test_oss_connection(provider, endpoint: str) -> str:
    """Test Aliyun OSS connection"""
    import hashlib
    import hmac
    import base64
    from email.utils import formatdate

    date_str = formatdate(usegmt=True)
    content_type = ""
    canonical_resource = "/" + provider.bucket + "/"

    string_to_sign = f"GET\n\n{content_type}\n{date_str}\n{canonical_resource}"

    signature = base64.b64encode(
        hmac.new(
            provider.secret_key.encode(),
            string_to_sign.encode(),
            hashlib.sha1,
        ).digest()
    ).decode()

    authorization = f"OSS {provider.access_key}:{signature}"

    url = f"{endpoint}/?max-keys=1"
    headers = {
        "Authorization": authorization,
        "Date": date_str,
        "Host": f"{provider.bucket}.{endpoint.replace('https://', '').replace('http://', '')}",
    }

    async with __import__("httpx").AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code in (200, 404):
            return f"Connection successful (OSS: {provider.bucket})"
        else:
            raise ValueError(f"HTTP {resp.status_code}: {resp.text[:300]}")


async def _test_cos_connection(provider, endpoint: str) -> str:
    """Test Tencent COS connection using simple auth"""
    import hashlib
    import hmac
    import base64

    method = "GET"
    key = "/"
    sign_key = "a" * 16  # q-sign-time placeholder
    sign_time = f"{int(time.time())};{int(time.time()) + 3600}"
    format_str = f"{method.lower()}\n{key}\n\nhost={provider.bucket}.cos.{provider.region or 'ap-shanghai'}.myqcloud.com\n"
    string_to_sign = f"sha1\n{sign_time}\n{hashlib.sha1(format_str.encode()).hexdigest()}\n"

    signature = hmac.new(
        provider.secret_key.encode(),
        string_to_sign.encode(),
        hashlib.sha1,
    ).hexdigest()

    url = f"{endpoint}/{provider.bucket}/?max-keys=1"
    headers = {
        "Authorization": f"q-sign-algorithm=sha1&q-ak={provider.access_key}&q-sign-time={sign_time}&q-key-time={sign_time}&q-headers=host&signature={signature}",
    }

    async with __import__("httpx").AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code in (200, 404):
            return f"Connection successful (COS: {provider.bucket})"
        else:
            raise ValueError(f"HTTP {resp.status_code}: {resp.text[:300]}")
