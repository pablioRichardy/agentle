"""S3 file storage manager implementation."""

import logging
from typing import Any

try:
    import boto3
    from botocore.exceptions import ClientError

    has_boto3 = True
except ImportError:
    boto3 = None  # type: ignore
    ClientError = Exception  # type: ignore
    has_boto3 = False

from agentle.storage.file_storage_manager import FileStorageManager, FileStorageError

logger = logging.getLogger(__name__)


class S3FileStorageManager(FileStorageManager):
    """S3 implementation of file storage manager."""

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        endpoint_url: str | None = None,
    ):
        """
        Initialize S3 file storage manager.

        Args:
            bucket_name: S3 bucket name
            region: AWS region
            aws_access_key_id: AWS access key (optional, uses default credentials if not provided)
            aws_secret_access_key: AWS secret key (optional, uses default credentials if not provided)
            endpoint_url: Custom S3 endpoint URL (for S3-compatible services like MinIO)
        """
        if not has_boto3 or boto3 is None:
            raise ImportError(
                "boto3 is required for S3FileStorageManager. "
                + "Install it with: pip install boto3"
            )

        self.bucket_name = bucket_name
        self.region = region

        # Configure S3 client
        client_kwargs: dict[str, Any] = {"region_name": region}

        if aws_access_key_id and aws_secret_access_key:
            client_kwargs.update(
                {
                    "aws_access_key_id": aws_access_key_id,
                    "aws_secret_access_key": aws_secret_access_key,
                }
            )

        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        self.s3_client = boto3.client("s3", **client_kwargs)

        logger.info(f"S3FileStorageManager initialized for bucket: {bucket_name}")

    async def upload_file(self, file_data: bytes, filename: str, mime_type: str) -> str:
        """Upload file to S3 and return public URL."""
        try:
            logger.debug(f"Uploading file to S3: {filename} ({len(file_data)} bytes)")

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=file_data,
                ContentType=mime_type,
                ACL="public-read",  # Make file publicly accessible
            )

            # Generate public URL
            if self.s3_client.meta.region_name == "us-east-1":
                url = f"https://{self.bucket_name}.s3.amazonaws.com/{filename}"
            else:
                url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"

            logger.info(f"File uploaded successfully: {url}")
            return url

        except ClientError as e:
            error_msg = f"Failed to upload file to S3: {e}"
            logger.error(error_msg)
            raise FileStorageError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error uploading to S3: {e}"
            logger.error(error_msg)
            raise FileStorageError(error_msg) from e

    async def delete_file(self, file_url: str) -> bool:
        """Delete file from S3 by URL."""
        try:
            # Extract key from URL
            if f"s3.{self.region}.amazonaws.com" in file_url:
                key = file_url.split(f"s3.{self.region}.amazonaws.com/")[-1]
            elif "s3.amazonaws.com" in file_url:
                key = file_url.split("s3.amazonaws.com/")[-1]
            else:
                logger.warning(f"Could not extract S3 key from URL: {file_url}")
                return False

            logger.debug(f"Deleting file from S3: {key}")

            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)

            logger.info(f"File deleted successfully: {key}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting from S3: {e}")
            return False
