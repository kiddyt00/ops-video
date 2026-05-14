"""
OSS Service - Multi-cloud storage abstraction layer

Supports: Aliyun OSS, AWS S3 (and S3-compatible), Tencent COS
"""
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from app.models.storage_provider import StorageProvider, StorageProviderType

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a storage connection test"""
    success: bool
    message: str


class OSSService:
    """Multi-cloud storage service abstraction.

    Wraps different cloud storage SDKs behind a unified interface.
    Supports:
      - aliyun_oss  (oss2 SDK)
      - aws_s3      (boto3 SDK)
      - tencent_cos (cos-python-sdk)
    """

    def __init__(self, provider: StorageProvider):
        self.provider = provider
        self._client = None

    # ------------------------------------------------------------------
    # Lazy client loading
    # ------------------------------------------------------------------
    def _get_client(self):
        """Lazily initialise the storage SDK client."""
        if self._client is not None:
            return self._client

        provider_type = self.provider.provider_type

        if provider_type in (StorageProviderType.OSS.value, "oss"):
            self._client = self._init_aliyun_oss()
        elif provider_type in (
            StorageProviderType.S3.value,
            StorageProviderType.S3_COMPATIBLE.value,
        ):
            self._client = self._init_aws_s3()
        elif provider_type == StorageProviderType.COS.value:
            self._client = self._init_tencent_cos()
        else:
            raise ValueError(
                f"Unsupported storage provider type: {provider_type}"
            )

        return self._client

    # ------------------------------------------------------------------
    # Provider-specific initialisation
    # ------------------------------------------------------------------
    def _init_aliyun_oss(self):
        """Create oss2.Bucket client."""
        try:
            import oss2
        except ImportError:
            raise ImportError(
                "oss2 package is required for Aliyun OSS. "
                "Install with: pip install oss2"
            )

        auth = oss2.Auth(
            self.provider.access_key,
            self.provider.secret_key,
        )
        endpoint = self.provider.endpoint or "oss-cn-hangzhou.aliyuncs.com"
        return oss2.Bucket(auth, endpoint, self.provider.bucket)

    def _init_aws_s3(self):
        """Create boto3 S3 client."""
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise ImportError(
                "boto3 package is required for AWS S3. "
                "Install with: pip install boto3"
            )

        kwargs: dict = {
            "aws_access_key_id": self.provider.access_key,
            "aws_secret_access_key": self.provider.secret_key,
        }

        if self.provider.endpoint:
            kwargs["endpoint_url"] = self.provider.endpoint
        if self.provider.region:
            kwargs["region_name"] = self.provider.region

        config = Config(
            s3={"addressing_style": "path"},
            signature_version="s3v4",
        )
        return boto3.client("s3", config=config, **kwargs)

    def _init_tencent_cos(self):
        """Create COS client."""
        try:
            from qcloud_cos import CosConfig, CosS3Client
        except ImportError:
            raise ImportError(
                "cos-python-sdk-v5 is required for Tencent COS. "
                "Install with: pip install cos-python-sdk-v5"
            )

        config = CosConfig(
            Region=self.provider.region or "ap-shanghai",
            SecretId=self.provider.access_key,
            SecretKey=self.provider.secret_key,
            Scheme="https",
        )
        return CosS3Client(config)

    # ------------------------------------------------------------------
    # Public URL helper
    # ------------------------------------------------------------------
    def _get_cdn_url(self, key: str) -> str:
        """Return public URL, using CDN base if configured."""
        extra = self.provider.extra_config or {}
        cdn_url: Optional[str] = extra.get("cdn_url")

        if cdn_url:
            base = cdn_url.rstrip("/")
            return f"{base}/{key}"

        # Fallback: construct from endpoint + bucket
        if self.provider.endpoint:
            endpoint = self.provider.endpoint.lstrip("https://").lstrip("http://")
            return f"https://{self.provider.bucket}.{endpoint}/{key}"

        return key

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------
    def upload(self, local_path: str, prefix: str = "") -> str:
        """Upload a local file to cloud storage.

        Args:
            local_path: Absolute or relative path to the local file.
            prefix: Optional key prefix (e.g. \"videos/\", \"images/\").

        Returns:
            Public URL of the uploaded object.
        """
        local_path = str(local_path)
        if not os.path.isfile(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")

        filename = os.path.basename(local_path)
        key = f"{prefix.rstrip('/')}/{filename}".lstrip("/") if prefix else filename

        provider_type = self.provider.provider_type

        if provider_type in (StorageProviderType.OSS.value, "oss"):
            bucket = self._get_client()
            bucket.put_object_from_file(key, local_path)

        elif provider_type in (
            StorageProviderType.S3.value,
            StorageProviderType.S3_COMPATIBLE.value,
        ):
            client = self._get_client()
            client.upload_file(local_path, self.provider.bucket, key)

        elif provider_type == StorageProviderType.COS.value:
            cos_client = self._get_client()
            with open(local_path, "rb") as f:
                cos_client.put_object(
                    Bucket=self.provider.bucket,
                    Body=f,
                    Key=key,
                )
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

        logger.info("Uploaded %s -> %s", local_path, key)
        return self._get_cdn_url(key)

    def download_url_to_local(self, url: str, local_path: str) -> str:
        """Download a file from a public URL to a local path.

        Uses httpx for streaming download.

        Args:
            url: Public HTTP/HTTPS URL of the remote file.
            local_path: Destination local path.

        Returns:
            The local_path on success.
        """
        local_path = str(local_path)
        parent = Path(local_path).parent
        parent.mkdir(parents=True, exist_ok=True)

        with httpx.stream("GET", url, follow_redirects=True, timeout=120.0) as resp:
            resp.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=8192):
                    f.write(chunk)

        logger.info("Downloaded %s -> %s", url, local_path)
        return local_path

    def generate_signed_url(
        self, key: str, expires_hours: int = 1
    ) -> str:
        """Generate a temporary signed/presigned URL for private access.

        Args:
            key: Object key in the bucket.
            expires_hours: Expiry time in hours (default 1).

        Returns:
            Signed URL string.
        """
        expires_seconds = int(expires_hours * 3600)
        provider_type = self.provider.provider_type

        if provider_type in (StorageProviderType.OSS.value, "oss"):
            bucket = self._get_client()
            return bucket.sign_url("GET", key, expires_seconds)

        elif provider_type in (
            StorageProviderType.S3.value,
            StorageProviderType.S3_COMPATIBLE.value,
        ):
            client = self._get_client()
            return client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.provider.bucket, "Key": key},
                ExpiresIn=expires_seconds,
            )

        elif provider_type == StorageProviderType.COS.value:
            cos_client = self._get_client()
            url = cos_client.get_presigned_download_url(
                Bucket=self.provider.bucket,
                Key=key,
                Expired=expires_seconds,
            )
            return url

        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

    def delete(self, key: str) -> bool:
        """Delete an object from cloud storage.

        Args:
            key: Object key in the bucket.

        Returns:
            True on success.
        """
        provider_type = self.provider.provider_type

        if provider_type in (StorageProviderType.OSS.value, "oss"):
            bucket = self._get_client()
            bucket.delete_object(key)

        elif provider_type in (
            StorageProviderType.S3.value,
            StorageProviderType.S3_COMPATIBLE.value,
        ):
            client = self._get_client()
            client.delete_object(Bucket=self.provider.bucket, Key=key)

        elif provider_type == StorageProviderType.COS.value:
            cos_client = self._get_client()
            cos_client.delete_object(
                Bucket=self.provider.bucket,
                Key=key,
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

        logger.info("Deleted %s from %s", key, self.provider.bucket)
        return True


# ------------------------------------------------------------------
# Connection test
# ------------------------------------------------------------------
async def test_storage_connection(provider: StorageProvider) -> TestResult:
    """Test connectivity to a storage provider.

    For HTTP-accessible endpoints, performs a HEAD request to verify
    the endpoint is reachable. For actual credential-based tests,
    attempts a bucket listing.

    Args:
        provider: StorageProvider model instance with credentials.

    Returns:
        TestResult(success, message)
    """
    import time

    start = time.time()

    try:
        # --- Quick endpoint reachability check ---
        if provider.endpoint:
            url = provider.endpoint
            if not url.startswith("http"):
                url = f"https://{url}"
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.head(url)
                if resp.status_code > 404:
                    logger.warning(
                        "Storage endpoint returned %d for %s",
                        resp.status_code,
                        url,
                    )

        # --- Credential-based test via actual SDK call ---
        service = OSSService(provider)

        pt = provider.provider_type
        if pt in (StorageProviderType.OSS.value, "oss"):
            bucket = service._get_client()
            # List first 1 object to verify credentials
            result = bucket.list_objects(prefix="", max_keys=1)
            bucket_name = result.bucket if hasattr(result, "bucket") else provider.bucket
            msg = f"Aliyun OSS connected: bucket={bucket_name}"

        elif pt in (
            StorageProviderType.S3.value,
            StorageProviderType.S3_COMPATIBLE.value,
        ):
            client = service._get_client()
            client.head_bucket(Bucket=provider.bucket)
            region = provider.region or "default"
            msg = f"AWS S3 connected: bucket={provider.bucket}, region={region}"

        elif pt == StorageProviderType.COS.value:
            cos_client = service._get_client()
            cos_client.head_bucket(Bucket=provider.bucket)
            region = provider.region or "default"
            msg = f"Tencent COS connected: bucket={provider.bucket}, region={region}"

        else:
            return TestResult(
                success=False,
                message=f"Unsupported provider type: {pt}",
            )

        latency = (time.time() - start) * 1000
        return TestResult(success=True, message=f"{msg} ({latency:.0f}ms)")

    except ImportError as e:
        return TestResult(success=False, message=f"Missing SDK: {str(e)}")
    except Exception as e:
        latency = (time.time() - start) * 1000
        logger.warning("Storage connection test failed: %s", str(e))
        return TestResult(
            success=False,
            message=f"Connection failed: {str(e)} ({latency:.0f}ms)",
        )
